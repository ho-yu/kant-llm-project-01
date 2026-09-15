"""원본 기록에서 집계 수치를 계산한다.

집계 결과는 저장된 값을 읽는 것이 아니라 매번 raw 에서 다시 계산한다.
따라서 data/derived/ 아래 파일은 언제든 지우고 재생성할 수 있다.

집계 규칙
  - 워밍업/재시도/추가 실험은 기본 집계에서 제외한다 (config.AGGREGATED_PHASES).
  - 지표마다 평균과 함께 n(계산에 사용한 응답 수)을 낸다. n 은 지표마다 다르다.
  - 유효 값이 한 건도 없으면 평균을 0 으로 쓰지 않고 available=False 로 표시한다.
  - 모든 집계값에 기여한 run_id 목록을 함께 담아 역추적이 가능하게 한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from . import config, recorder, schema, scoring


@dataclass
class MetricStat:
    """한 지표의 집계 결과."""

    available: bool
    mean: float | None = None
    n: int = 0
    min: float | None = None
    max: float | None = None
    values: list[float] = field(default_factory=list)
    source_run_ids: list[str] = field(default_factory=list)
    excluded_run_ids: list[str] = field(default_factory=list)
    unavailable_reason: str | None = None

    def render(self, digits: int = 2) -> str:
        """표에 넣을 문자열. 값이 없으면 0 이 아니라 '집계 불가'."""
        if not self.available:
            return "집계 불가"
        return f"{self.mean:.{digits}f} (n={self.n})"


def _collect(records: list[dict[str, Any]], metric: str) -> MetricStat:
    values: list[float] = []
    used: list[str] = []
    excluded: list[str] = []

    for rec in records:
        v = rec.get(metric)
        if v is None:
            excluded.append(rec["run_id"])
            continue
        values.append(float(v))
        used.append(rec["run_id"])

    if not values:
        return MetricStat(
            available=False,
            n=0,
            excluded_run_ids=excluded,
            unavailable_reason="유효한 측정값 없음",
        )

    return MetricStat(
        available=True,
        mean=sum(values) / len(values),
        n=len(values),
        min=min(values),
        max=max(values),
        values=values,
        source_run_ids=used,
        excluded_run_ids=excluded,
    )


def _in_scope(rec: dict[str, Any], phases: Iterable[str]) -> bool:
    return rec.get("phase") in tuple(phases)


def aggregate_local(phases: Iterable[str] = config.AGGREGATED_PHASES) -> dict[str, Any]:
    """모델별 집계. 기본은 본 실험(main)만."""
    all_records = list(recorder.iter_records(config.LOCAL_RUNS_PATH))
    scoped = [r for r in all_records if _in_scope(r, phases)]

    out: dict[str, Any] = {
        "scope_phases": list(phases),
        "total_records_in_file": len(all_records),
        "records_in_scope": len(scoped),
        "settings_version": None,
        "questions_version": None,
        "models": {},
    }

    versions = {r.get("settings_version") for r in scoped if r.get("settings_version")}
    if len(versions) > 1:
        out["settings_version_conflict"] = sorted(versions)
    elif versions:
        out["settings_version"] = versions.pop()

    qversions = {r.get("questions_version") for r in scoped if r.get("questions_version")}
    if qversions:
        out["questions_version"] = sorted(qversions)[0] if len(qversions) == 1 else None
        if len(qversions) > 1:
            out["questions_version_conflict"] = sorted(qversions)

    for model in config.enabled_models():
        label = model["model_label"]
        rows = [r for r in scoped if r.get("model_label") == label]
        ok_rows = [r for r in rows if r.get("status") == config.STATUS_SUCCESS]

        metrics = {m: asdict(_collect(ok_rows, m)) for m in schema.LOCAL_METRIC_FIELDS}

        out["models"][label] = {
            "display_name": model.get("display_name"),
            "model_tag": model.get("model_tag"),
            # 축 1: 호출 성공 여부
            "attempts": len(rows),
            "success": len(ok_rows),
            "errors": len(rows) - len(ok_rows),
            "error_run_ids": [r["run_id"] for r in rows if r.get("status") == config.STATUS_ERROR],
            # 축 2: 지표별 측정 여부 (지표마다 n 이 다르다)
            "metrics": metrics,
            "run_ids": [r["run_id"] for r in rows],
        }

    return out


def aggregate_quality(phases: Iterable[str] = config.AGGREGATED_PHASES) -> dict[str, Any]:
    """축 3: 품질 점수. 실행 기록과 run_id 로 조인한다."""
    runs = {
        r["run_id"]: r
        for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
        if r.get("run_id") and _in_scope(r, phases)
    }
    scores = [s for s in scoring.scored_only() if s.get("run_id") in runs]

    qmap = config.question_map()
    criteria = config.load_questions()["criteria"]

    out: dict[str, Any] = {"scope_phases": list(phases), "criteria": criteria, "models": {}}

    for model in config.enabled_models():
        label = model["model_label"]
        rows = [s for s in scores if runs[s["run_id"]].get("model_label") == label]

        per_criterion: dict[str, Any] = {}
        for code in criteria:
            vals: list[float] = []
            used: list[str] = []
            for s in rows:
                v = (s.get("scores") or {}).get(code)
                if v is None:
                    continue
                vals.append(float(v))
                used.append(s["run_id"])

            if vals:
                per_criterion[code] = asdict(
                    MetricStat(
                        available=True,
                        mean=sum(vals) / len(vals),
                        n=len(vals),
                        min=min(vals),
                        max=max(vals),
                        values=vals,
                        source_run_ids=used,
                    )
                )
            else:
                per_criterion[code] = asdict(
                    MetricStat(available=False, unavailable_reason="채점된 응답 없음")
                )

        # 사례 유형별
        by_case: dict[str, Any] = {}
        for case_type in {q["case_type"] for q in qmap.values()}:
            qids = {qid for qid, q in qmap.items() if q["case_type"] == case_type}
            vals = [
                v
                for s in rows
                if s.get("question_id") in qids
                for v in [s.get("average")]
                if v is not None
            ]
            by_case[case_type] = (
                asdict(MetricStat(available=True, mean=sum(vals) / len(vals), n=len(vals), values=vals))
                if vals
                else asdict(MetricStat(available=False, unavailable_reason="채점된 응답 없음"))
            )

        # Run 간 일관성
        by_repeat: dict[str, Any] = {}
        for rep in sorted({runs[s["run_id"]].get("repeat") for s in rows} - {None}):
            vals = [
                s["average"]
                for s in rows
                if runs[s["run_id"]].get("repeat") == rep and s.get("average") is not None
            ]
            by_repeat[f"r{rep}"] = (
                asdict(MetricStat(available=True, mean=sum(vals) / len(vals), n=len(vals), values=vals))
                if vals
                else asdict(MetricStat(available=False, unavailable_reason="채점된 응답 없음"))
            )

        out["models"][label] = {
            "display_name": model.get("display_name"),
            "scored_count": len(rows),
            "per_criterion": per_criterion,
            "by_case_type": by_case,
            "by_repeat": by_repeat,
        }

    return out


def aggregate_cloud(phases: Iterable[str] = config.AGGREGATED_PHASES) -> dict[str, Any]:
    all_records = list(recorder.iter_records(config.CLOUD_RUNS_PATH))
    scoped = [r for r in all_records if _in_scope(r, phases)]
    ok_rows = [r for r in scoped if r.get("status") == config.STATUS_SUCCESS]

    return {
        "scope_phases": list(phases),
        "cloud_question_ids": config.cloud_question_ids(),
        "attempts": len(scoped),
        "success": len(ok_rows),
        "errors": len(scoped) - len(ok_rows),
        "error_run_ids": [r["run_id"] for r in scoped if r.get("status") == config.STATUS_ERROR],
        "metrics": {m: asdict(_collect(ok_rows, m)) for m in schema.CLOUD_METRIC_FIELDS},
        "run_ids": [r["run_id"] for r in scoped],
        "_note": "로컬은 질문당 2회, Cloud 는 1회다. 반복 수가 다르므로 표에 함께 표시한다.",
    }


def trace(run_id: str) -> dict[str, Any] | None:
    """집계 수치에서 원본으로 역추적. run_id 하나의 실행 기록 + 채점 기록을 모은다."""
    for path, source in ((config.LOCAL_RUNS_PATH, "local"), (config.CLOUD_RUNS_PATH, "cloud")):
        for rec in recorder.iter_records(path):
            if rec.get("run_id") == run_id:
                score = next(
                    (s for s in scoring.parse() if s.get("run_id") == run_id),
                    None,
                )
                return {"source_file": source, "path": str(path), "run": rec, "score": score}
    return None


def write_summaries() -> list[str]:
    """집계 결과를 data/derived/ 에 저장한다. 이 파일들은 재생성 가능한 생성물이다."""
    import json

    config.DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    payload = {"local": aggregate_local(), "quality": aggregate_quality()}
    config.LOCAL_SUMMARY_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append(str(config.LOCAL_SUMMARY_PATH))

    config.CLOUD_SUMMARY_PATH.write_text(
        json.dumps(aggregate_cloud(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append(str(config.CLOUD_SUMMARY_PATH))

    return written


if __name__ == "__main__":
    from . import use_utf8_stdout

    use_utf8_stdout()
    for p in write_summaries():
        print("written:", p)

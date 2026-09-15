"""저장된 파일을 다시 열어 검사한다.

검사 항목
  1. 줄마다 json.loads 로 파싱되는가
  2. 스키마 필수 키가 모두 있는가
  3. run_id 가 유일한가
  4. 값이 null 인 지표에 measurement_notes 사유가 있는가  (0 으로 채우기 방지)
  5. status / is_warmup / phase 가 서로 모순되지 않는가
  6. 채점 레코드의 run_id 가 실제 실행 기록에 존재하는가 (역추적 가능성)
  7. 본 실험 커버리지 — 계획된 조합 중 빠진 run_id
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config, recorder, schema, scoring


@dataclass
class ValidationReport:
    target: str
    checked: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        head = f"[{'OK' if self.ok else 'FAIL'}] {self.target} — {self.checked}건 검사"
        lines = [head]
        for e in self.errors:
            lines.append(f"  ERROR  {e}")
        for w in self.warnings:
            lines.append(f"  WARN   {w}")
        if self.ok and not self.warnings:
            lines.append("  문제 없음")
        return "\n".join(lines)


def _check_missing_reasons(
    rec: dict[str, Any],
    metric_fields: tuple[str, ...],
    report: ValidationReport,
) -> None:
    """값이 None 인 지표에는 사유가 있어야 한다."""
    run_id = rec.get("run_id", "?")
    notes = rec.get("measurement_notes") or {}
    for f in metric_fields:
        if f not in rec:
            continue
        if rec[f] is None and f not in notes:
            report.errors.append(f"{run_id}: {f} 가 null 인데 measurement_notes 에 사유 없음")
        if rec[f] == 0 and f in notes:
            report.warnings.append(
                f"{run_id}: {f} 가 0 인데 사유도 있음 — 측정 불가면 null 이어야 함"
            )


def _check_consistency(rec: dict[str, Any], report: ValidationReport) -> None:
    run_id = rec.get("run_id", "?")

    phase = rec.get("phase")
    if phase not in config.ALL_PHASES:
        report.errors.append(f"{run_id}: 알 수 없는 phase={phase!r}")

    if rec.get("is_warmup") != (phase == config.PHASE_WARMUP):
        report.errors.append(f"{run_id}: is_warmup={rec.get('is_warmup')} 과 phase={phase!r} 불일치")

    status = rec.get("status")
    if status not in (config.STATUS_SUCCESS, config.STATUS_ERROR):
        report.errors.append(f"{run_id}: 알 수 없는 status={status!r}")

    if status == config.STATUS_ERROR and not rec.get("error_type"):
        report.errors.append(f"{run_id}: status=error 인데 error_type 없음")

    if status == config.STATUS_SUCCESS and rec.get("response_text") is None:
        notes = rec.get("measurement_notes") or {}
        if "response_text" not in notes:
            report.errors.append(f"{run_id}: status=success 인데 response_text 가 null (사유도 없음)")

    if phase == config.PHASE_RETRY and not rec.get("retry_of_run_id"):
        report.errors.append(f"{run_id}: phase=retry 인데 retry_of_run_id 없음")


def validate_runs(
    path: Path,
    fields: tuple[schema.FieldSpec, ...],
    metric_fields: tuple[str, ...],
) -> ValidationReport:
    report = ValidationReport(target=str(path))
    required = schema.required_keys(fields)
    seen: dict[str, int] = {}

    try:
        records = list(recorder.iter_records(path))
    except ValueError as e:
        report.errors.append(str(e))
        return report

    for idx, rec in enumerate(records, 1):
        report.checked += 1
        run_id = rec.get("run_id")

        missing = [k for k in required if k not in rec]
        if missing:
            report.errors.append(f"line {idx} ({run_id}): 필드 누락 {missing}")

        if not run_id:
            report.errors.append(f"line {idx}: run_id 없음")
            continue

        if run_id in seen:
            report.errors.append(f"{run_id}: run_id 중복 (line {seen[run_id]}, {idx})")
        seen[run_id] = idx

        _check_consistency(rec, report)
        _check_missing_reasons(rec, metric_fields, report)

    return report


def validate_local_runs(path: Path | None = None) -> ValidationReport:
    return validate_runs(
        path or config.LOCAL_RUNS_PATH,
        schema.LOCAL_RUN_FIELDS,
        schema.LOCAL_METRIC_FIELDS,
    )


def validate_cloud_runs(path: Path | None = None) -> ValidationReport:
    return validate_runs(
        path or config.CLOUD_RUNS_PATH,
        schema.CLOUD_RUN_FIELDS,
        schema.CLOUD_METRIC_FIELDS,
    )


def validate_scores(path: Path | None = None) -> ValidationReport:
    """채점 입력면(eval-results.md)을 검사한다.

    블록 제목이 run_id 가 되므로, 제목이 실제 실행 기록과 맞는지 확인한다.
    """
    path = path or config.EVAL_RESULTS_PATH
    report = ValidationReport(target=str(path))

    runs = {
        r["run_id"]: r
        for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
        if r.get("run_id")
    }
    qmap = config.question_map()
    scale = config.load_questions().get("score_scale") or {}
    lo, hi = scale.get("min"), scale.get("max")

    blocks = scoring.parse(path)
    scored = [b for b in blocks if any(v is not None for v in b["scores"].values())]
    report.checked = len(blocks)

    seen: set[str] = set()
    for b in blocks:
        run_id = b["run_id"]
        if run_id in seen:
            report.errors.append(f"{run_id}: 같은 제목의 블록이 두 번 있습니다")
        seen.add(run_id)

        q = qmap.get(b["question_id"])
        if q is None:
            report.errors.append(f"{run_id}: 질문 {b['question_id']} 가 questions.json 에 없습니다")
            continue

        # 블록에 적힌 기준이 그 질문의 기준과 맞는가
        expected = set(q["criteria_codes"])
        got = set(b["scores"])
        if expected != got:
            report.errors.append(
                f"{run_id}: 평가 기준 불일치 (질문={sorted(expected)}, 블록={sorted(got)})"
            )

        if b not in scored:
            continue  # 아직 채점 전 — 그 자체는 문제가 아니다

        if run_id not in runs:
            report.errors.append(f"{run_id}: 대응하는 실행 기록이 없습니다 — 역추적 불가")
        elif runs[run_id].get("status") == config.STATUS_ERROR:
            report.warnings.append(f"{run_id}: 원본이 호출 실패인데 점수가 적혀 있습니다")

        for code, value in b["scores"].items():
            if value is None:
                report.warnings.append(f"{run_id}: {code} 점수가 비어 있습니다")
                continue
            if lo is not None and hi is not None and not (lo <= value <= hi):
                report.errors.append(f"{run_id}: {code} 점수 {value} 가 척도 {lo}~{hi} 밖입니다")
            if not b["rationales"].get(code):
                report.warnings.append(f"{run_id}: {code} 점수는 있는데 근거가 비어 있습니다")

    if scored:
        report.warnings.insert(0, scoring.summary())

    return report


def check_coverage(path: Path | None = None) -> ValidationReport:
    """계획된 본 실험 조합 중 빠진 run_id 를 찾는다."""
    path = path or config.LOCAL_RUNS_PATH
    report = ValidationReport(target=f"{path} (본 실험 커버리지)")

    settings = config.load_run_settings()
    models = config.enabled_models()
    questions = config.load_questions()["questions"]

    planned = {
        config.make_run_id(m["model_label"], q["question_id"], r, config.PHASE_MAIN)
        for m in models
        for q in questions
        for r in range(1, settings["repeats"] + 1)
    }
    planned_warmup = {config.make_run_id(m["model_label"], phase=config.PHASE_WARMUP) for m in models}

    actual = recorder.load_run_ids(path)
    report.checked = len(actual)

    missing_main = sorted(planned - actual)
    if missing_main:
        report.warnings.append(f"본 실험 미실행 {len(missing_main)}건 (계획 {len(planned)}건): {missing_main[:10]}{' ...' if len(missing_main) > 10 else ''}")

    missing_warmup = sorted(planned_warmup - actual)
    if missing_warmup:
        report.warnings.append(f"워밍업 미실행: {missing_warmup}")

    unexpected = sorted(a for a in actual if a not in planned and a not in planned_warmup)
    if unexpected:
        report.warnings.append(f"계획 외 run_id {len(unexpected)}건 (재시도/추가 실험이면 정상): {unexpected[:10]}{' ...' if len(unexpected) > 10 else ''}")

    return report


def validate_all() -> list[ValidationReport]:
    return [
        validate_local_runs(),
        validate_cloud_runs(),
        validate_scores(),
        check_coverage(),
    ]


if __name__ == "__main__":
    import sys

    from . import use_utf8_stdout

    use_utf8_stdout()
    reports = validate_all()
    for r in reports:
        print(r.render())
        print()
    sys.exit(0 if all(r.ok for r in reports) else 1)

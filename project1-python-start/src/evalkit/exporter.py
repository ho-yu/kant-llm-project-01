"""집계 결과를 마크다운 표로 변환한다.

출력물은 docs/ 문서에 붙여 넣는 용도이며 data/derived/tables/ 에 저장된다.
표의 모든 수치는 aggregator 가 raw 에서 계산한 값이고, 각 표 아래에
역추적 경로를 함께 적는다.
"""

from __future__ import annotations

from typing import Any

from . import aggregator, config, recorder, scoring


def _rel(path) -> str:
    """마크다운에 넣을 저장소 상대경로. Windows 역슬래시를 슬래시로 바꾼다."""
    return path.relative_to(config.REPO_ROOT).as_posix()


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = [_row(header), "|" + "---|" * len(header)]
    lines += [_row(r) for r in rows]
    return "\n".join(lines)


def _split_tiers(models: dict[str, Any]) -> tuple[list[str], list[str]]:
    """표에 쓸 라벨을 비교 대상 / 부가 테스트로 나눈다.

    성능 측정은 6개 모두 산출물이므로 버리지 않고, 표만 분리한다.
    """
    primary = [l for l in models if config.is_primary(l)]
    extra = [l for l in models if not config.is_primary(l)]
    return primary, extra


def _tier_note() -> str:
    names = ", ".join(m.get("display_name") or m["model_label"] for m in config.primary_models())
    return f"> 비교 대상: {names}. 최종 선정은 이 중에서 한다."


def _stat(metrics: dict[str, Any], key: str, digits: int = 2) -> str:
    """집계 불가면 0 이 아니라 '집계 불가'."""
    st = metrics.get(key)
    if not st or not st.get("available"):
        reason = (st or {}).get("unavailable_reason") or "측정값 없음"
        return f"집계 불가 ({reason})"
    return f"{st['mean']:.{digits}f} (n={st['n']})"


# ---------------------------------------------------------------- 표


def local_summary_table(summary: dict[str, Any] | None = None) -> str:
    """모델별 성능 집계표 — docs/steps/step06.md 의 '모델별 집계표'에 대응."""
    summary = summary or aggregator.aggregate_local()
    models = summary["models"]
    primary, extra = _split_tiers(models)

    def block(labels: list[str]) -> str:
        header = ["지표"] + [models[l]["display_name"] or l for l in labels]
        rows = [
            ["호출 성공 / 전체 시도"]
            + [f"{models[l]['success']} / {models[l]['attempts']}" for l in labels],
            ["평균 전체 응답 시간 (초)"] + [_stat(models[l]["metrics"], "elapsed_sec") for l in labels],
            ["평균 로딩 시간 (초)"] + [_stat(models[l]["metrics"], "load_duration_sec") for l in labels],
            ["평균 출력 토큰 수"] + [_stat(models[l]["metrics"], "eval_count", 1) for l in labels],
            ["평균 생성 속도 (tokens/s)"] + [_stat(models[l]["metrics"], "tokens_per_sec") for l in labels],
            ["VRAM (MiB, 관측 시점)"] + [_stat(models[l]["metrics"], "size_vram_mib", 1) for l in labels],
        ]
        return _table(header, rows)

    out = [block(primary), ""]
    if extra:
        out += [
            "### 부가 테스트",
            "",
            "같은 조건으로 돌린 기록이다. 품질 채점과 최종 선정 대상에서는 빠진다.",
            "",
            block(extra),
            "",
        ]
    out.append(_tier_note())
    out.append(f"> 집계 범위: phase={summary['scope_phases']} (워밍업·재시도·추가 실험 제외)")
    out.append(f"> 파일 내 전체 {summary['total_records_in_file']}건 중 집계 대상 {summary['records_in_scope']}건")
    out.append("> n 은 지표마다 다르다. 측정값을 얻지 못한 회차는 해당 지표의 평균과 n 에서 제외된다.")
    out.append("> VRAM 은 응답 직후 관측 시점의 값이며 최대 VRAM 이 아니다.")
    out.append(f"> 원본: `{_rel(config.LOCAL_RUNS_PATH)}`")
    return "\n".join(out)


def quality_table(quality: dict[str, Any] | None = None) -> str:
    """기준별 품질 점수표."""
    quality = quality or aggregator.aggregate_quality()
    models = quality["models"]
    primary, extra = _split_tiers(models)
    criteria = quality["criteria"]

    def block(labels: list[str]) -> str:
        header = ["평가 기준"] + [models[l]["display_name"] or l for l in labels]
        rows = [
            [f"{code}. {name}"] + [_stat(models[l]["per_criterion"], code) for l in labels]
            for code, name in criteria.items()
        ]
        return _table(header, rows)

    out = [block(primary), ""]
    scored_extra = [l for l in extra if models[l].get("scored_count")]
    if scored_extra:
        out += [
            "**부가 테스트** — 판정에 반영되지 않는다.",
            "",
            block(scored_extra),
            "",
        ]
    out.append(_tier_note())
    out.append("> 기준마다 출제 문항 수가 달라 n 이 다르다.")
    out.append(f"> 원본: `{_rel(config.EVAL_RESULTS_PATH)}` (블록 제목이 run_id 가 된다)")
    return "\n".join(out)


def case_type_table(quality: dict[str, Any] | None = None) -> str:
    quality = quality or aggregator.aggregate_quality()
    models = quality["models"]
    labels = [l for l in models if config.is_primary(l)]  # 비교 대상만
    case_types = sorted({ct for l in labels for ct in models[l]["by_case_type"]})

    header = ["모델"] + case_types
    rows = [
        [models[l]["display_name"] or l] + [_stat(models[l]["by_case_type"], ct) for ct in case_types]
        for l in labels
    ]
    return _table(header, rows)


def repeat_consistency_table(quality: dict[str, Any] | None = None) -> str:
    """Run 간 일관성 — 같은 질문을 2회 돌린 결과 차이."""
    quality = quality or aggregator.aggregate_quality()
    models = quality["models"]
    labels = [l for l in models if config.is_primary(l)]  # 비교 대상만
    reps = sorted({r for l in labels for r in models[l]["by_repeat"]})

    header = ["모델"] + reps
    rows = [
        [models[l]["display_name"] or l] + [_stat(models[l]["by_repeat"], r) for r in reps]
        for l in labels
    ]
    return _table(header, rows)


def per_question_table() -> str:
    """질문별 × 모델별 품질 평균. 채점 블록에서 바로 계산한다.

    예전에는 eval-results.md 안에 질문마다 집계표를 두고 손으로 옮겨 적었다.
    같은 값을 두 곳에 쓰면 어긋나므로 여기서 만든다.
    """
    labels = config.primary_labels()
    names = {m["model_label"]: m.get("display_name") or m["model_label"]
             for m in config.primary_models()}
    by = {}
    for rec in scoring.scored_only():
        by.setdefault(rec["question_id"], {}).setdefault(rec["model_label"], []).append(rec)

    header = ["질문"] + [names[l] for l in labels]
    rows = []
    for q in config.load_questions()["questions"]:
        qid = q["question_id"]
        cells = [f"{qid} {q['title']}"]
        for l in labels:
            recs = by.get(qid, {}).get(l, [])
            vals = [r["average"] for r in recs if r.get("average") is not None]
            cells.append(f"{sum(vals) / len(vals):.2f} (n={len(vals)})" if vals else "미채점")
        rows.append(cells)

    out = [_table(header, rows), ""]
    out.append("> 각 칸은 그 질문 Run 1·Run 2 의 블록 평균이다. n 은 채점된 회차 수.")
    out.append(f"> 원본: `{_rel(config.EVAL_RESULTS_PATH)}`")
    return "\n".join(out)


def error_table(summary: dict[str, Any] | None = None) -> str:
    """축 1(호출 실패)만 모은 표. 품질 점수와 섞지 않는다."""
    summary = summary or aggregator.aggregate_local()
    models = summary["models"]
    rows = []
    for label, m in models.items():
        if not m["error_run_ids"]:
            continue
        rows.append([m["display_name"] or label, str(m["errors"]), ", ".join(m["error_run_ids"])])

    if not rows:
        return "호출 실패 없음."
    return _table(["모델", "실패 수", "run_id"], rows)


def local_cloud_table(
    local: dict[str, Any] | None = None,
    cloud: dict[str, Any] | None = None,
) -> str:
    """산출물 4 — Local vs Cloud. 실측 항목만 채우고 정성 항목은 비워 둔다.

    로컬은 질문 10개 x 2회, Cloud 는 공통 5문항 x 1회다.
    두 열의 문항 수와 반복 수가 다르므로 표 안과 주석에 그 사실을 함께 적는다.
    문항 단위로 맞춰 보려면 step07.md 의 '동일 문항 비교표' 를 쓴다.
    """
    local = local or aggregator.aggregate_local()
    cloud = cloud or aggregator.aggregate_cloud()

    n_q = len(config.load_questions()["questions"])
    n_cq = len(cloud["cloud_question_ids"])
    repeats = config.load_run_settings()["repeats"]

    rows = [
        [
            "집계 범위",
            f"질문 {n_q}개 x {repeats}회",
            f"공통 {n_cq}문항 x 1회",
            "**같은 문항 수가 아니다**",
        ],
        ["Quality", "(품질표 참조)", "(품질표 참조)", "실측"],
        [
            "Latency",
            " / ".join(
                f"{local['models'][l]['display_name'] or l} {_stat(local['models'][l]['metrics'], 'elapsed_sec')}"
                for l in local["models"]
                if config.is_primary(l)
            ),
            _stat(cloud["metrics"], "elapsed_sec"),
            "실측",
        ],
        ["Cost", "", _stat(cloud["metrics"], "estimated_cost", 4), "Cloud 는 추정치 / 로컬은 장비·전력·관리 비용"],
        ["Security", "", "", "운영 조건 분석"],
        ["Infrastructure", "", "", "운영 조건 분석"],
        ["Customization", "", "", "운영 조건 분석"],
        ["Operations", "", "", "운영 조건 분석"],
    ]

    out = [_table(["기준", "Local LLM", "Cloud API", "구분"], rows), ""]
    out.append(_tier_note())
    out.append(
        f"> **집계 범위가 다르다** — 로컬은 질문 {n_q}개 x {repeats}회, "
        f"Cloud 는 공통 {n_cq}문항 {cloud['cloud_question_ids']} x 1회다. "
        "이 표의 Local 열은 10문항 전체 평균이므로 Cloud 열과 같은 질문 집합이 아니다."
    )
    out.append(
        "> 문항 단위로 맞춰 보려면 `docs/steps/step07.md` 의 '동일 문항 비교표' 를 쓴다 — "
        "거기서는 같은 질문끼리 비교한다."
    )
    out.append(
        "> 로컬 값은 Run 1·Run 2 **평균**이다. 회차 중 좋은 쪽만 골라 쓰지 않는다."
    )
    for name, why in config.cloud_option_gaps().items():
        out.append(f"> 동일 조건 아님 — {name}: {why}")
    out.append("> 실측 결과와 운영 조건 분석을 구분한다. 로컬 총비용을 0 으로 적지 않는다.")
    return "\n".join(out)


def model_comparison_table() -> str:
    """산출물 2 — 제원 비교.

    과제가 요구하는 항목을 행으로 두고 모델을 열로 둔다 (deliverables.md 형식).
    제원은 environment.json, VRAM 은 실행 기록, 주요 특징은 models.json 에서 온다.
    실측값과 문서 기반 값을 섞지 않도록 출처를 표 아래에 적는다.
    """
    env = config.load_environment()
    entries = {m["model_label"]: m for m in env.get("models", []) if m.get("model_label")}
    meta = {m["model_label"]: m for m in config.enabled_models()}
    local = aggregator.aggregate_local()

    labels = [l for l in config.primary_labels() if l in entries]
    if not labels:
        return "> `data/env/environment.json` 을 먼저 채운다."

    def ctx_of(label: str) -> str:
        for rid in local["models"].get(label, {}).get("run_ids", []):
            t = aggregator.trace(rid)
            if t and t["run"].get("context_length"):
                return str(t["run"]["context_length"])
        return ""

    def vram_of(label: str) -> str:
        return _stat(local["models"].get(label, {}).get("metrics", {}), "size_vram_mib", 1)

    def name_of(label: str) -> str:
        """표시용 모델 이름. 태그의 저장소명에서 뽑는다."""
        tag = entries[label].get("model_tag") or ""
        return tag.split("/")[-1].split(":")[0] or label

    def size_of(label: str) -> str:
        n = entries[label].get("download_size_bytes")
        return f"{n / 1_073_741_824:.2f} GB" if n else ""

    rows: list[tuple[str, object]] = [
        ("Model Name", name_of),
        ("Parameter", lambda l: entries[l].get("parameter_size") or ""),
        ("License (선언)", lambda l: entries[l].get("license_declared") or ""),
        ("License (Base)", lambda l: entries[l].get("license_base_model") or ""),
        ("문서상 최대 Context", lambda l: str(entries[l].get("doc_max_context") or "(미확인)")),
        ("실험 Context", ctx_of),
        ("Quantization", lambda l: entries[l].get("quantization_level") or ""),
        ("VRAM (관측 시점)", vram_of),
        ("다운로드 크기", size_of),
        ("주요 특징", lambda l: "<br>".join(meta.get(l, {}).get("highlights") or [])),
        ("Model Card (GGUF)", lambda l: entries[l].get("model_card_url") or ""),
        ("Model Card (원본)", lambda l: entries[l].get("upstream_model_card_url") or ""),
        ("모델 태그", lambda l: f"`{entries[l].get('model_tag') or ''}`"),
        ("digest", lambda l: f"`{(entries[l].get('digest') or '')[:12]}`"),
    ]

    header = ["항목"] + [meta.get(l, {}).get("display_name") or l for l in labels]
    body = [[label] + [str(fn(l)) for l in labels] for label, fn in rows]

    out = [_table(header, body), ""]
    out.append(_tier_note())
    out.append("> `문서상 최대 Context` 는 Model Card 값(문서 기반), `실험 Context` 는 실행 기록의 context_length(실측)다.")
    out.append("> VRAM 은 응답 직후 관측값의 평균이며 최대 VRAM 이 아니다.")
    out.append("> `주요 특징` 은 Model Card 기반 설명이며 측정 결과가 아니다.")
    out.append(f"> 출처: `{_rel(config.ENVIRONMENT_PATH)}`, `{_rel(config.LOCAL_RUNS_PATH)}`, `{_rel(config.MODELS_PATH)}`")

    extra = [l for l in entries if not config.is_primary(l)]
    if extra:
        out += ["", "### 부가 테스트 (참고)", ""]
        ex_header = ["라벨", "Model Name", "Parameter", "License (선언)", "모델 태그"]
        ex_rows = [
            [l, name_of(l), entries[l].get("parameter_size") or "",
             entries[l].get("license_declared") or "",
             f"`{entries[l].get('model_tag') or ''}`"]
            for l in extra
        ]
        out.append(_table(ex_header, ex_rows))
        out.append("")
        out.append("> 채점·선정 대상이 아니다. 제외 근거로 남긴다.")

    return "\n".join(out)


# ---------------------------------------------------------------- 채점 원본 내보내기


def write_scores_jsonl() -> str:
    """채점 결과를 JSONL 로 내보낸다.

    과제는 원본 결과를 '다시 읽을 수 있는 형식'으로 요구한다.
    실행 기록은 runs.jsonl 로 이미 그 조건을 채우지만, 점수와 근거는
    eval-results.md 안에만 있어 사람만 읽을 수 있었다.

    채점 입력면은 그대로 두고 여기서 뽑아낸다. 이 파일은 생성물이므로
    직접 고치지 않는다 — 고칠 곳은 언제나 eval-results.md 다.

    실행 기록과 run_id 로 조인해 질문·모델이 어긋나지 않는지 확인하고,
    응답 원문 대신 그 위치를 남긴다(원문은 runs.jsonl 에 있다).
    """
    import json

    runs = {
        r["run_id"]: r
        for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
        if r.get("run_id")
    }
    criteria = config.load_questions()["criteria"]

    rows = []
    for rec in scoring.scored_only():
        run = runs.get(rec["run_id"], {})
        rows.append({
            "run_id": rec["run_id"],
            "source_file": "local",
            "question_id": rec["question_id"],
            "model_label": rec["model_label"],
            "model_tag": run.get("model_tag"),
            "repeat": rec["repeat"],
            "scores": rec["scores"],
            "criteria_names": {c: criteria[c] for c in rec["scores"]},
            "rationales": rec["rationales"],
            "average": rec["average"],
            "average_source": rec["average_source"],
            "reviewed": rec["reviewed"],
            "revision_reason": rec["revision_reason"],
            "status_note": rec["status_note"],
            "run_status": run.get("status"),
            "source": rec["source"],
        })

    config.DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    with config.SCORES_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return f"{config.SCORES_PATH} ({len(rows)}건)"


# ---------------------------------------------------------------- 파일로 쓰기


def write_tables() -> list[str]:
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)

    local = aggregator.aggregate_local()
    quality = aggregator.aggregate_quality()
    cloud = aggregator.aggregate_cloud()

    docs = {
        "model_comparison.md": ["# Model Comparison Table (생성물)", "", model_comparison_table()],
        "local_summary.md": [
            "# 로컬 모델 성능 집계 (생성물)", "",
            local_summary_table(local), "",
            "## 품질 점수", "", quality_table(quality), "",
            "## 질문별", "", per_question_table(), "",
            "## 사례 유형별", "", case_type_table(quality), "",
            "## Run 간 일관성", "", repeat_consistency_table(quality), "",
            "## 호출 실패", "", error_table(local),
        ],
        "local_cloud.md": ["# Local vs Cloud (생성물)", "", local_cloud_table(local, cloud)],
    }

    written = [write_scores_jsonl()]
    for name, parts in docs.items():
        path = config.TABLES_DIR / name
        body = "\n".join(parts)
        header = (
            f"<!-- 자동 생성됨: python -m evalkit.exporter\n"
            f"     직접 수정하지 말 것. 원본: data/raw/, docs/eval-results.md -->\n\n"
        )
        path.write_text(header + body + "\n", encoding="utf-8")
        written.append(str(path))

    return written


if __name__ == "__main__":
    from . import use_utf8_stdout

    use_utf8_stdout()
    for p in write_tables():
        print("written:", p)

"""STEP 04 / STEP 06 문서에 그대로 붙일 수 있는 형태로 출력한다."""

from __future__ import annotations

from typing import Any

from . import aggregator, config, recorder, schema

BAR = "=" * 62


def _quant(env_model: dict[str, Any], run: dict[str, Any]) -> str:
    """양자화 표기.

    client.list() 와 client.ps() 가 서로 다른 값을 돌려주는 경우가 있다
    (list 는 Q4_K_M, ps 는 unknown). list 쪽이 정확하므로 그 값을 쓰되,
    다르면 ps 가 무엇이라고 했는지 함께 남긴다.
    """
    listed = env_model.get("quantization_level")
    reported = run.get("quantization_level")
    if listed and listed != reported:
        return f"{listed} (ps 보고: {reported})"
    return str(listed or reported)


def _overall_mean(model_quality: dict[str, Any]) -> tuple[float | None, int]:
    """기준별 점수를 모두 합쳐 낸 전체 평균과 집계 응답 수."""
    values: list[float] = []
    for stat in (model_quality.get("per_criterion") or {}).values():
        if stat.get("available"):
            values.extend(stat.get("values") or [])
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def _overall(model_quality: dict[str, Any]) -> str:
    mean, n = _overall_mean(model_quality)
    return "집계 불가" if mean is None else f"{mean:.2f} (n={n})"


def _condition6(model_quality: dict[str, Any], threshold: float) -> str:
    """STEP 2 필수 조건 6 — 채점이 끝나기 전에는 판정하지 않는다."""
    mean, n = _overall_mean(model_quality)
    if mean is None:
        return "판정 전"
    return f"{'Pass' if mean >= threshold else 'Fail'} ({mean:.2f})"


def _fmt(stat: dict[str, Any] | None, unit: str = "", digits: int = 2) -> str:
    """집계값 한 칸. 유효값이 없으면 0 이 아니라 '집계 불가'."""
    if not stat or not stat.get("available"):
        return "집계 불가"
    return f"{stat['mean']:.{digits}f}{unit} (n={stat['n']})"


# ---------------------------------------------------------------- STEP 04


def step04(model_label: str) -> str:
    """실행 환경 + 이 모델의 식별값 + 저장된 기록 1건 확인."""
    env = config.load_environment()
    rt, hw = env.get("runtime", {}), env.get("hardware", {})
    pkgs = rt.get("packages", {})

    lines = [
        f"## STEP 04 — 실행 환경 / {model_label} 연결 확인",
        "",
        "### 실행 환경",
        "",
        "| 항목 | 값 |",
        "|---|---|",
        f"| OS | {env.get('platform', {}).get('os')} {env.get('platform', {}).get('os_version')} |",
        f"| Python | {rt.get('python_version')} |",
        f"| Ollama | {rt.get('ollama_version')} |",
        f"| Python `ollama` 패키지 | {pkgs.get('ollama')} |",
        f"| Python `openai` 패키지 | {pkgs.get('openai')} |",
        f"| GPU | {hw.get('gpu_name')} |",
        f"| VRAM | {hw.get('vram_total_mib')} MiB |",
        f"| CPU | {hw.get('cpu')} |",
        f"| 시스템 RAM | {hw.get('system_ram_gb')} GB |",
        "",
    ]

    # 이 모델의 실행 시점 식별값 — 기록에서 가져온다(수기 입력 아님)
    runs = [
        r
        for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
        if r.get("model_label") == model_label and r.get("status") == config.STATUS_SUCCESS
    ]
    meta = next((m for m in config.enabled_models() if m["model_label"] == model_label), {})
    env_model = next(
        (m for m in env.get("models", []) if m.get("model_label") == model_label), {}
    )

    lines += [
        f"### {meta.get('display_name') or model_label} 식별값",
        "",
        "| 항목 | 값 | 출처 |",
        "|---|---|---|",
        f"| 모델 태그 | `{meta.get('model_tag')}` | `models.json` |",
    ]

    if runs:
        s = runs[0]
        size = env_model.get("download_size_bytes")
        lines += [
            f"| digest | `{(s.get('digest') or '')[:16]}...` | 실행 기록 |",
            f"| 양자화 | {_quant(env_model, s)} | `client.list()` |",
            f"| 실험에 사용한 Context | {s.get('context_length')} | 실행 기록 |",
            f"| 문서상 최대 Context | {env_model.get('doc_max_context') or '(미기재)'} | Model Card |",
            f"| 다운로드 크기 | {f'{size / 1_073_741_824:.2f} GB' if size else '(미수집)'} | `client.list()` |",
            f"| CPU/GPU 적재 | {s.get('processor')} | 실행 기록 |",
        ]
    else:
        lines.append("| (성공한 실행 기록 없음) | | |")

    lines += ["", "### 저장 후 다시 읽어 확인한 기록 1건", ""]
    if runs:
        s = runs[0]
        text = (s.get("response_text") or "").strip()
        preview = text[:200] + (" …" if len(text) > 200 else "")
        lines += [
            "```",
            f"파일     : data/raw/local/runs.jsonl",
            f"run_id   : {s['run_id']}",
            f"질문     : {s.get('question_id')}",
            f"설정     : {s.get('options')}",
            f"상태     : {s.get('status')} / done_reason={s.get('done_reason')}",
            f"응답 앞부분:",
            preview,
            "```",
        ]
    else:
        lines.append("_아직 성공한 기록이 없습니다._")

    return "\n".join(lines)


# ---------------------------------------------------------------- STEP 06


def step06(model_label: str | None = None) -> str:
    """모델별 성능 집계. model_label 을 주면 그 모델만 강조해서 보여준다."""
    summary = aggregator.aggregate_local()
    models = summary["models"]
    labels = [model_label] if model_label and model_label in models else list(models)

    lines = [
        "## STEP 06 — 성능 측정",
        "",
        "| 지표 | " + " | ".join(models[l]["display_name"] or l for l in labels) + " |",
        "|---|" + "---|" * len(labels),
    ]

    rows = [
        ("호출 성공 / 전체 시도", lambda m: f"{m['success']} / {m['attempts']}"),
        ("평균 전체 응답 시간", lambda m: _fmt(m["metrics"].get("elapsed_sec"), "s")),
        ("평균 로딩 시간", lambda m: _fmt(m["metrics"].get("load_duration_sec"), "s")),
        ("평균 출력 토큰 수", lambda m: _fmt(m["metrics"].get("eval_count"), "", 1)),
        ("평균 입력 토큰 수", lambda m: _fmt(m["metrics"].get("prompt_eval_count"), "", 1)),
        ("평균 생성 속도", lambda m: _fmt(m["metrics"].get("tokens_per_sec"), " t/s")),
        ("VRAM (관측 시점)", lambda m: _fmt(m["metrics"].get("size_vram_mib"), " MiB", 1)),
    ]
    for label, fn in rows:
        lines.append(f"| {label} | " + " | ".join(fn(models[l]) for l in labels) + " |")

    # 품질 평균과 STEP 2 필수 조건 6 판정 — 채점이 시작된 뒤에만 보여준다
    quality = aggregator.aggregate_quality()["models"]
    scale = config.load_questions().get("score_scale") or {}
    threshold = scale.get("pass_threshold")
    if any(quality.get(l, {}).get("scored_count") for l in labels):
        lines.append("| 평균 품질 점수 | " + " | ".join(_overall(quality.get(l, {})) for l in labels) + " |")
        if threshold is not None:
            lines.append(
                f"| 조건 6 판정 (평균 {threshold} 이상) | "
                + " | ".join(_condition6(quality.get(l, {}), threshold) for l in labels)
                + " |"
            )

    lines += [
        "",
        f"> 집계 범위: 본 실험만 (워밍업·재시도 제외). 파일 전체 {summary['total_records_in_file']}건 중 {summary['records_in_scope']}건.",
        "> `n` 은 지표마다 다르다. 측정값을 얻지 못한 회차는 그 지표의 평균과 `n` 에서 제외된다.",
        "> VRAM 은 응답 직후 관측 시점의 값이며 최대 VRAM 이 아니다.",
        "> CPU/GPU 적재 상태는 GPU 이용률이 아니다.",
    ]

    # 실패 / 측정 누락 — 있을 때만
    problems: list[str] = []
    for l in labels:
        m = models[l]
        for rid in m["error_run_ids"]:
            problems.append(f"| {rid} | 호출 실패 | 원본 기록의 error_message 참조 |")

    missing: dict[str, list[str]] = {}
    for rec in recorder.iter_records(config.LOCAL_RUNS_PATH):
        if rec.get("model_label") not in labels or rec.get("phase") != config.PHASE_MAIN:
            continue
        if rec.get("status") != config.STATUS_SUCCESS:
            continue
        for field, reason in (rec.get("measurement_notes") or {}).items():
            # 성능 지표만 다룬다. quantization_level 같은 메타데이터는
            # client.list() 로 environment.json 에 이미 들어가 있으므로
            # ps 가 unknown 을 보고해도 "측정 누락" 이 아니다.
            if field not in schema.LOCAL_METRIC_FIELDS:
                continue
            missing.setdefault(f"{field} — {reason}", []).append(rec["run_id"])

    for key, rids in missing.items():
        shown = ", ".join(rids[:3]) + (f" 외 {len(rids) - 3}건" if len(rids) > 3 else "")
        problems.append(f"| {shown} | 측정 누락 | {key} |")

    if problems:
        lines += [
            "",
            "### 실패 / 측정 누락",
            "",
            "| 회차 | 구분 | 사유 |",
            "|---|---|---|",
            *problems,
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------- 진행 상황


def progress(model_label: str | None = None) -> str:
    settings = config.load_run_settings()
    total = len(config.load_questions()["questions"]) * settings["repeats"]
    records = list(recorder.iter_records(config.LOCAL_RUNS_PATH))

    lines = [f"{'모델':<22} {'본실험':>9} {'성공':>6} {'실패':>6} {'워밍업':>7}"]
    for m in config.enabled_models():
        label = m["model_label"]
        rows = [r for r in records if r.get("model_label") == label]
        main = [r for r in rows if r.get("phase") == config.PHASE_MAIN]
        ok = sum(1 for r in main if r.get("status") == config.STATUS_SUCCESS)
        warm = "있음" if any(r.get("phase") == config.PHASE_WARMUP for r in rows) else "없음"
        mark = " <-" if label == model_label else ""
        name = m.get("display_name") or label
        lines.append(f"{name:<22} {f'{len(main)}/{total}':>9} {ok:>6} {len(main) - ok:>6} {warm:>7}{mark}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 사전 점검


def preflight() -> list[str]:
    """실험을 시작하기 전에 반드시 정해져 있어야 하는 값들."""
    settings = config.load_run_settings()
    options = settings.get("options") or {}
    problems = []

    if options.get("num_predict") is None:
        problems.append(
            "options.num_predict 가 비어 있습니다. 출력 한도가 없으면 생성이 폭주합니다 "
            "(실측: 한 질문에 40,960 토큰 / 13분 이상)."
        )
    if settings.get("timeout_sec") is None:
        problems.append("timeout_sec 가 비어 있습니다. 모델이 멈추면 실험이 무한 대기합니다.")
    if options.get("num_ctx") is None:
        problems.append(
            "options.num_ctx 가 비어 있습니다. 산출물의 '실험에 사용한 Context' 근거가 없어집니다."
        )
    if settings.get("warmup_question_id") is None:
        problems.append(
            "warmup_question_id 가 비어 있습니다. 워밍업이 건너뛰어집니다 (과제 필수 항목)."
        )
    return problems

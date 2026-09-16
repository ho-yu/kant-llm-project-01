"""집계 결과를 마크다운 표로 변환한다.

출력물은 docs/ 문서에 붙여 넣는 용도이며 data/derived/tables/ 에 저장된다.
표의 모든 수치는 aggregator 가 raw 에서 계산한 값이고, 각 표 아래에
역추적 경로를 함께 적는다.
"""

from __future__ import annotations

from typing import Any

from . import aggregator, config


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
    """산출물 4 — Local vs Cloud. 실측 항목만 채우고 정성 항목은 비워 둔다."""
    local = local or aggregator.aggregate_local()
    cloud = cloud or aggregator.aggregate_cloud()

    rows = [
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
    out.append(f"> 반복 수: 로컬 질문당 2회, Cloud 질문당 1회. Cloud 대상 문항 {cloud['cloud_question_ids']}")
    for name, why in config.cloud_option_gaps().items():
        out.append(f"> 동일 조건 아님 — {name}: {why}")
    out.append("> 실측 결과와 운영 조건 분석을 구분한다. 로컬 총비용을 0 으로 적지 않는다.")
    return "\n".join(out)


def model_comparison_table() -> str:
    """산출물 2 — 제원 비교. environment.json 에서 읽는다(실행 기록 아님)."""
    env = config.load_environment()
    entries = [m for m in env.get("models", []) if m.get("model_label")]

    header = [
        "구분", "라벨", "모델 태그", "digest", "양자화",
        "다운로드 크기", "문서상 최대 Context", "실험 Context", "License(선언)", "License(Base)",
    ]
    # 비교 대상을 먼저 (산출물 2 의 후보 열 순서와 맞춘다)
    entries.sort(key=lambda m: 0 if config.is_primary(m["model_label"]) else 1)

    if not entries:
        return (
            _table(header, [["(environment.json 미작성)"] + [""] * (len(header) - 1)])
            + "\n\n> `data/env/environment.json` 을 먼저 채운다."
        )

    local = aggregator.aggregate_local()
    rows = []
    for m in entries:
        label = m["model_label"]
        ctx = None
        for rid in local["models"].get(label, {}).get("run_ids", []):
            t = aggregator.trace(rid)
            if t and t["run"].get("context_length"):
                ctx = t["run"]["context_length"]
                break

        size = m.get("download_size_bytes")
        rows.append([
            "비교 대상" if config.is_primary(label) else "부가",
            label,
            f"`{m.get('model_tag') or ''}`",
            (m.get("digest") or "")[:12],
            m.get("quantization_level") or "",
            f"{size / 1_073_741_824:.2f} GB" if size else "",
            str(m.get("doc_max_context") or ""),
            str(ctx or ""),
            m.get("license_declared") or "",
            m.get("license_base_model") or "",
        ])

    out = [_table(header, rows), ""]
    out.append(_tier_note())
    out.append("> `문서상 최대 Context` 는 Model Card 값, `실험 Context` 는 실행 기록의 context_length 다.")
    out.append(f"> 출처: `{_rel(config.ENVIRONMENT_PATH)}`, `{_rel(config.LOCAL_RUNS_PATH)}`")
    return "\n".join(out)


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
            "## 사례 유형별", "", case_type_table(quality), "",
            "## Run 간 일관성", "", repeat_consistency_table(quality), "",
            "## 호출 실패", "", error_table(local),
        ],
        "local_cloud.md": ["# Local vs Cloud (생성물)", "", local_cloud_table(local, cloud)],
    }

    written = []
    for name, parts in docs.items():
        path = config.TABLES_DIR / name
        body = "\n".join(parts)
        header = (
            f"<!-- 자동 생성됨: python -m evalkit.exporter\n"
            f"     직접 수정하지 말 것. 원본: data/raw/, data/scoring/ -->\n\n"
        )
        path.write_text(header + body + "\n", encoding="utf-8")
        written.append(str(path))

    return written


if __name__ == "__main__":
    from . import use_utf8_stdout

    use_utf8_stdout()
    for p in write_tables():
        print("written:", p)

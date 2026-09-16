"""채점하려고 원본 응답을 읽을 수 있게 뽑아낸다.

runs.jsonl 은 한 줄에 JSON 전체가 들어 있어 눈으로 읽을 수 없다.
질문 하나에 대한 모든 모델·회차의 응답을 한 파일로 모아
eval-results.md 옆에 놓고 채점할 수 있게 한다.

eval-results.md 의 블록 순서(질문 -> 모델 -> 회차)와 같은 순서로 나온다.
"""

from __future__ import annotations

from typing import Any

from . import config, recorder


def _runs_for(question_id: str) -> list[dict[str, Any]]:
    """해당 질문의 본 실험 회차를 모델·회차 순으로."""
    order = {m["model_label"]: i for i, m in enumerate(config.enabled_models())}
    rows = [
        r
        for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
        if r.get("question_id") == question_id and r.get("phase") == config.PHASE_MAIN
    ]
    # 채점 대상을 먼저. 부가 테스트를 스크롤로 지나치지 않아도 된다.
    rows.sort(
        key=lambda r: (
            0 if config.is_primary(r.get("model_label")) else 1,
            order.get(r.get("model_label"), 99),
            r.get("repeat") or 0,
        )
    )
    return rows


def render(question_id: str) -> str:
    q = config.question_map().get(question_id)
    if q is None:
        return f"_{question_id} 는 questions.json 에 없습니다._"

    crit = config.load_questions()["criteria"]
    names = {m["model_label"]: m.get("display_name") for m in config.enabled_models()}

    out = [
        f"# {question_id} — {q['title']} · 응답 모음",
        "",
        "> 채점용으로 원본 기록에서 뽑아낸 것이다. 생성물이므로 직접 고치지 않는다.",
        f"> 점수는 [eval-results.md](../../docs/eval-results.md) 의 `## {question_id} / Model X / Run N` 블록에 적는다.",
        "",
        "**채점 대상:** "
        + ", ".join(m.get("display_name") or m["model_label"] for m in config.primary_models()),
        "",
        f"**구분:** {q['category']} / {q['case_type']} 사례 / 난이도 {q['difficulty']}"
        f" / Cloud 비교 {'Yes' if q.get('cloud_compare') else 'No'}",
        "",
        "## 질문",
        "",
        f"> {q['prompt']}",
        "",
        f"**평가 목적:** {q.get('purpose', '')}",
        "",
        "**이 질문의 평가 기준**",
        "",
    ]
    for code in q["criteria_codes"]:
        out.append(f"- `{code}` {crit.get(code, '')}")

    out += ["", "**기대 결과 / 확인 항목**", ""]
    out += [f"- {x}" for x in q.get("expected_points", [])]
    out += ["", "**감점 요소**", ""]
    out += [f"- {x}" for x in q.get("penalty_points", [])]

    rows = _runs_for(question_id)
    if not rows:
        out += ["", "---", "", "_아직 이 질문의 실행 기록이 없습니다._"]
        return "\n".join(out)

    shown_extra_header = False
    for r in rows:
        label = r["model_label"]
        if not config.is_primary(label) and not shown_extra_header:
            shown_extra_header = True
            out += [
                "",
                "---",
                "",
                "# 여기부터 부가 테스트",
                "",
                "> 채점하지 않아도 된다. 같은 조건으로 돌린 기록을 참고용으로 남긴 것이다.",
            ]
        out += [
            "",
            "---",
            "",
            f"## {label}_{question_id}_r{r['repeat']} — {names.get(label) or label} / Run {r['repeat']}",
            "",
        ]

        if r["status"] != config.STATUS_SUCCESS:
            out += [
                f"**호출 실패** — `{r['error_type']}`",
                "",
                "```",
                (r["error_message"] or "")[:500],
                "```",
                "",
                "> 채점 대상이 아니다. eval-results.md 의 `상태` 줄에 실패를 적고 점수는 비워 둔다.",
            ]
            continue

        def num(value, fmt):
            """값이 없으면 0 이 아니라 '측정 안 됨' 으로 적는다."""
            return fmt.format(value) if value is not None else "측정 안 됨"

        out += [
            f"- 출력 {num(r['eval_count'], '{:.0f}토큰')}"
            f" / {num(r['elapsed_sec'], '{:.1f}초')}"
            f" / {num(r['tokens_per_sec'], '{:.1f} t/s')}"
            f" / 종료 `{r.get('done_reason')}`"
            f" / 응답 {len(r.get('response_text') or '')}자",
        ]
        if r.get("done_reason") == "length":
            out.append("- **출력 한도에서 잘림** (`done_reason=length`) — '내용 부족'과 구분해서 채점")
        missing = [k for k in ("eval_count", "tokens_per_sec") if r.get(k) is None]
        if missing:
            out.append(
                f"- **응답에 통계 필드가 없어 {', '.join(missing)} 를 측정하지 못함** "
                "— 이 회차는 해당 지표의 평균과 n 에서 빠진다"
            )
        out += ["", "```text", (r["response_text"] or "").rstrip(), "```"]

    return "\n".join(out)


def write_all() -> list[str]:
    """질문마다 파일 하나씩."""
    out_dir = config.DERIVED_DIR / "responses"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for q in config.load_questions()["questions"]:
        qid = q["question_id"]
        path = out_dir / f"{qid}.md"
        path.write_text(render(qid) + "\n", encoding="utf-8")
        written.append(str(path))
    return written

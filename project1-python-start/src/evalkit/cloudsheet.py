"""STEP 7 전용 면 — Local vs Cloud 비교 (docs/cloud-compare.md).

STEP 6 채점표(eval-results.md)와 섞지 않는다. 대상도 회차도 다르다.

    STEP 6   로컬 C·D·F × 10문항 × 2회   -> eval-results.md (60블록)
    STEP 7   Cloud × 공통 5문항 × 1회     -> 이 파일 (5블록)

한 파일 안에서 문항마다 이렇게 놓는다.

    질문 / 평가 기준
    로컬 3종 응답 요약 + 이미 매긴 점수   (읽기 전용, STEP 6 에서 가져온다)
    Cloud 응답 전문
    Cloud 채점 블록                      (여기에 직접 적는다)

로컬 점수는 Run 1·Run 2 **평균**을 쓴다. 회차 중 좋은 쪽만 고르지 않는다 —
발제가 금지하는 비교 방식이다.

Cloud 채점 블록은 run_id 로 보존되므로 여러 번 생성해도 안전하다.
"""

from __future__ import annotations

import re
from typing import Any

from . import config, recorder, scoresheet

BLOCK_RE = scoresheet.BLOCK_RE

HEADER = """# Local vs Cloud 비교 (STEP 7)

> 질문 세트·평가 기준 원본: [steps/step05.md](steps/step05.md)
> 로컬 채점 원본: [eval-results.md](eval-results.md)
> 연결 산출물: [deliverables.md](deliverables.md) → `4. Local LLM vs Cloud API 비교`

## 이 파일의 역할

**Cloud 응답을 로컬과 같은 기준으로 채점하는 곳이다.** 아래 Cloud 블록에만 직접 적는다.
로컬 점수는 STEP 6 에서 이미 매긴 값을 가져다 보여주는 것이므로 고치지 않는다
(고칠 곳은 언제나 [eval-results.md](eval-results.md) 다).

| | 로컬 C·D·F | Cloud |
|---|---|---|
| 대상 문항 | 10개 전부 | **공통 5문항만** |
| 반복 | 질문당 2회 | 질문당 **1회** |
| 채점 위치 | eval-results.md | **이 파일** |

> **반복 수가 다르다.** 로컬 값은 Run 1·Run 2 평균이며,
> 회차 중 좋은 쪽만 골라 Cloud 와 비교하지 않는다.

## 채점 방법

블록 제목이 곧 실행 기록의 `run_id` 다 — `## Q01 / Model CLOUD / Run 1` → `CLOUD_Q01_r1`.
점수는 1~5 정수, 근거는 응답의 특정 부분을 가리킨다.
기준 정의는 [steps/step05.md](steps/step05.md) `1. 공통 평가 기준`.

채운 뒤 `uv run python 11_finish.py` 로 집계한다.

> **이 파일의 문항 구간은 생성물이다.** `13_cloud.py` 또는 `12_read.py` 가 다시 만든다.
> 적어 둔 점수는 `run_id` 로 찾아 그대로 옮기므로 여러 번 실행해도 안전하다.
"""


def _local_scores(question_id: str) -> dict[str, float | None]:
    """그 질문의 로컬 모델별 Run 1·Run 2 평균. STEP 6 채점 결과에서 가져온다."""
    from . import scoring

    out: dict[str, float | None] = {}
    for m in config.primary_models():
        label = m["model_label"]
        vals = [
            r["average"]
            for r in scoring.parse()
            if r["question_id"] == question_id
            and r["model_label"] == label
            and r["average"] is not None
        ]
        out[label] = sum(vals) / len(vals) if vals else None
    return out


def _cloud_runs(question_id: str) -> list[dict[str, Any]]:
    return [
        r
        for r in recorder.iter_records(config.CLOUD_RUNS_PATH)
        if r.get("question_id") == question_id and r.get("phase") == config.PHASE_MAIN
    ]


def render_question(q: dict[str, Any], criteria: dict[str, str], detail: dict[str, str]) -> list[str]:
    qid = q["question_id"]
    names = {m["model_label"]: m.get("display_name") or m["model_label"]
             for m in config.primary_models()}

    out = [
        "---",
        "",
        f"# {qid} — {q['title']}",
        "",
        f"**구분:** {scoresheet.CATEGORY_LABEL.get(q['category'], q['category'])}"
        f" / {q['case_type']} 사례 / 난이도 {q['difficulty']}",
        "",
        "**질문**",
        "",
        f"> {q['prompt']}",
        "",
        "**평가 기준** — 로컬과 같은 기준을 적용한다 (1~5점)",
        "",
        "| 코드 | 기준 | 무엇을 보는가 |",
        "|---|---|---|",
    ]
    for c in q["criteria_codes"]:
        out.append(f"| {c} | {criteria[c]} | {detail.get(c, '')} |")

    out += ["", "**기대 결과 / 확인 항목**", ""]
    out += [f"- {x}" for x in q.get("expected_points", [])]
    out += ["", "**감점 요소**", ""]
    out += [f"- {x}" for x in q.get("penalty_points", [])]

    # 로컬 결과 (읽기 전용)
    local = _local_scores(qid)
    out += [
        "",
        "## 로컬 결과 (STEP 6 에서 가져옴 — 고치지 않는다)",
        "",
        "| 모델 | Run 1·2 평균 |",
        "|---|---|",
    ]
    for label, avg in local.items():
        out.append(f"| {names[label]} | {'미채점' if avg is None else f'{avg:.2f}'} |")
    out += [
        "",
        f"> 응답 전문은 `data/derived/responses/{qid}.md` 에 있다.",
    ]

    # Cloud 응답 + 채점 블록
    runs = _cloud_runs(qid)
    out += ["", "## Cloud 응답", ""]
    if not runs:
        out += ["_아직 실행 기록이 없습니다. `13_cloud.py` 를 실행하세요._", ""]
    for r in runs:
        if r.get("status") != config.STATUS_SUCCESS:
            out += [
                f"**호출 실패** — `{r.get('error_type')}`",
                "",
                "```",
                (r.get("error_message") or "")[:500],
                "```",
                "",
                "> 채점 대상이 아니다. 아래 `상태` 줄에 실패를 적고 점수는 비워 둔다.",
                "",
            ]
            continue

        def num(v, fmt):
            return fmt.format(v) if v is not None else "측정 안 됨"

        cost = r.get("estimated_cost")
        cost_txt = (
            f"{cost:.6f} {r.get('price_currency') or ''}" if cost is not None else "측정 안 됨"
        )
        out += [
            f"- 입력 {num(r.get('input_tokens'), '{:.0f}토큰')}"
            f" / 출력 {num(r.get('output_tokens'), '{:.0f}토큰')}"
            f" / {num(r.get('elapsed_sec'), '{:.1f}초')}"
            f" / 상태 `{r.get('api_status')}`"
            f" / 응답 {len(r.get('response_text') or '')}자",
            f"- 추정 비용 {cost_txt} — 토큰 × 단가이며 **실제 청구액이 아니다**",
            "",
            "```text",
            (r.get("response_text") or "").rstrip(),
            "```",
        ]
    out.append("")
    return out


def render_block(q: dict[str, Any], criteria: dict[str, str], kept: dict[str, list[str]]) -> list[str]:
    qid = q["question_id"]
    label = (config.load_models().get("cloud_model") or {}).get("model_label") or "CLOUD"
    run_id = f"{label}_{qid}_r1"
    out = [f"## {qid} / Model {label} / Run 1", ""]
    body = kept.get(run_id)
    out += scoresheet._ensure_fields(body) or scoresheet.blank_block(q, criteria)
    return out


def build(text: str | None = None) -> str:
    """파일 전체를 다시 만든다. 적어 둔 Cloud 점수는 run_id 로 보존한다."""
    kept = scoresheet._existing_blocks(text) if text else {}

    questions = config.load_questions()
    criteria = questions["criteria"]
    detail = questions.get("criteria_detail") or {}
    targets = set(config.cloud_question_ids())

    body: list[str] = []
    for q in questions["questions"]:
        if q["question_id"] not in targets:
            continue
        body += render_question(q, criteria, detail)
        body += render_block(q, criteria, kept)

    return HEADER + "\n" + "\n".join(body).rstrip("\n") + "\n"


def sync() -> str:
    path = config.CLOUD_COMPARE_PATH
    before = path.read_text(encoding="utf-8") if path.exists() else None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(before), encoding="utf-8")

    n = len(config.cloud_question_ids())
    runs = len(list(recorder.iter_records(config.CLOUD_RUNS_PATH)))
    return f"{path.name}: 공통 {n}문항 — Cloud 실행 기록 {runs}건"

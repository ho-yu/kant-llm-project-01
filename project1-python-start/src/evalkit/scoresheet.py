"""채점 입력면(eval-results.md)의 질문 구간을 만들어 낸다.

질문·기준·기대 결과는 questions.json 에서, 채점할 모델은 models.json 의
tier 에서 온다. 두 곳만 고치면 채점표가 따라온다 — 손으로 열을 맞추다
어긋나는 일을 없애려는 것이다.

파일 앞머리(채점 방법·실행 환경·모델 목록 등 직접 쓴 설명)는 건드리지 않는다.
첫 질문 구간부터 끝까지만 다시 만든다.

이미 적어 둔 점수는 run_id 로 찾아서 그대로 옮긴다. 다시 실행해도 안전하다.
"""

from __future__ import annotations

import re
from typing import Any

from . import config

#: 이 줄부터 파일 끝까지가 생성 구간이다.
SECTION_START = re.compile(r"^# (Q\d+) — ")

BLOCK_RE = re.compile(r"^## (Q\d+) / Model ([A-Z]) / Run (\d+)\s*$")

#: 화면에 보일 때만 붙이는 우리말 풀이. 집계 키는 questions.json 의 category 다.
CATEGORY_LABEL = {
    "Customer Support": "Customer Support (고객 문의)",
    "Seller Support": "Seller Support (셀러 업무)",
}


def _existing_blocks(text: str) -> dict[str, list[str]]:
    """이미 적어 둔 블록 본문을 run_id 별로 모은다.

    본문은 제목 다음 줄부터 다음 제목 직전까지다.
    """
    out: dict[str, list[str]] = {}
    lines = text.split("\n")
    cur: str | None = None
    buf: list[str] = []
    fence = False

    for line in lines:
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence:
            m = BLOCK_RE.match(line)
            if m:
                if cur:
                    out[cur] = buf
                cur, buf = f"{m.group(2)}_{m.group(1)}_r{m.group(3)}", []
                continue
            if line.startswith("# ") or line.startswith("## "):
                if cur:
                    out[cur] = buf
                cur, buf = None, []
                continue
        if cur is not None:
            buf.append(line)

    if cur:
        out[cur] = buf
    return {k: _trim(v) for k, v in out.items()}


def _trim(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def blank_block(question: dict[str, Any], criteria: dict[str, str]) -> list[str]:
    """빈 채점 양식. 그 질문의 평가 기준만 넣는다."""
    out = ["원본 기록 ID:", "상태: 성공 / 오류", ""]
    for code in question["criteria_codes"]:
        out += [f"{criteria[code]}:", "근거:", "", ""]
    out.append("평균:")
    return out


def render_question(question: dict[str, Any], criteria: dict[str, str]) -> list[str]:
    qid = question["question_id"]
    models = config.primary_models()

    out = [
        "---",
        "",
        f"# {qid} — {question['title']}",
        "",
        f"**구분:** {CATEGORY_LABEL.get(question['category'], question['category'])}"
        f" / {question['case_type']} 사례"
        f" / 난이도 {question['difficulty']}"
        f" / Cloud 비교 {'Yes' if question.get('cloud_compare') else 'No'}",
        "",
        "**질문**",
        "",
        f"> {question['prompt']}",
        "",
        f"**평가 목적:** {question.get('purpose', '')}",
        "",
        "**평가 기준:** "
        + ", ".join(f"{c}. {criteria[c]}" for c in question["criteria_codes"]),
        "",
        "**기대 결과 / 확인 항목**",
        "",
    ]
    out += [f"- {x}" for x in question.get("expected_points", [])]
    out += ["", "**감점 요소**", ""]
    out += [f"- {x}" for x in question.get("penalty_points", [])]
    out.append("")
    return out


def render_aggregate(question: dict[str, Any], criteria: dict[str, str]) -> list[str]:
    """질문별 집계표. 채점 대상 모델만 행으로 둔다."""
    qid = question["question_id"]
    names = [criteria[c] for c in question["criteria_codes"]]
    header = ["모델"] + names + ["평균", "n", "성공/시도", "비고"]
    repeats = config.load_run_settings()["repeats"]

    out = [
        f"## {qid} 집계",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
    ]
    for m in config.primary_models():
        cells = [m.get("display_name") or m["model_label"]]
        cells += [""] * (len(names) + 2)
        cells += [f"/{repeats}", ""]
        out.append("| " + " | ".join(cells) + " |")
    out += ["", f"**{qid} 관찰 메모**", "", ""]
    return out


def build(text: str, *, preserve: bool = True) -> str:
    """파일 전체를 다시 만든다. 앞머리는 그대로 두고 질문 구간만 교체한다."""
    lines = text.split("\n")

    start = None
    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence and SECTION_START.match(line):
            start = i
            break
    if start is None:
        raise SystemExit("질문 구간(`# Q01 — ...`)을 찾지 못했습니다.")

    # 질문 구간 바로 앞의 "---" 구분선까지 잘라낸다
    head_end = start
    while head_end > 0 and not lines[head_end - 1].strip():
        head_end -= 1
    if head_end > 0 and lines[head_end - 1].strip() == "---":
        head_end -= 1

    kept = _existing_blocks(text) if preserve else {}

    questions = config.load_questions()
    criteria = questions["criteria"]
    repeats = config.load_run_settings()["repeats"]

    body: list[str] = []
    for q in questions["questions"]:
        qid = q["question_id"]
        body += render_question(q, criteria)
        for m in config.primary_models():
            label = m["model_label"]
            for rep in range(1, repeats + 1):
                run_id = f"{label}_{qid}_r{rep}"
                body += [f"## {qid} / Model {label} / Run {rep}", ""]
                body += kept.get(run_id) or blank_block(q, criteria)
                body.append("")
        body += render_aggregate(q, criteria)

    return "\n".join(lines[:head_end] + [""] + body).rstrip("\n") + "\n"


def sync(*, preserve: bool = True) -> str:
    path = config.EVAL_RESULTS_PATH
    before = path.read_text(encoding="utf-8")
    path.write_text(build(before, preserve=preserve), encoding="utf-8")

    labels = ", ".join(m["model_label"] for m in config.primary_models())
    total = config.expected_scored_block_count()
    how = "기존 점수 유지" if preserve else "점수 초기화"
    return f"{path.name}: 채점 대상 {labels} — 블록 {total}개 ({how})"

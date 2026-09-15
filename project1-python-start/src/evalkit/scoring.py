"""docs/eval-results.md 를 채점 입력면으로 읽는다.

채점은 이 파일 한 곳에서만 한다. 블록 제목이 곧 run_id 이므로
사람이 run_id 를 따로 적을 필요가 없다.

    ## Q01 / Model B / Run 1     ->  run_id = B_Q01_r1

    답변 적합성: 4
    근거: 주문 상태 확인을 먼저 제안했으나 배송사 문의 순서가 불명확

    평균: 4.3

점수를 비워 두면 미채점으로 본다. 0 과 구분한다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import config

#: eval-results.md 의 기준 표기 -> questions.json 의 기준 코드
CRITERION_CODE = {
    "답변 적합성": "A",
    "논리성/실용성": "B",
    "논리성 / 실용성": "B",
    "한국어 표현": "C",
    "지시사항 준수": "D",
    "불확실성 대응": "E",
    "정보 부족 / 불확실성 대응": "E",
}

BLOCK_RE = re.compile(r"^##\s+(Q\d+)\s*/\s*Model\s+([A-Z])\s*/\s*Run\s+(\d+)\s*$")
FIELD_RE = re.compile(r"^([^:]+?)\s*:\s*(.*)$")

#: 템플릿이 비워 둔 채로 남긴 자리표시자. 채워진 값으로 보지 않는다.
PLACEHOLDERS = {"", "성공 / 오류", "-"}


def _num(raw: str) -> float | None:
    raw = raw.strip()
    if raw in PLACEHOLDERS:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse(path: Path | None = None) -> list[dict[str, Any]]:
    """블록을 읽어 채점 레코드 목록으로 돌려준다."""
    path = path or config.EVAL_RESULTS_PATH
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    records: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    pending_code: str | None = None  # 방금 점수를 읽은 기준 — 다음 "근거:" 가 여기 붙는다

    for line in lines:
        header = BLOCK_RE.match(line)
        if header:
            qid, label, rep = header.group(1), header.group(2), int(header.group(3))
            cur = {
                "run_id": f"{label}_{qid}_r{rep}",
                "question_id": qid,
                "model_label": label,
                "repeat": rep,
                "scores": {},
                "rationales": {},
                "average": None,
                "status_note": None,
                "source": f"{path.name}:{qid}/{label}/r{rep}",
            }
            records.append(cur)
            pending_code = None
            continue

        if cur is None:
            continue
        if line.startswith("## ") or line.startswith("# "):
            cur = None
            continue

        field = FIELD_RE.match(line)
        if not field:
            # "근거:" 다음 줄들 — 여러 줄이면 이어 붙인다
            if pending_code and line.strip():
                prev = cur["rationales"].get(pending_code) or ""
                cur["rationales"][pending_code] = (prev + " " + line.strip()).strip()
            continue

        name, value = field.group(1).strip(), field.group(2).strip()

        if name == "근거":
            if pending_code:
                cur["rationales"][pending_code] = value or cur["rationales"].get(pending_code)
            continue

        if name == "평균":
            cur["average"] = _num(value)
            pending_code = None
            continue

        if name == "상태":
            cur["status_note"] = None if value in PLACEHOLDERS else value
            pending_code = None
            continue

        code = CRITERION_CODE.get(name)
        if code:
            cur["scores"][code] = _num(value)
            cur["rationales"].setdefault(code, None)
            pending_code = code
            continue

        # "원본 기록 ID" 등 그 밖의 줄은 무시한다 (run_id 는 제목에서 만든다)
        pending_code = None

    return records


def scored_only(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """점수가 하나라도 채워진 블록만."""
    records = records if records is not None else parse()
    return [r for r in records if any(v is not None for v in r["scores"].values())]


def summary() -> str:
    records = parse()
    scored = scored_only(records)
    by_model: dict[str, int] = {}
    for r in scored:
        by_model[r["model_label"]] = by_model.get(r["model_label"], 0) + 1
    detail = ", ".join(f"{k} {v}건" for k, v in sorted(by_model.items())) or "없음"
    return f"블록 {len(records)}개 중 채점됨 {len(scored)}개 ({detail})"

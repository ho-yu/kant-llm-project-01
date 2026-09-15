"""경로 상수와 설정 로더.

값 자체(temperature 등)는 이 파일에 하드코딩하지 않는다.
data/config/*.json 을 단일 출처로 두고 여기서는 읽기만 한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- 경로

# 이 파일: <repo>/project1-python-start/src/evalkit/config.py
REPO_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"

CONFIG_DIR = DATA_DIR / "config"
ENV_DIR = DATA_DIR / "env"
RAW_DIR = DATA_DIR / "raw"
DERIVED_DIR = DATA_DIR / "derived"
TABLES_DIR = DERIVED_DIR / "tables"

# 1회 작성 후 고정
RUN_SETTINGS_PATH = CONFIG_DIR / "run_settings.json"
MODELS_PATH = CONFIG_DIR / "models.json"
QUESTIONS_PATH = CONFIG_DIR / "questions.json"
ENVIRONMENT_PATH = ENV_DIR / "environment.json"

# 품질 채점 입력면 — 사람이 직접 채운다
EVAL_RESULTS_PATH = DOCS_DIR / "eval-results.md"

# append 전용 — 절대 "w" 로 열지 않는다
LOCAL_RUNS_PATH = RAW_DIR / "local" / "runs.jsonl"
CLOUD_RUNS_PATH = RAW_DIR / "cloud" / "runs.jsonl"

# 생성물 — 언제든 재생성 가능
STEP04_PATH = DERIVED_DIR / "step04.md"
STEP06_PATH = DERIVED_DIR / "step06.md"

LOCAL_SUMMARY_PATH = DERIVED_DIR / "local_summary.json"
CLOUD_SUMMARY_PATH = DERIVED_DIR / "cloud_summary.json"

APPEND_ONLY_PATHS = (LOCAL_RUNS_PATH, CLOUD_RUNS_PATH)

# ---------------------------------------------------------------- 실험 단계

PHASE_WARMUP = "warmup"
PHASE_MAIN = "main"
PHASE_RETRY = "retry"
PHASE_EXTRA = "extra"

ALL_PHASES = (PHASE_WARMUP, PHASE_MAIN, PHASE_RETRY, PHASE_EXTRA)

#: 기본 비교표에 들어가는 단계. 워밍업·재시도·추가 실험은 제외한다.
AGGREGATED_PHASES = (PHASE_MAIN,)

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# ---------------------------------------------------------------- 로더


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _strip_comments(value: Any) -> Any:
    """설명용 "_" 키를 제거한다.

    JSON 에는 주석을 달 수 없어 "_comment" 같은 키로 설명을 적어두는데,
    그대로 Ollama 에 넘기면 알 수 없는 옵션이 섞인다.
    """
    if isinstance(value, dict):
        return {k: _strip_comments(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [_strip_comments(v) for v in value]
    return value


def load_run_settings() -> dict[str, Any]:
    return _load_json(RUN_SETTINGS_PATH)


def chat_options() -> dict[str, Any]:
    """client.chat(options=...) 에 넘길 값.

    설명용 키를 걷어내고, 값이 정해지지 않은(None) 항목도 뺀다.
    None 을 그대로 넘기면 Ollama 가 기본값 대신 None 을 해석하려 한다.
    기록에는 여기서 만든 딕셔너리가 그대로 남으므로, 실제로 넘긴 값과
    기록이 항상 일치한다.
    """
    raw = _strip_comments(load_run_settings().get("options") or {})
    return {k: v for k, v in raw.items() if v is not None}


def load_models() -> dict[str, Any]:
    return _load_json(MODELS_PATH)


def load_questions() -> dict[str, Any]:
    return _load_json(QUESTIONS_PATH)


def load_environment() -> dict[str, Any]:
    return _load_json(ENVIRONMENT_PATH)


def enabled_models() -> list[dict[str, Any]]:
    """본 실험 대상 모델만. models.json 에 적힌 순서를 유지한다."""
    return [m for m in load_models()["models"] if m.get("enabled")]


def question_map() -> dict[str, dict[str, Any]]:
    return {q["question_id"]: q for q in load_questions()["questions"]}


def cloud_question_ids() -> list[str]:
    """cloud_compare=true 인 질문. 결과를 보기 전에 확정되어 있어야 한다."""
    return [q["question_id"] for q in load_questions()["questions"] if q.get("cloud_compare")]


def expected_main_run_count() -> int:
    settings = load_run_settings()
    return len(enabled_models()) * len(load_questions()["questions"]) * settings["repeats"]


# ---------------------------------------------------------------- run_id

def make_run_id(
    model_label: str,
    question_id: str | None = None,
    repeat: int | None = None,
    phase: str = PHASE_MAIN,
    attempt: int | None = None,
) -> str:
    """run_id 는 전 파일에서 유일하다. 재시도는 원본과 다른 id 를 받으므로
    원래 실패 기록을 덮어쓸 수 없다.

    main   : B_Q01_r1
    warmup : B_warmup
    retry  : B_Q01_r1_retry1
    extra  : B_Q01_r1_extra1
    """
    if phase == PHASE_WARMUP:
        return f"{model_label}_warmup"

    if question_id is None or repeat is None:
        raise ValueError(f"phase={phase} 에는 question_id 와 repeat 이 필요합니다.")

    base = f"{model_label}_{question_id}_r{repeat}"
    if phase == PHASE_MAIN:
        return base
    if phase in (PHASE_RETRY, PHASE_EXTRA):
        if attempt is None:
            raise ValueError(f"phase={phase} 에는 attempt 가 필요합니다.")
        return f"{base}_{phase}{attempt}"

    raise ValueError(f"알 수 없는 phase: {phase}")

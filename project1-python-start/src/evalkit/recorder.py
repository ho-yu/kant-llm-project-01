"""레코드 생성 / append 저장 / 중복 run_id 검사.

이 모듈을 거치지 않고 JSONL 을 직접 쓰지 않는다.
여기서만 파일을 열고, 항상 "a" 모드를 쓴다.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from . import config, schema


# ---------------------------------------------------------------- 공통


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def iter_records(path: Path) -> Iterator[dict[str, Any]]:
    """JSONL 을 한 줄씩 읽는다. 파일이 없으면 아무것도 내지 않는다."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 파싱 실패: {e}") from None


def load_run_ids(path: Path) -> set[str]:
    return {r.get("run_id") for r in iter_records(path) if r.get("run_id")}


def append_record(path: Path, record: dict[str, Any]) -> None:
    """append 전용 저장.

    - 항상 "a" 모드. 기존 기록을 덮어쓸 수 있는 경로가 없다.
    - 한 줄 = 한 레코드. ensure_ascii=False 로 한국어를 그대로 남긴다.
    """
    if path not in config.APPEND_ONLY_PATHS:
        raise ValueError(f"append 대상이 아닌 경로입니다: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    if "\n" in line:
        raise ValueError("레코드 직렬화 결과에 개행이 포함되었습니다.")

    with path.open("a", encoding="utf-8") as f:  # "w" 금지
        f.write(line + "\n")


class RunLog:
    """한 파일에 대한 append 세션. 이미 있는 run_id 는 건너뛴다."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._seen = load_run_ids(path)
        self.skipped: list[str] = []
        self.written: list[str] = []

    def has(self, run_id: str) -> bool:
        return run_id in self._seen

    def append(self, record: dict[str, Any]) -> bool:
        """저장했으면 True, 중복이라 건너뛰었으면 False."""
        run_id = record["run_id"]
        if run_id in self._seen:
            warnings.warn(f"run_id 중복으로 건너뜁니다: {run_id}", stacklevel=2)
            self.skipped.append(run_id)
            return False

        append_record(self.path, record)
        self._seen.add(run_id)
        self.written.append(run_id)
        return True

    def summary(self) -> str:
        return f"{self.path.name}: 저장 {len(self.written)}건, 중복 건너뜀 {len(self.skipped)}건"


# ---------------------------------------------------------------- 레코드 생성


def _note_missing(record: dict[str, Any], field: str, reason: str) -> None:
    """지표를 못 구했을 때. 값은 None 그대로 두고 사유만 남긴다."""
    record[field] = None
    record["measurement_notes"][field] = reason


def new_local_record(
    *,
    run_id: str,
    phase: str,
    model_label: str,
    model_tag: str,
    prompt: str,
    options: dict[str, Any],
    settings_version: str,
    questions_version: str,
    question_id: str | None = None,
    repeat: int | None = None,
    system_prompt: str | None = None,
    retry_of_run_id: str | None = None,
) -> dict[str, Any]:
    """호출 직전에 만드는 빈 레코드. 측정값은 전부 None 으로 시작한다."""
    rec = schema.blank_record(schema.LOCAL_RUN_FIELDS)
    rec.update(
        run_id=run_id,
        phase=phase,
        question_id=question_id,
        repeat=repeat,
        is_warmup=(phase == config.PHASE_WARMUP),
        timestamp=now_iso(),
        retry_of_run_id=retry_of_run_id,
        model_label=model_label,
        model_tag=model_tag,
        settings_version=settings_version,
        questions_version=questions_version,
        options=dict(options),
        system_prompt=system_prompt,
        prompt=prompt,
    )
    return rec


def new_cloud_record(
    *,
    run_id: str,
    phase: str,
    model_label: str,
    model_id: str,
    question_id: str,
    repeat: int,
    prompt: str,
    options: dict[str, Any],
    settings_version: str,
    questions_version: str,
    retry_of_run_id: str | None = None,
) -> dict[str, Any]:
    rec = schema.blank_record(schema.CLOUD_RUN_FIELDS)
    rec.update(
        run_id=run_id,
        phase=phase,
        question_id=question_id,
        repeat=repeat,
        is_warmup=False,
        timestamp=now_iso(),
        retry_of_run_id=retry_of_run_id,
        model_label=model_label,
        model_id=model_id,
        settings_version=settings_version,
        questions_version=questions_version,
        options=dict(options),
        prompt=prompt,
    )
    return rec


def new_score_record(
    *,
    run_id: str,
    source_file: str,
    question_id: str,
    model_label: str,
    criteria_codes: list[str],
) -> dict[str, Any]:
    """빈 채점 레코드. 점수는 전부 None 으로 시작한다."""
    rec = schema.blank_record(schema.SCORE_FIELDS)
    rec.update(
        run_id=run_id,
        source_file=source_file,
        question_id=question_id,
        model_label=model_label,
        scores={code: None for code in criteria_codes},
        rationales={code: None for code in criteria_codes},
        scored_at=now_iso(),
        reviewed=False,
    )
    return rec


# ---------------------------------------------------------------- 응답 -> 레코드


def fill_from_ollama_response(
    record: dict[str, Any],
    response: Any,
    elapsed_sec: float,
) -> dict[str, Any]:
    """Ollama 응답에서 측정값을 채운다.

    규칙
      - 통계 필드가 없으면 0 이 아니라 None + measurement_notes 에 사유.
      - eval_duration <= 0 이면 tokens_per_sec 를 계산하지 않는다.
      - 나노초는 1e9 로 나눠 초로 기록한다.
    """
    record["status"] = config.STATUS_SUCCESS
    record["elapsed_sec"] = elapsed_sec

    content = getattr(getattr(response, "message", None), "content", None)
    if content is None:
        _note_missing(record, "response_text", "응답 객체에 message.content 없음")
    else:
        record["response_text"] = content  # 가공 없이 그대로

    load_duration = getattr(response, "load_duration", None)
    if load_duration is None:
        _note_missing(record, "load_duration_sec", "응답에 load_duration 없음")
    else:
        record["load_duration_sec"] = load_duration / 1_000_000_000

    eval_count = getattr(response, "eval_count", None)
    if eval_count is None:
        _note_missing(record, "eval_count", "응답에 eval_count 없음")
    else:
        record["eval_count"] = eval_count

    eval_duration = getattr(response, "eval_duration", None)
    if eval_duration is None:
        _note_missing(record, "eval_duration_sec", "응답에 eval_duration 없음")
    else:
        record["eval_duration_sec"] = eval_duration / 1_000_000_000

    # tokens_per_sec 는 두 값이 모두 있고 eval_duration > 0 일 때만.
    if eval_count is None or eval_duration is None:
        _note_missing(record, "tokens_per_sec", "eval_count 또는 eval_duration 없음")
    elif eval_duration <= 0:
        _note_missing(record, "tokens_per_sec", "eval_duration <= 0 이라 계산하지 않음")
    else:
        record["tokens_per_sec"] = eval_count / (eval_duration / 1_000_000_000)

    prompt_eval_count = getattr(response, "prompt_eval_count", None)
    if prompt_eval_count is None:
        _note_missing(record, "prompt_eval_count", "응답에 prompt_eval_count 없음")
    else:
        record["prompt_eval_count"] = prompt_eval_count

    prompt_eval_duration = getattr(response, "prompt_eval_duration", None)
    if prompt_eval_duration is None:
        _note_missing(record, "prompt_eval_duration_sec", "응답에 prompt_eval_duration 없음")
    else:
        record["prompt_eval_duration_sec"] = prompt_eval_duration / 1_000_000_000

    total_duration = getattr(response, "total_duration", None)
    if total_duration is None:
        _note_missing(record, "total_duration_sec", "응답에 total_duration 없음")
    else:
        record["total_duration_sec"] = total_duration / 1_000_000_000

    # done_reason="length" 면 num_predict 한도에서 잘린 답변이다.
    # 품질 채점 시 "내용이 부족한 것"과 "잘린 것"을 구분하는 근거가 된다.
    done_reason = getattr(response, "done_reason", None)
    if done_reason is None:
        _note_missing(record, "done_reason", "응답에 done_reason 없음")
    else:
        record["done_reason"] = done_reason

    return record


def compute_processor(size: int | None, size_vram: int | None) -> str | None:
    """`ollama ps` 의 PROCESSOR 열과 같은 방식으로 CPU/GPU 적재 상태를 만든다.

    GPU 이용률이나 VRAM 용량이 아니라, 모델 가중치가 어디에 올라가 있는지다.
    """
    if size is None or size_vram is None:
        return None
    if size_vram == 0:
        return "100% CPU"
    if size_vram == size:
        return "100% GPU"
    if size_vram > size or size == 0:
        return "Unknown"
    cpu_percent = round((size - size_vram) / size * 100)
    return f"{cpu_percent}%/{100 - cpu_percent}% CPU/GPU"


def fill_from_ps(
    record: dict[str, Any],
    ps_entries: list[Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    """client.ps().models 에서 VRAM/적재 상태/식별값을 채운다.

    응답을 받은 직후, 모델이 언로드되기 전에 조회한 결과를 넘겨야 한다.
    size_vram 은 그 시점의 값이며 최대 VRAM 이 아니다.

    실측으로 확인한 ps 항목 구조:
        model / name / digest / expires_at / size / size_vram
        details.quantization_level / details.parameter_size
        context_length
    """
    observed_at = observed_at or now_iso()
    target_tag = record["model_tag"]

    match = None
    for entry in ps_entries or []:
        if getattr(entry, "model", None) == target_tag or getattr(entry, "name", None) == target_tag:
            match = entry
            break

    if match is None:
        for field in ("size_vram_mib", "size_total_mib", "processor", "vram_observed_at"):
            _note_missing(record, field, "client.ps() 에 해당 모델 없음 (이미 언로드되었을 수 있음)")
        for field in ("digest", "quantization_level", "context_length"):
            record["measurement_notes"].setdefault(field, "client.ps() 에 해당 모델 없음")
        return record

    size = getattr(match, "size", None)
    size_vram = getattr(match, "size_vram", None)

    if size_vram is None:
        _note_missing(record, "size_vram_mib", "ps 항목에 size_vram 없음")
        _note_missing(record, "vram_observed_at", "size_vram 을 읽지 못함")
    else:
        record["size_vram_mib"] = size_vram / 1_048_576
        record["vram_observed_at"] = observed_at

    if size is None:
        _note_missing(record, "size_total_mib", "ps 항목에 size 없음")
    else:
        record["size_total_mib"] = size / 1_048_576

    processor = compute_processor(size, size_vram)
    if processor is None:
        _note_missing(record, "processor", "size 또는 size_vram 이 없어 적재 상태를 계산할 수 없음")
    else:
        record["processor"] = processor

    record["digest"] = getattr(match, "digest", None)
    if record["digest"] is None:
        record["measurement_notes"]["digest"] = "ps 항목에 digest 없음"

    record["context_length"] = getattr(match, "context_length", None)
    if record["context_length"] is None:
        record["measurement_notes"]["context_length"] = "ps 항목에 context_length 없음"

    details = getattr(match, "details", None)
    quant = getattr(details, "quantization_level", None) if details is not None else None
    record["quantization_level"] = quant
    if quant is None:
        record["measurement_notes"]["quantization_level"] = "ps details 에서 읽지 못함"
    elif str(quant).lower() == "unknown":
        # 태그에는 Q4_K_M 이라고 적혀 있어도 ps 는 unknown 을 돌려줄 수 있다.
        # 값을 덮어쓰지 않고 그대로 두되, 비교표에서 태그 기준값과 구분하도록 남긴다.
        record["measurement_notes"]["quantization_level"] = (
            "ps 가 'unknown' 으로 보고함 — 비교표에는 모델 태그 기준값을 함께 기재할 것"
        )

    return record


def fill_error(record: dict[str, Any], exc: BaseException, elapsed_sec: float | None = None) -> dict[str, Any]:
    """호출 실패. 회차를 건너뛰지 않고 이 레코드를 그대로 남긴다.

    지표는 None 으로 두고, 품질 점수와는 별개 축이다.
    """
    record["status"] = config.STATUS_ERROR
    record["error_type"] = type(exc).__name__
    record["error_message"] = str(exc)
    record["elapsed_sec"] = elapsed_sec
    if elapsed_sec is None:
        record["measurement_notes"]["elapsed_sec"] = "호출 실패로 측정 불가"

    for field in ("load_duration_sec", "eval_count", "eval_duration_sec",
                  "tokens_per_sec", "prompt_eval_count", "prompt_eval_duration_sec",
                  "total_duration_sec", "done_reason", "size_vram_mib",
                  "size_total_mib", "processor"):
        if field in record and record[field] is None:
            record["measurement_notes"].setdefault(field, "호출 실패로 측정 불가")

    return record

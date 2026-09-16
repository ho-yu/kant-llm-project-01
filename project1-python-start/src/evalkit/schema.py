"""레코드 스키마 정의.

세 축을 서로 다른 것으로 취급한다.

    1) 호출 성공 여부   -> status ("success" | "error")
    2) 지표 측정 여부   -> 각 지표 필드가 None 인지 + measurement_notes 에 사유
    3) 답변 품질        -> 이 파일이 아니라 scores.jsonl (별도 축)

status="success" 인데 지표가 None 일 수 있다(호출은 됐지만 통계를 못 읽음).
status="error" 인데 품질 점수가 없는 것은 정상이다(채점 대상이 아님).
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------- 필드 정의
# (필드명, 타입, 필수 여부, 설명)
# 필수=True 는 "키가 존재해야 한다"는 뜻이며, 값이 None 인 것은 허용된다.
# 값을 못 구했을 때 0 으로 채우지 않기 위한 구분이다.

FieldSpec = tuple[str, str, bool, str]

LOCAL_RUN_FIELDS: tuple[FieldSpec, ...] = (
    # --- 식별
    ("run_id", "str", True, "전 파일 유일. config.make_run_id() 로 생성"),
    ("phase", "str", True, "warmup | main | retry | extra"),
    ("question_id", "str|null", True, "워밍업이면 null 가능"),
    ("repeat", "int|null", True, "본 실험 회차(1..N). 워밍업이면 null"),
    ("is_warmup", "bool", True, "phase == 'warmup' 과 항상 일치해야 함"),
    ("timestamp", "str", True, "ISO8601, 요청 직전 시각"),
    ("retry_of_run_id", "str|null", True, "재시도일 때 원본 run_id. 원본은 그대로 남는다"),
    # --- 모델 식별 (실행 시점의 실제 값)
    ("model_label", "str", True, "B | C | D | E"),
    ("model_tag", "str", True, "실제 호출한 전체 태그"),
    ("digest", "str|null", True, "client.ps()/list() 응답값. 수기 입력 금지"),
    ("quantization_level", "str|null", True, "details.quantization_level"),
    ("context_length", "int|null", True, "실행 시점 실제 context. 문서상 최대값과 다름"),
    # --- 입력
    ("settings_version", "str", True, "execution_conditions.json 의 settings_version"),
    ("questions_version", "str", True, "questions.json 의 questions_version"),
    ("options", "dict", True, "client.chat(options=...) 에 실제로 넘긴 값 전체"),
    ("system_prompt", "str|null", True, "미사용이면 null"),
    ("prompt", "str", True, "실제 입력 전문"),
    # --- 출력
    ("response_text", "str|null", True, "원본 그대로. 트리밍/요약/가공 금지. 실패면 null"),
    ("status", "str", True, "success | error"),
    ("error_type", "str|null", True, "실패 시 예외 클래스명 등"),
    ("error_message", "str|null", True, "실패 시 메시지"),
    # --- 측정값 (못 구하면 None + measurement_notes 에 사유)
    ("elapsed_sec", "float|null", True, "요청 직전~응답 수신 직후. TTFT 아님"),
    ("load_duration_sec", "float|null", True, "response.load_duration / 1e9"),
    ("eval_count", "int|null", True, "response.eval_count (생성 토큰 수)"),
    ("eval_duration_sec", "float|null", True, "response.eval_duration / 1e9"),
    ("tokens_per_sec", "float|null", True, "eval_count / eval_duration_sec"),
    ("prompt_eval_count", "int|null", True, "response.prompt_eval_count (입력 토큰 수)"),
    ("prompt_eval_duration_sec", "float|null", True, "response.prompt_eval_duration / 1e9"),
    ("total_duration_sec", "float|null", True, "response.total_duration / 1e9. 서버 측 총 소요"),
    ("done_reason", "str|null", True, "stop=정상 종료 / length=num_predict 한도에서 잘림"),
    ("size_vram_mib", "float|null", True, "client.ps() size_vram / 1048576. 최대값 아님"),
    ("size_total_mib", "float|null", True, "client.ps() size / 1048576. processor 계산 근거"),
    ("vram_observed_at", "str|null", True, "size_vram 조회 시각(응답 직후, 언로드 전)"),
    ("processor", "str|null", True, "size 와 size_vram 비율로 계산한 CPU/GPU 적재 상태. GPU 이용률 아님"),
    # --- 사유
    ("measurement_notes", "dict", True, "{필드명: 사유}. 값이 null 인 지표는 여기에 사유 필수"),
)

CLOUD_RUN_FIELDS: tuple[FieldSpec, ...] = (
    ("run_id", "str", True, "CLOUD_Q01_r1 형식"),
    ("phase", "str", True, "main | retry | extra (Cloud 워밍업 없음)"),
    ("question_id", "str", True, ""),
    ("repeat", "int", True, "Cloud 는 각 1회"),
    ("is_warmup", "bool", True, "항상 false"),
    ("timestamp", "str", True, "ISO8601"),
    ("retry_of_run_id", "str|null", True, ""),
    ("model_label", "str", True, "CLOUD"),
    ("model_id", "str", True, "실제 호출한 모델 식별자"),
    ("settings_version", "str", True, ""),
    ("questions_version", "str", True, ""),
    ("options", "dict", True, "실제로 넘긴 요청 파라미터"),
    ("prompt", "str", True, ""),
    ("response_text", "str|null", True, "원본 그대로"),
    ("status", "str", True, "success | error"),
    ("api_status", "str|null", True, "API 가 돌려준 처리 상태 (예: completed)"),
    ("error_type", "str|null", True, ""),
    ("error_message", "str|null", True, ""),
    ("elapsed_sec", "float|null", True, "API 요청 전후로 측정. 네트워크 조건 포함"),
    ("input_tokens", "int|null", True, ""),
    ("output_tokens", "int|null", True, ""),
    ("price_input_per_1m_tokens", "float|null", True, "호출 시점 단가 (models.json 에서 복사)"),
    ("price_output_per_1m_tokens", "float|null", True, ""),
    ("price_currency", "str|null", True, ""),
    ("estimated_cost", "float|null", True, "사용량 x 단가로 계산한 추정치. 실제 청구액 아님"),
    ("measurement_notes", "dict", True, "{필드명: 사유}"),
)

SCORE_FIELDS: tuple[FieldSpec, ...] = (
    ("run_id", "str", True, "runs.jsonl 의 run_id 와 연결. 이것이 역추적 키"),
    ("source_file", "str", True, "local | cloud — 어느 runs.jsonl 인지"),
    ("question_id", "str", True, "원본과 일치해야 함 (validator 가 검사)"),
    ("model_label", "str", True, "원본과 일치해야 함"),
    ("scores", "dict", True, "{기준코드: 점수|null}. 해당 질문의 criteria_codes 와 일치"),
    ("rationales", "dict", True, "{기준코드: 근거}. 응답의 어느 부분인지 적는다"),
    ("average", "float|null", True, "채점자가 적거나 aggregator 가 계산. 미채점이면 null"),
    ("scored_at", "str", True, "ISO8601"),
    ("reviewed", "bool", True, "재검토 수행 여부"),
    ("reviewed_at", "str|null", True, ""),
    ("revision_reason", "str|null", True, "점수를 수정했다면 사유"),
    ("not_scored_reason", "str|null", True, "채점하지 않았다면 사유 (예: status=error)"),
)

# ---------------------------------------------------------------- 지표 목록

#: 평균과 n 을 함께 계산해야 하는 로컬 성능 지표.
LOCAL_METRIC_FIELDS = (
    "elapsed_sec",
    "load_duration_sec",
    "eval_count",
    "eval_duration_sec",
    "tokens_per_sec",
    "prompt_eval_count",
    "size_vram_mib",
)

CLOUD_METRIC_FIELDS = (
    "elapsed_sec",
    "input_tokens",
    "output_tokens",
    "estimated_cost",
)


def required_keys(fields: tuple[FieldSpec, ...]) -> list[str]:
    return [name for name, _, required, _ in fields if required]


def blank_record(fields: tuple[FieldSpec, ...]) -> dict[str, Any]:
    """모든 키가 존재하고 값은 비어 있는 레코드.

    dict 타입은 {}, 나머지는 None. 0 으로 채우지 않는다.
    """
    out: dict[str, Any] = {}
    for name, typ, _, _ in fields:
        out[name] = {} if typ == "dict" else None
    return out

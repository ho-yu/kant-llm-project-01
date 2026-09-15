"""Cloud 실험 실행 엔트리.

대상은 questions.json 에서 cloud_compare=true 인 질문뿐이다 (결과를 보기 전에 확정됨).
각 질문 1회.

API 키는 어떤 파일에도 저장하지 않는다.
실행 시점에 입력받거나 환경변수에서 읽고, 레코드에는 담지 않는다.
"""

from __future__ import annotations

import argparse
from typing import Any

from . import config, recorder


def get_api_key() -> str:
    """API 키를 가져온다. 레코드·설정 파일 어디에도 남기지 않는다.

    환경변수 OPENAI_API_KEY 가 있으면 쓰고, 없으면 실행 시점에 입력받는다.
    입력값은 화면에 표시되지 않고 파일로 저장되지 않는다.
    """
    import os
    from getpass import getpass

    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if key:
        print("  API 키: 환경변수 OPENAI_API_KEY 사용")
        return key

    key = getpass("  API 키를 붙여넣고 Enter (화면에 보이지 않음): ").strip()
    if not key:
        raise SystemExit("키를 입력하지 않아 API를 호출하지 않았습니다.")
    return key


def _get_client(api_key: str):
    """max_retries=0 — 자동 재시도하지 않는다.

    재시도하면 실패한 호출도 과금되고, elapsed_sec 에 재시도 시간이 섞여
    '한 번 호출에 걸린 시간'이라는 측정 정의가 깨진다.
    """
    from openai import OpenAI

    settings = config.load_run_settings()
    return OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        timeout=settings.get("timeout_sec"),
        max_retries=0,
    )


def call_cloud(model_id: str, prompt: str, options: dict[str, Any], api_key: str):
    """한 번 호출하고 (response, elapsed_sec) 를 돌려준다.

    elapsed 는 요청 직전부터 최종 응답 수신 직후까지다. run_local 과 같은 정의다.
    다만 네트워크 왕복이 포함되므로 로컬 값과 그대로 비교하지 않는다.

    options 는 기록에 남은 것을 그대로 받는다 (run_local 과 같은 이유).
    """
    from time import perf_counter

    client = _get_client(api_key)

    kwargs: dict[str, Any] = {
        "model": model_id,
        "input": prompt,          # 독립 질문 — 이전 대화를 이어 붙이지 않는다
        "reasoning": {"effort": "none"},
        "tools": [],
        "tool_choice": "none",
        "store": False,           # 응답을 서버에 보관하지 않는다
    }
    kwargs.update(options)        # temperature / max_output_tokens

    start = perf_counter()
    response = client.responses.create(**kwargs)
    elapsed = perf_counter() - start
    return response, elapsed


def extract_usage(response: Any) -> tuple[int | None, int | None, str | None]:
    """(input_tokens, output_tokens, api_status) 를 뽑는다.

    값이 없으면 0 이 아니라 None 이다. 0 으로 채우면 '토큰을 안 썼다'가 되어
    비용 계산과 평균이 조용히 틀어진다.
    """
    usage = getattr(response, "usage", None)
    tin = getattr(usage, "input_tokens", None) if usage is not None else None
    tout = getattr(usage, "output_tokens", None) if usage is not None else None
    return tin, tout, getattr(response, "status", None)


def _fill_cost(rec: dict[str, Any], pricing: dict[str, Any]) -> None:
    """사용량 x 단가로 추정 비용을 계산한다. 실제 청구액이 아니다."""
    rec["price_input_per_1m_tokens"] = pricing.get("price_input_per_1m_tokens")
    rec["price_output_per_1m_tokens"] = pricing.get("price_output_per_1m_tokens")
    rec["price_currency"] = pricing.get("price_currency")

    tin, tout = rec.get("input_tokens"), rec.get("output_tokens")
    pin, pout = rec["price_input_per_1m_tokens"], rec["price_output_per_1m_tokens"]

    if None in (tin, tout, pin, pout):
        rec["estimated_cost"] = None
        rec["measurement_notes"]["estimated_cost"] = "토큰 사용량 또는 단가 미확인"
        return

    rec["estimated_cost"] = (tin / 1_000_000) * pin + (tout / 1_000_000) * pout


def run_all(dry_run: bool = False) -> recorder.RunLog:
    settings = config.load_run_settings()
    questions = config.question_map()
    pricing = config.load_models()["cloud_model"]
    model_id = pricing.get("model_id")

    if not model_id and not dry_run:
        raise SystemExit("models.json 의 cloud_model.model_id 를 먼저 채우세요.")

    target_ids = config.cloud_question_ids()
    print(f"Cloud 대상 질문 {len(target_ids)}개: {target_ids}")

    opts = config.cloud_options()
    print(f"요청 파라미터: {opts}")
    for name, why in config.cloud_option_gaps().items():
        print(f"  로컬 {name} 는 넘기지 못함 — {why}")

    log = recorder.RunLog(config.CLOUD_RUNS_PATH)
    api_key = None if dry_run else get_api_key()

    for qid in target_ids:
        q = questions[qid]
        run_id = f"CLOUD_{qid}_r1"

        if log.has(run_id):
            print(f"  skip (이미 기록됨): {run_id}")
            continue

        rec = recorder.new_cloud_record(
            run_id=run_id,
            phase=config.PHASE_MAIN,
            model_label="CLOUD",
            model_id=model_id or "",
            question_id=qid,
            repeat=1,
            prompt=q["prompt"],
            options=config.cloud_options(),
            settings_version=settings["settings_version"],
            questions_version=config.load_questions()["questions_version"],
        )

        # 로컬과 조건이 갈라지는 지점을 기록에 남긴다. 나중에 표로 옮길 때 근거가 된다.
        for name, why in config.cloud_option_gaps().items():
            rec["measurement_notes"][f"options.{name}"] = why

        if dry_run:
            print(f"  dry-run: {run_id}")
            continue

        elapsed = None
        try:
            # 기록에 남은 options 를 그대로 넘긴다 (run_local 과 같은 이유)
            response, elapsed = call_cloud(model_id, q["prompt"], rec["options"], api_key)
            rec["status"] = config.STATUS_SUCCESS
            rec["elapsed_sec"] = elapsed
            rec["response_text"] = getattr(response, "output_text", None)
            if rec["response_text"] is None:
                rec["measurement_notes"]["response_text"] = "응답에서 본문을 읽지 못함"

            tin, tout, api_status = extract_usage(response)
            rec["input_tokens"], rec["output_tokens"], rec["api_status"] = tin, tout, api_status
            if tin is None:
                rec["measurement_notes"]["input_tokens"] = "응답에 usage 없음"
            if tout is None:
                rec["measurement_notes"]["output_tokens"] = "응답에 usage 없음"
            _fill_cost(rec, pricing)

        except Exception as e:
            rec["status"] = config.STATUS_ERROR
            rec["error_type"] = type(e).__name__
            rec["error_message"] = str(e)  # 키가 섞이지 않는지 확인할 것
            rec["elapsed_sec"] = elapsed
            for f in ("input_tokens", "output_tokens", "estimated_cost"):
                rec["measurement_notes"].setdefault(f, "호출 실패로 측정 불가")

        log.append(rec)
        print(f"  {rec['status']}: {run_id}")

    print("\n" + log.summary())
    print("실행 전후로 API 사용량 페이지에서 실제 사용 내역을 확인하고, 추정 비용과 구분해 기록한다.")
    return log


def main() -> None:
    from . import use_utf8_stdout

    use_utf8_stdout()
    p = argparse.ArgumentParser(description="Cloud 비교 실험 실행")
    p.add_argument("--dry-run", action="store_true", help="호출 없이 대상만 출력")
    args = p.parse_args()
    run_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

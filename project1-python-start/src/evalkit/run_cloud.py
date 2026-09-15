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

    TODO: 구현
      - getpass.getpass() 로 입력받거나 os.environ 에서 읽는다.
      - 반환값을 로그·레코드·예외 메시지에 넣지 않는다.
    """
    raise NotImplementedError("get_api_key 미구현")


def call_cloud(model_id: str, prompt: str, options: dict[str, Any], api_key: str):
    """한 번 호출하고 (response, elapsed_sec) 를 돌려준다.

    TODO: 구현
      1. 클라이언트 생성 (max_retries=0 — 자동 재시도하지 않는다)
      2. start = perf_counter() 직후 요청
      3. elapsed = perf_counter() - start
      4. return response, elapsed
    """
    raise NotImplementedError("call_cloud 미구현")


def extract_usage(response: Any) -> tuple[int | None, int | None, str | None]:
    """(input_tokens, output_tokens, api_status) 를 뽑는다.

    TODO: 구현. 값이 없으면 0 이 아니라 None 을 돌려준다.
    """
    raise NotImplementedError("extract_usage 미구현")


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
            options=config.chat_options(),
            settings_version=settings["settings_version"],
            questions_version=config.load_questions()["questions_version"],
        )

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

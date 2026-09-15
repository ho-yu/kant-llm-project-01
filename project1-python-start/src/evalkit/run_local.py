"""로컬 실험 실행 엔트리.

저장·중복검사·루프 구조는 동작하는 코드다.
실제 Ollama 호출부만 TODO 로 비워 두었다.

실행 순서 (모델 한 개씩, 동시에 올리지 않는다)
    모델 로드 -> 워밍업 1회 -> Q01..Q10 x repeat -> 언로드 -> 다음 모델
"""

from __future__ import annotations

import argparse
from typing import Any

from . import config, recorder


# ---------------------------------------------------------------- 호출부 (TODO)


def call_ollama(model_tag: str, prompt: str, options: dict[str, Any], system_prompt: str | None):
    """한 번 호출하고 (response, elapsed_sec) 를 돌려준다.

    TODO: 구현
      1. from ollama import Client; client = Client(host=..., timeout=...)
      2. messages 를 구성한다.
         - run_settings.independent_questions=true 이므로 이전 대화 이력을 붙이지 않는다.
         - system_prompt 를 쓰는 경우에만 {"role": "system"} 을 앞에 둔다.
      3. start = perf_counter() 직후 client.chat(..., stream=False, options=options)
      4. elapsed = perf_counter() - start  (응답 수신 직후)
      5. return response, elapsed
    """
    raise NotImplementedError("call_ollama 미구현")


def fetch_ps(model_tag: str) -> list[Any]:
    """client.ps() 의 모델 목록을 돌려준다.

    반드시 응답을 받은 직후, 모델이 언로드되기 전에 호출해야 한다.
    여기서 digest / quantization_level / context_length / size_vram 을 얻는다.

    TODO: 구현
      1. client.ps() 호출
      2. 응답의 models 리스트를 반환
    """
    raise NotImplementedError("fetch_ps 미구현")


def unload_model(model_tag: str) -> None:
    """모델을 메모리에서 내린다. 다음 모델로 넘어가기 전에 호출한다.

    TODO: 구현 (예: keep_alive=0 으로 빈 요청을 보낸다)
    """
    raise NotImplementedError("unload_model 미구현")


# ---------------------------------------------------------------- 한 회차


def execute_once(
    log: recorder.RunLog,
    *,
    run_id: str,
    phase: str,
    model: dict[str, Any],
    prompt: str,
    settings: dict[str, Any],
    questions_version: str,
    question_id: str | None = None,
    repeat: int | None = None,
    retry_of_run_id: str | None = None,
    dry_run: bool = False,
) -> bool:
    """한 회차를 실행하고 결과를 append 한다.

    호출이 실패해도 건너뛰지 않고 status="error" 로 기록한다.
    """
    if log.has(run_id):
        print(f"  skip (이미 기록됨): {run_id}")
        return False

    rec = recorder.new_local_record(
        run_id=run_id,
        phase=phase,
        model_label=model["model_label"],
        model_tag=model["model_tag"],
        prompt=prompt,
        options=settings["options"],
        settings_version=settings["settings_version"],
        questions_version=questions_version,
        question_id=question_id,
        repeat=repeat,
        system_prompt=settings["system_prompt"] if settings.get("use_system_prompt") else None,
        retry_of_run_id=retry_of_run_id,
    )

    if dry_run:
        rec["status"] = config.STATUS_ERROR
        rec["error_type"] = "DryRun"
        rec["error_message"] = "dry-run 모드 — 실제 호출하지 않음"
        print(f"  dry-run: {run_id}")
        return False  # dry-run 은 저장하지 않는다

    elapsed = None
    try:
        response, elapsed = call_ollama(
            model["model_tag"], prompt, settings["options"], rec["system_prompt"]
        )
        recorder.fill_from_ollama_response(rec, response, elapsed)

        # 응답 직후, 언로드 전에 조회
        try:
            observed_at = recorder.now_iso()
            recorder.fill_from_ps(rec, fetch_ps(model["model_tag"]), observed_at)
        except Exception as e:  # ps 실패가 본 호출 결과를 지우지 않게 한다
            rec["measurement_notes"]["size_vram_mib"] = f"client.ps() 실패: {type(e).__name__}"
            rec["measurement_notes"]["processor"] = f"client.ps() 실패: {type(e).__name__}"

    except Exception as e:
        recorder.fill_error(rec, e, elapsed)

    log.append(rec)
    print(f"  {rec['status']}: {run_id}")
    return rec["status"] == config.STATUS_SUCCESS


# ---------------------------------------------------------------- 전체 루프


def run_all(dry_run: bool = False, only_model: str | None = None) -> recorder.RunLog:
    settings = config.load_run_settings()
    questions = config.load_questions()
    qversion = questions["questions_version"]
    models = config.enabled_models()
    if only_model:
        models = [m for m in models if m["model_label"] == only_model]

    log = recorder.RunLog(config.LOCAL_RUNS_PATH)

    for model in models:  # 모델 하나씩 — 동시에 메모리에 올리지 않는다
        label = model["model_label"]
        print(f"\n=== {model.get('display_name') or label} ===")

        # 워밍업 (본 집계에서 제외되지만 기록은 남긴다)
        warmup_qid = settings.get("warmup_question_id")
        warmup_prompt = config.question_map()[warmup_qid]["prompt"] if warmup_qid else None
        if warmup_prompt is None:
            print("  warmup 건너뜀: run_settings.warmup_question_id 미설정")
        else:
            execute_once(
                log,
                run_id=config.make_run_id(label, phase=config.PHASE_WARMUP),
                phase=config.PHASE_WARMUP,
                model=model,
                prompt=warmup_prompt,
                settings=settings,
                questions_version=qversion,
                question_id=warmup_qid,
                dry_run=dry_run,
            )

        # 본 실험
        for q in questions["questions"]:
            for rep in range(1, settings["repeats"] + 1):
                execute_once(
                    log,
                    run_id=config.make_run_id(label, q["question_id"], rep, config.PHASE_MAIN),
                    phase=config.PHASE_MAIN,
                    model=model,
                    prompt=q["prompt"],
                    settings=settings,
                    questions_version=qversion,
                    question_id=q["question_id"],
                    repeat=rep,
                    dry_run=dry_run,
                )

        if not dry_run:
            try:
                unload_model(model["model_tag"])
            except NotImplementedError:
                print("  unload_model 미구현 — 다음 모델 전에 수동으로 내린다")

    print("\n" + log.summary())
    return log


def main() -> None:
    from . import use_utf8_stdout

    use_utf8_stdout()
    p = argparse.ArgumentParser(description="로컬 비교 실험 실행")
    p.add_argument("--dry-run", action="store_true", help="호출 없이 실행 계획만 출력")
    p.add_argument("--model", help="특정 model_label 만 실행")
    args = p.parse_args()
    run_all(dry_run=args.dry_run, only_model=args.model)


if __name__ == "__main__":
    main()

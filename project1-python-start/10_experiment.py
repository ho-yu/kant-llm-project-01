"""실험 실행 — 아래 MODE 와 MODEL 만 바꿔서 실행합니다.

    uv run python 10_experiment.py

전형적인 순서
    1. MODE = "env"    실험 시작 전 한 번. 환경 정보를 수집합니다.
    2. MODE = "run"    MODEL = "B", LIMIT = 3 으로 먼저 확인
                       -> VRAM 이 null 이면 멈추고 keep_alive 를 확인합니다
                       -> 문제없으면 LIMIT = None 으로 바꿔 나머지를 채웁니다
                       -> MODEL 을 C, D, E 로 바꿔 반복
    3. MODE = "score"  80회를 다 채운 뒤. 채점용 빈 레코드를 만듭니다.
                       scores.jsonl 의 점수와 근거는 사람이 채웁니다.
    4. MODE = "table"  집계하고 마크다운 표를 만듭니다.

기록은 append 전용입니다. 중단해도 괜찮고, 다시 실행하면 이미 기록된
회차는 건너뛰고 이어집니다.
"""

from evalkit import aggregator, collect_env, exporter, peek, prepare_scores, run_local, validator

# ---------------------------------------------------------------- 설정

# "env" | "run" | "check" | "score" | "table"
MODE = "run"

# MODE="run" 일 때 실행할 모델.
# 모델 "라벨" 을 적습니다. 태그(hf.co/...)가 아닙니다.
# 라벨과 태그의 짝은 data/config/models.json 에 있습니다.
MODEL = "B"     # "B" / "C" / "D" / "E"

# 본 실험을 몇 건까지만 할지. None 이면 전부(질문 10개 x 2회 = 20건).
# 처음 돌릴 때는 3 정도로 두고 값이 제대로 들어가는지 확인합니다.
LIMIT = 1

# 호출하지 않고 계획만 보려면 True.
DRY_RUN = False

# MODE="check" 에서 특정 회차의 전문(원본 응답 포함)을 보려면 run_id 를 적습니다.
# 예: "B_Q01_r1". None 이면 최근 회차 요약만 보여줍니다.
RUN_ID = None


# ---------------------------------------------------------------- 실행


def show_status() -> None:
    peek.show_progress()
    print()
    peek.show_recent(5, MODEL if MODE == "run" else None)


def show_validation() -> None:
    print("\n" + "=" * 60)
    for report in validator.validate_all():
        print(report.render())


if MODE == "env":
    collect_env.run(dry_run=DRY_RUN)

elif MODE == "run":
    run_local.run_all(dry_run=DRY_RUN, only_model=MODEL, limit=LIMIT)
    if not DRY_RUN:
        print("\n" + "=" * 60)
        show_status()
        show_validation()

elif MODE == "check":
    if RUN_ID:
        peek.show_one(RUN_ID)
    else:
        show_status()
        show_validation()

elif MODE == "score":
    prepare_scores.run(dry_run=DRY_RUN)

elif MODE == "table":
    for path in aggregator.write_summaries():
        print("written:", path)
    for path in exporter.write_tables():
        print("written:", path)

else:
    raise SystemExit(f"알 수 없는 MODE: {MODE!r} — env / run / check / score / table 중 하나")

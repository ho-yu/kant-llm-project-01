"""기록된 회차를 확인합니다.

모델별 진행 상황과 최근 회차를 한 줄씩 보여줍니다.
11_run_model.py 를 돌린 뒤 바로 이걸 실행해 값이 들어갔는지 봅니다.

VRAM 이 null 이면 멈추고 run_settings.json 의 keep_alive 를 확인하세요.
응답 직후 모델이 언로드되면 VRAM·digest·context 를 읽을 수 없고,
기록은 append 전용이라 나중에 되돌릴 수 없습니다.
"""

from evalkit import peek

# 특정 모델만 보려면 "B" 처럼 적습니다. None 이면 전체.
MODEL = None

# 최근 몇 건을 보여줄지.
RECENT = 5

# 한 회차의 전문(원본 응답 포함)을 보려면 run_id 를 적습니다. 예: "B_Q01_r1"
RUN_ID = None


if RUN_ID:
    peek.show_one(RUN_ID)
else:
    peek.show_progress()
    print()
    peek.show_recent(RECENT, MODEL)

"""모델 하나를 실행해 결과를 data/raw/local/runs.jsonl 에 기록합니다.

아래 MODEL 만 바꿔 가며 B -> C -> D -> E 순서로 실행합니다.
모델을 한 번에 하나씩만 메모리에 올립니다.

중단해도 괜찮습니다. 다시 실행하면 이미 기록된 회차는 건너뛰고 이어집니다.

처음 돌릴 때는 LIMIT 를 3 정도로 두고 12_check.py 로 값이 제대로
들어갔는지 확인한 뒤, LIMIT = None 으로 바꿔 나머지를 채웁니다.
"""

from evalkit import run_local

# 실행할 모델: "B" / "C" / "D" / "E"
MODEL = "B"

# 본 실험을 몇 건까지만 할지. None 이면 전부(질문 10개 x 2회 = 20건).
LIMIT = 3

# True 면 호출하지 않고 실행 계획만 출력합니다.
DRY_RUN = False

run_local.run_all(dry_run=DRY_RUN, only_model=MODEL, limit=LIMIT)

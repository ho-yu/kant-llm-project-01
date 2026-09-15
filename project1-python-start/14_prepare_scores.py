"""채점용 빈 레코드를 data/scoring/scores.jsonl 에 깔아둡니다.

runs.jsonl 을 읽어 회차마다 빈 채점 레코드를 만듭니다.
run_id / question_id / 평가 기준 코드는 원본에서 그대로 가져오므로
손으로 적다가 틀릴 일이 없습니다.

점수는 전부 null 로 나옵니다. 사람이 점수와 근거만 채웁니다.
호출이 실패한 회차는 not_scored_reason 이 채워진 채로 나옵니다.

80회를 다 돌린 뒤에 실행합니다. 여러 번 실행해도
이미 만들어진 채점 레코드는 건너뜁니다.
"""

from evalkit import prepare_scores

# True 면 저장하지 않고 몇 건이 생길지만 보여줍니다.
DRY_RUN = False

# 워밍업 회차도 채점 대상에 넣을지. 기본은 제외입니다.
INCLUDE_WARMUP = False

prepare_scores.run(dry_run=DRY_RUN, include_warmup=INCLUDE_WARMUP)

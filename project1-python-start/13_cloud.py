"""STEP 07 — Cloud 모델로 비교용 5문항을 실행합니다.

    uv run python 13_cloud.py
    uv run python 13_cloud.py --probe-temperature

대상은 questions.json 에서 cloud_compare=true 인 질문뿐입니다.
결과를 보기 전에 확정된 목록이라, 여기서 고를 수 없습니다.

API 키
  실행할 때 입력받습니다. 화면에 보이지 않고 어떤 파일에도 저장되지 않습니다.
  환경변수 OPENAI_API_KEY 가 있으면 그것을 씁니다.

DRY_RUN = True 로 두면 호출하지 않고 대상과 요청 파라미터만 출력합니다.
중단해도 됩니다. 다시 실행하면 이미 기록된 회차는 건너뜁니다.
"""

import argparse

from evalkit import cloudsheet, run_cloud

# ---------------------------------------------------------------- 여기만 바꿉니다

DRY_RUN = False       # True 면 호출하지 않음. 대상·파라미터 확인용

# ----------------------------------------------------------------

BAR = "=" * 68

parser = argparse.ArgumentParser(description="STEP 07 Cloud 실행")
parser.add_argument(
    "--probe-temperature",
    action="store_true",
    help="temperature=0 요청을 1회 시험하고 기존 실험 기록에는 저장하지 않음",
)
args = parser.parse_args()

if args.probe_temperature:
    print(BAR)
    print("  Cloud temperature=0 지원 시험 (기존 실험과 분리)")
    print(BAR)
    run_cloud.probe_temperature()
    raise SystemExit(0)

print(BAR)
print("  STEP 07 — Cloud 실행" + ("  (dry-run)" if DRY_RUN else ""))
print(BAR)

run_cloud.run_all(dry_run=DRY_RUN)

# 실행 결과를 STEP 7 비교면에 반영한다 (적어 둔 Cloud 점수는 보존된다)
print()
print(cloudsheet.sync())

print("\n" + BAR)
print("  다음")
print(BAR)
print("  1. data/raw/cloud/runs.jsonl 에 기록이 쌓였는지 확인")
print("  2. docs/cloud-compare.md 에서 Cloud 응답 5건을 로컬과 같은 기준으로 채점")
print("  3. docs/steps/step07.md 의 비교표 작성")
print("  4. API 사용량 페이지에서 실제 사용 내역 확인 (추정 비용과 구분해 기록)")

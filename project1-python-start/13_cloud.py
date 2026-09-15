"""STEP 07 — Cloud 모델로 비교용 5문항을 실행합니다.

    uv run python 13_cloud.py

대상은 questions.json 에서 cloud_compare=true 인 질문뿐입니다.
결과를 보기 전에 확정된 목록이라, 여기서 고를 수 없습니다.

API 키
  실행할 때 입력받습니다. 화면에 보이지 않고 어떤 파일에도 저장되지 않습니다.
  환경변수 OPENAI_API_KEY 가 있으면 그것을 씁니다.

DRY_RUN = True 로 두면 호출하지 않고 대상과 요청 파라미터만 출력합니다.
중단해도 됩니다. 다시 실행하면 이미 기록된 회차는 건너뜁니다.
"""

from evalkit import run_cloud

# ---------------------------------------------------------------- 여기만 바꿉니다

DRY_RUN = True        # True 면 호출하지 않음. 대상·파라미터 확인용

# ----------------------------------------------------------------

BAR = "=" * 68

print(BAR)
print("  STEP 07 — Cloud 실행" + ("  (dry-run)" if DRY_RUN else ""))
print(BAR)

run_cloud.run_all(dry_run=DRY_RUN)

print("\n" + BAR)
print("  다음")
print(BAR)
print("  1. data/raw/cloud/runs.jsonl 에 기록이 쌓였는지 확인")
print("  2. docs/eval-results.md 에는 아직 Cloud 채점 블록이 없다 (로컬 120개뿐)")
print("  3. docs/steps/step07.md 의 비교표 작성")
print("  4. API 사용량 페이지에서 실제 사용 내역 확인 (추정 비용과 구분해 기록)")

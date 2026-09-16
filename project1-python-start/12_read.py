"""채점 준비 — 채점표를 맞추고, 원본 응답을 읽을 수 있게 뽑아냅니다.

    uv run python 12_read.py

두 가지를 합니다.

 1. docs/eval-results.md 의 채점 블록을 채점 대상에 맞춥니다
    (models.json 의 tier 와 questions.json 을 그대로 따릅니다).
    이미 적어 둔 점수는 run_id 로 찾아 그대로 옮기므로 여러 번 실행해도 됩니다.

 2. 질문마다 응답 모음 파일을 만듭니다

    data/derived/responses/Q01.md   ← Q01 에 대한 채점 대상 모델 × 2회 응답 전문
    data/derived/responses/Q02.md
    ...

채점 방법
  1. 이 파일을 실행한다 (모델을 더 돌릴 때마다 다시 실행하면 갱신된다)
  2. responses/Q01.md 를 열어 답을 나란히 읽는다
     — 질문, 기대 결과, 감점 요소가 맨 위에 같이 있다
  3. docs/eval-results.md 의 `## Q01 / Model C / Run 1` 블록에 점수와 근거를 적는다
  4. Q02, Q03 ... 순서로 반복
  5. 다 채우면 11_finish.py 로 집계

채점 대상을 바꾸려면 data/config/models.json 의 tier 를 고치고 다시 실행합니다.
  primary       = 채점하고 최종 선정 후보로 삼는다
  supplementary = 실행 기록과 성능 측정만 쓰고 채점하지 않는다

RESET = True 로 두면 적어 둔 점수를 전부 지우고 빈 양식으로 되돌립니다.
"""

from evalkit import cloudsheet, responses, scoresheet

# ---------------------------------------------------------------- 여기만 바꿉니다

RESET = False      # True 면 채점 내용을 전부 지웁니다. 되돌릴 수 없습니다.

# ----------------------------------------------------------------

if RESET:
    print("!! RESET=True — 적어 둔 점수를 모두 지웁니다.\n")

print(scoresheet.sync(preserve=not RESET))
print(cloudsheet.sync())
print()

for path in responses.write_all():
    print("written:", path)

print()
print("responses/Q01.md 부터 열어 읽고, docs/eval-results.md 에 점수를 적으세요.")

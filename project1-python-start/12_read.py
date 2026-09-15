"""채점하려고 원본 응답을 읽을 수 있게 뽑아냅니다.

    uv run python 12_read.py

질문마다 파일 하나씩 만들어집니다.

    data/derived/responses/Q01.md   ← Q01 에 대한 6개 모델 × 2회 응답 전문
    data/derived/responses/Q02.md
    ...

채점 방법
  1. 이 파일을 실행한다 (모델을 더 돌릴 때마다 다시 실행하면 갱신된다)
  2. responses/Q01.md 를 열어 6개 모델의 답을 나란히 읽는다
     — 질문, 기대 결과, 감점 요소가 맨 위에 같이 있다
  3. docs/eval-results.md 의 `## Q01 / Model A / Run 1` 블록에 점수와 근거를 적는다
  4. Q02, Q03 ... 순서로 반복
  5. 다 채우면 11_finish.py 로 집계

한 질문의 6개 답을 나란히 놓고 채점하면 같은 기준을 유지하기 쉽습니다.
"""

from evalkit import responses

for path in responses.write_all():
    print("written:", path)

print()
print("responses/Q01.md 부터 열어 읽고, docs/eval-results.md 에 점수를 적으세요.")

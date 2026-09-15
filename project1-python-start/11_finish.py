"""80회를 다 채운 뒤에 한 번 실행합니다.

    uv run python 11_finish.py

하는 일
  1. 저장된 기록을 다시 열어 검사
  2. 채점용 빈 레코드를 data/scoring/scores.jsonl 에 생성
     -> 점수와 근거는 사람이 채웁니다
  3. 집계하고 마크다운 표를 data/derived/tables/ 에 생성
  4. 4개 모델 전체 STEP 06 표를 출력

2번에서 만들어진 scores.jsonl 을 채운 뒤 다시 실행하면
품질 점수가 반영된 표가 나옵니다.
"""

from evalkit import aggregator, exporter, prepare_scores, report, validator

print(report.BAR)
print("  1. 기록 검사")
print(report.BAR)
for rep in validator.validate_all():
    print(rep.render())

print("\n" + report.BAR)
print("  2. 채점용 빈 레코드")
print(report.BAR)
prepare_scores.run()

print("\n" + report.BAR)
print("  3. 집계 / 표 생성")
print(report.BAR)
for path in aggregator.write_summaries():
    print("written:", path)
for path in exporter.write_tables():
    print("written:", path)

print("\n" + report.BAR)
print("  4. 전체 STEP 06 표")
print(report.BAR + "\n")
print(report.step06())

"""80회를 다 채운 뒤에 실행합니다.

    uv run python 11_finish.py

하는 일
  1. 저장된 실행 기록과 채점 입력면을 검사
  2. 집계하고 마크다운 표를 data/derived/tables/ 에 생성
  3. 4개 모델 전체 STEP 06 표를 출력

품질 채점은 docs/eval-results.md 에 직접 씁니다.
블록 제목(## Q01 / Model B / Run 1)이 곧 run_id 이므로
따로 적을 것은 없고, 점수와 근거만 채우면 됩니다.
채운 뒤 이 파일을 다시 실행하면 품질 점수가 표에 반영됩니다.
"""

from evalkit import aggregator, config, exporter, recorder, report, scoring, step07_report, validator

print(report.BAR)
print("  1. 검사")
print(report.BAR)
for rep in validator.validate_all():
    print(rep.render())

print("\n" + report.BAR)
print("  2. 채점 진행 상황")
print(report.BAR)
print(scoring.summary())
print("채점 입력면: docs/eval-results.md")

print("\n" + report.BAR)
print("  3. 집계 / 표 생성")
print(report.BAR)
for path in aggregator.write_summaries():
    print("written:", path)
for path in exporter.write_tables():
    print("written:", path)
cloud_ids = {r.get("question_id") for r in recorder.iter_records(config.CLOUD_RUNS_PATH)
             if r.get("phase") == config.PHASE_MAIN}
if cloud_ids == set(config.cloud_question_ids()):
    print("written: docs/steps/step07.md (" + step07_report.write() + ")")

print("\n" + report.BAR)
print("  4. 전체 STEP 06 표")
print(report.BAR + "\n")
print(report.step06())

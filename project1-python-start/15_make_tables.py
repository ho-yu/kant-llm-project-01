"""원본 기록에서 집계를 계산하고 마크다운 표를 만듭니다.

만들어지는 것 (data/derived/)
  local_summary.json / cloud_summary.json   집계 결과 + 기여한 run_id
  tables/model_comparison.md                산출물 2 — 제원 비교표
  tables/local_summary.md                   산출물 3 — 성능·품질 집계표
  tables/local_cloud.md                     산출물 4 — Local vs Cloud

저장된 값을 읽는 게 아니라 매번 runs.jsonl 에서 다시 계산합니다.
data/derived/ 를 지우고 이 파일만 다시 실행하면 복원됩니다.

표의 수치를 원본까지 역추적하려면 local_summary.json 의
source_run_ids 를 보고 12_check.py 의 RUN_ID 에 넣습니다.
"""

from evalkit import aggregator, exporter

for path in aggregator.write_summaries():
    print("written:", path)

for path in exporter.write_tables():
    print("written:", path)

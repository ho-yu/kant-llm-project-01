"""저장된 기록을 다시 열어 검사합니다.

  - 줄마다 JSON 으로 파싱되는가
  - 스키마 필수 필드가 다 있는가
  - run_id 가 겹치지 않는가
  - 값이 null 인 지표에 사유가 적혀 있는가
  - 채점 기록이 실제 실행 기록과 연결되는가
  - 계획한 회차 중 빠진 것이 있는가

ERROR 가 없으면 통과입니다.
아직 안 돌린 모델에 대한 커버리지 WARN 은 정상입니다.
"""

from evalkit import validator

for report in validator.validate_all():
    print(report.render())
    print()

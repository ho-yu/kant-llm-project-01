"""실행 환경 정보를 수집해 data/env/environment.json 에 채웁니다.

OS / Python / Ollama / 패키지 버전, GPU·VRAM·CPU·RAM,
모델별 digest·양자화·다운로드 크기가 자동으로 들어갑니다.

Model Card URL, License, 문서상 최대 Context 는 직접 확인해야 하는 값이라
건드리지 않고, 비어 있는 항목을 목록으로 알려줍니다.

실험 시작 전에 한 번 실행합니다. 여러 번 실행해도 안전합니다.
"""

from evalkit import collect_env

# True 로 두면 파일을 쓰지 않고 수집 결과만 보여줍니다.
DRY_RUN = False

collect_env.run(dry_run=DRY_RUN)

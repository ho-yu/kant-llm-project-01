"""로컬/Cloud LLM 비교 실험의 기록·검증·집계 도구.

모듈
    config      경로 상수, 설정 로더, run_id 생성
    schema      레코드 필드 정의 (세 축 분리: 호출 성공 / 측정 여부 / 품질)
    recorder    레코드 생성, append 저장, 중복 run_id 검사
    validator   저장된 파일 재파싱, 필드 누락·규칙 위반 검사
    aggregator  원본에서 집계 계산 (워밍업 제외, 지표별 n, 역추적용 run_id)
    exporter    집계 결과를 마크다운 표로 변환
    run_local   로컬 실험 실행 엔트리
    run_cloud   Cloud 실험 실행 엔트리

여기서 하위 모듈을 import 하지 않는다.
`python -m evalkit.validator` 처럼 실행할 때 RuntimeWarning 이 나기 때문이다.
"""


def use_utf8_stdout() -> None:
    """Windows 콘솔 기본 코드페이지(cp949)에서 한국어·em dash 출력이
    UnicodeEncodeError 로 죽는 것을 막는다. 각 모듈의 __main__ 에서 호출한다.
    """
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

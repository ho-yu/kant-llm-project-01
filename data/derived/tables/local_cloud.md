<!-- 자동 생성됨: python -m evalkit.exporter
     직접 수정하지 말 것. 원본: data/raw/, docs/eval-results.md -->

# Local vs Cloud (생성물)

| 기준 | Local LLM | Cloud API | 구분 |
|---|---|---|---|
| 집계 범위 | 질문 10개 x 2회 | 공통 5문항 x 1회 | **같은 문항 수가 아니다** |
| Quality | (품질표 참조) | (품질표 참조) | 실측 |
| Latency | Model C (금융) 2.89 (n=20) / Model D (코딩) 4.05 (n=20) / Model F (이커머스) 3.33 (n=20) | 6.97 (n=5) | 실측 |
| Cost |  | 0.0006 (n=5) | Cloud 는 추정치 / 로컬은 장비·전력·관리 비용 |
| Security |  |  | 운영 조건 분석 |
| Infrastructure |  |  | 운영 조건 분석 |
| Customization |  |  | 운영 조건 분석 |
| Operations |  |  | 운영 조건 분석 |

> 비교 대상: Model C (금융), Model D (코딩), Model F (이커머스). 최종 선정은 이 중에서 한다.
> **집계 범위가 다르다** — 로컬은 질문 10개 x 2회, Cloud 는 공통 5문항 ['Q01', 'Q04', 'Q06', 'Q09', 'Q10'] x 1회다. 이 표의 Local 열은 10문항 전체 평균이므로 Cloud 열과 같은 질문 집합이 아니다.
> 문항 단위로 맞춰 보려면 `docs/steps/step07.md` 의 '동일 문항 비교표' 를 쓴다 — 거기서는 같은 질문끼리 비교한다.
> 로컬 값은 Run 1·Run 2 **평균**이다. 회차 중 좋은 쪽만 골라 쓰지 않는다.
> 동일 조건 아님 — num_ctx: Cloud API 에는 컨텍스트 창 지정 파라미터가 없다
> 동일 조건 아님 — seed: Responses API 에는 seed 파라미터가 없다 — 재현성 조건이 로컬과 다르다
> 실측 결과와 운영 조건 분석을 구분한다. 로컬 총비용을 0 으로 적지 않는다.

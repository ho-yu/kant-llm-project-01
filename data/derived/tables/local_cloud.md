<!-- 자동 생성됨: python -m evalkit.exporter
     직접 수정하지 말 것. 원본: data/raw/, docs/eval-results.md -->

# Local vs Cloud (생성물)

| 기준 | Local LLM | Cloud API | 구분 |
|---|---|---|---|
| Quality | (품질표 참조) | (품질표 참조) | 실측 |
| Latency | Model C (금융) 2.89 (n=20) / Model D (코딩) 4.05 (n=20) / Model F (이커머스) 3.33 (n=20) | 집계 불가 (유효한 측정값 없음) | 실측 |
| Cost |  | 집계 불가 (유효한 측정값 없음) | Cloud 는 추정치 / 로컬은 장비·전력·관리 비용 |
| Security |  |  | 운영 조건 분석 |
| Infrastructure |  |  | 운영 조건 분석 |
| Customization |  |  | 운영 조건 분석 |
| Operations |  |  | 운영 조건 분석 |

> 비교 대상: Model C (금융), Model D (코딩), Model F (이커머스). 최종 선정은 이 중에서 한다.
> 반복 수: 로컬 질문당 2회, Cloud 질문당 1회. Cloud 대상 문항 ['Q01', 'Q04', 'Q06', 'Q09', 'Q10']
> 동일 조건 아님 — num_ctx: Cloud API 에는 컨텍스트 창 지정 파라미터가 없다
> 동일 조건 아님 — seed: Responses API 에는 seed 파라미터가 없다 — 재현성 조건이 로컬과 다르다
> 동일 조건 아님 — temperature: 이 모델은 temperature 를 지정할 수 없다. 로컬 0 / Cloud 1 (모델 고정값) 로 다르다
> 실측 결과와 운영 조건 분석을 구분한다. 로컬 총비용을 0 으로 적지 않는다.

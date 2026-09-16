# Step 07

<일반적인 이커머스 고객 문의와 셀러 업무 질문에 적절하게 답변할 수 있는 로컬 LLM을 비교·평가하여 가장 적합한 모델을 선정한다.>

## 1. Cloud 모델 선정 및 실행

| | |
|---|---|
| 모델 | **GPT LUNA** (`gpt-5.6-luna`) — `data/config/models.json` 의 `cloud_model` |
| 대상 문항 | STEP 5에서 사전 선정한 **Q01·Q04·Q06·Q09·Q10** × 각 1회 |
| 실행 | `uv run python 13_cloud.py` (`DRY_RUN = False` 로 바꾼 뒤) |
| 기록 | `data/raw/cloud/runs.jsonl` *(실행 시 생성)* |
| 상태 | **미실행** |

API 키는 실행 시점에 입력받거나 `OPENAI_API_KEY` 에서 읽고 **어떤 파일에도 저장하지 않는다.**
자동 재시도를 끄고(`max_retries=0`) 호출한다 — 재시도하면 실패분도 과금되고
`elapsed_sec` 에 재시도 시간이 섞여 측정 정의가 깨진다.

**실행 전에 채울 것** — `models.json` 의 `cloud_model`

- [ ] `price_input_per_1m_tokens` / `price_output_per_1m_tokens` / `price_currency`
- [ ] `price_source_url` / `price_checked_at` (공식 가격 페이지와 확인 날짜)

비우면 호출은 되지만 `estimated_cost` 가 `null` 로 남고 사유가 기록된다.

### 동일 조건이 아닌 축 — 반드시 기재

로컬과 Cloud 는 파라미터 이름이 다르고, Cloud 쪽에 아예 없는 것도 있다.
`13_cloud.py` 가 실행할 때 화면에 찍고, 각 기록의 `measurement_notes` 에도 남긴다.

| 설정 | 로컬 | Cloud |
|---|---|---|
| 출력 한도 | `num_predict` 768 | `max_output_tokens` 768 — **같음** |
| temperature | `0` | **지정 불가** (모델 고정값 1로 알려짐) |
| `num_ctx` | 4096 | **지정 불가** — API 에 해당 파라미터가 없다 |
| `seed` | 0 | **지정 불가** — Responses API 에 없다 |
| 반복 | 질문당 2회 | 질문당 **1회** |

> temperature 지정이 실제로 가능한 것으로 확인되면 `models.json` 의
> `supports_temperature` 를 `true` 로 바꾼다. 코드는 건드리지 않아도 된다.

## 2. 로컬 동일 문항 결과와 비교

> Cloud 실행 후 아래 '동일 문항 비교표' 를 채운다.
> 로컬 점수는 `docs/eval-results.md` 채점 결과에서 나온다 (Q01·Q04·Q06·Q09·Q10).

## 3. 운영 조건 비교

> 실측(품질·비용·속도)과 운영 조건 분석(보안·인프라·운영 난이도·커스터마이징)을
> **구분해서** 쓴다 — 평가표 #7 요구사항.
> STEP 1 에서 "데이터 보안 중요하지 않음" 으로 정했으므로, 보안 축의 판단 근거로 재사용한다.


---

## 산출물 정리

> 연결 산출물: [deliverables.md](../deliverables.md)
> - `4. Local LLM vs Cloud API 비교` ← **이 스텝이 원본**
> - `3. Model Test / Benchmark 결과` → Cloud 실행 기록
> - 요구사항 충족도 평가표 **#7. Local–Cloud 비교**

### Cloud 실행 기록 필드

| 필드 | 설명 |
|---|---|
| `question_id` | STEP 5에서 사전 선정한 5개 |
| `model` | Cloud 모델 식별값 |
| `prompt` | 실제 입력 전문 |
| `response` | 원본 응답 전문 |
| `status` | 처리 상태 (completed 등) |
| `latency_s` | 응답 시간 |
| `input_tokens` / `output_tokens` | 토큰 사용량 |
| `cost` | 비용 (단가 × 토큰) |
| `options` | 실행 설정 |
| `timestamp` | 실행 시각 |

### 동일 문항 비교표 (Cloud 5문항)

| 질문 ID | Model C 품질 | Model D 품질 | Model F 품질 | Cloud 품질 | Cloud latency | Cloud 토큰 | Cloud 비용 |
|---|---|---|---|---|---|---|---|
| Q01 | | | | | | | |
| Q04 | | | | | | | |
| Q06 | | | | | | | |
| Q09 | | | | | | | |
| Q10 | | | | | | | |

> 로컬 품질은 각 모델의 Run 1·Run 2 평균이다 (`eval-results.md` 에서 나온다).
> 로컬 latency 는 모델마다 다르므로 STEP 6 표를 참조하고 여기서 중복 기재하지 않는다.
> 부가 테스트(A·B·E)는 이 비교에 넣지 않는다.

### Local vs Cloud 비교 (산출물 4)

| 비교 축 | Local (선정 모델) | Cloud (GPT LUNA) | 판단 근거 |
|---|---|---|---|
| 품질 | | | 동일 5문항 채점 결과 (실측) |
| 비용 | | | Cloud는 실측 토큰 × 단가 / Local은 장비·전력 |
| 속도 | | | 실측 latency |
| 보안 | | | 데이터 외부 전송 여부 (STEP 1: 보안 중요도 낮음) |
| 인프라 | | | VRAM 8GB 제약 vs API 의존 |
| 운영 난이도 | | | 모델 관리·업데이트·장애 대응 |
| 커스터마이징 가능성 | | | Fine-tuning / 프롬프트·파라미터 제어 범위 |

### 주의 — 평가표 #7 필수 조건

- [ ] **반복 수 차이 명시**: 로컬 2회 vs Cloud 1회 → 동일 조건 비교가 아님을 기재
- [ ] **샘플링 조건 차이 명시**: temperature 로컬 0 / Cloud 모델 고정값, `num_ctx`·`seed` 는 Cloud 지정 불가
      (각 Cloud 기록의 `measurement_notes` 에 사유가 남아 있다)
- [ ] **비교 대상 명시**: 로컬 후보 3개(C·D·F). 부가 테스트 A·B·E 는 제외
- [ ] 지표별 **집계 응답 수(n)** 표시
- [ ] **실측 결과**(품질·비용·속도)와 **운영 조건 분석**(보안·인프라·운영 난이도·커스터마이징)을 구분해서 서술
- [ ] API 키는 저장소·문서·노션에 기록하지 않음
- [ ] 누적 사용량·비용 확인 (자동 재시도 없음, 자동 차단 없음)

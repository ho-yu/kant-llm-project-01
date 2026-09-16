# 이커머스 고객 문의 대응 로컬 LLM 비교·선정

상품 상세페이지 기반 고객 문의에 답변할 **로컬 LLM 후보를 비교하고 1개를 선정**하는 프로젝트다.

| | |
|---|---|
| 수행 형태 | 개인 |
| 실행 환경 | Windows 11 · RTX 5060 Laptop (VRAM 8GB) · Ollama |
| 실행 완료 | 로컬 6개 모델 × 10문항 × 2회 = **120회** |
| 채점 대상 | 3개 모델 × 10문항 × 2회 = **60블록** |
| 현재 진행 | 채점 **15 / 60** · Cloud 비교 미실행 |

---

## 1. 문제 정의 — 무엇을 풀려고 하는가

상품별 고객 문의에 답변하는 시스템을 운영 중인데 **문의 폭주로 업무가 마비**됐다.
정확히 답변할 수 있는 자동 응답 모델이 필요하다.

| 항목 | 내용 |
|---|---|
| 사용 사례 | 상품 상세페이지 정보 기반 고객 문의 자동 응답 |
| 사용자 | 일반 쇼핑몰 고객 |
| 태스크 | 상품 관련 질의응답 + 셀러 업무 질문 |
| 한국어 성능 | **중요** |
| 응답 속도 | **중요** |
| 데이터 보안 | 중요하지 않음 → STEP 7 Local–Cloud 판단 근거로 재사용 |

원문: [docs/steps/step01.md](docs/steps/step01.md)

## 2. 선정 기준 — 실험 전에 확정

결과를 보고 기준을 바꾸지 않기 위해 **실험 시작 전에** 정했다.

**모델 요구사항** — VRAM 8GB 제약에서 도출

| 항목 | 기준 | 이유 |
|---|---|---|
| 파라미터 규모 | 7~8B 급 | 가중치와 KV 캐시가 8GB 에 함께 올라가야 한다 |
| 양자화 | Q4_K_M | 7~8B 이 4.3~4.6GB 로 내려와 여유가 남는다 |
| Context Length | 4,096 이상 | 상세페이지 정보 + 질문 + 답변 |
| 배포 형식 | Ollama GGUF | `ollama pull` 로 받을 수 있어야 한다 |

**필수 통과 조건 (Pass/Fail)** — 판정 대상은 비교 대상 3개

| # | 조건 | 확인 시점 |
|---|---|---|
| 1 | 한국어 Chat/QA 가능 | STEP 6 |
| 2 | Ollama 실행 가능 | STEP 3~4 |
| 3 | 현재 PC에서 안정 실행 | STEP 4, 6 |
| 4 | 상업적 활용 가능 License | STEP 3 |
| 5 | 이커머스 질의 처리 가능한 Context Length | STEP 3, 6 |
| 6 | **전체 평균 3.5 이상** (1~5점) | STEP 5~6 |

조건 6 판정은 손으로 계산하지 않는다. 통과선 3.5 는 `questions.json` 의
`score_scale.pass_threshold` 에 값으로 박혀 있고, `11_finish.py` 가 그 값을 읽어
`Pass / Fail` 을 STEP 06 표에 찍는다.

**선호 우선순위** — 답변 품질 → 한국어 자연스러움 → Instruction Following → 응답 속도 → 메모리 사용량

4·5 순위는 이미 실측이 끝났다 (5절). 1~3 순위는 채점 결과로 정해진다.

원문: [docs/steps/step02.md](docs/steps/step02.md)

## 3. 후보 모델 — 도메인이 다른 6개를 돌리고 3개로 좁힘

도메인 특화가 서로 다른 모델이 이커머스 질의에 어떻게 반응하는지 보려고 6개를 전부 실행했다.
그중 **채점과 최종 선정은 3개**로 한정한다.

| 구분 | 라벨 | 도메인 | 모델 |
|---|---|---|---|
| **비교 대상** | C | 금융 | BCCard-Llama-3.1-Kor-Finance-8B |
| **비교 대상** | D | 코딩 | Qwen2.5-Coder-7B-Instruct |
| **비교 대상** | F | 이커머스 | sam-1-base |
| 부가 테스트 | A | 법률 | Llama-3.1-Korean-8B-Instruct-Law |
| 부가 테스트 | B | 의료·바이오 | KoBioMed-Llama-3.1-8B-Instruct |
| 부가 테스트 | E | 수학 | Math-IIO-7B-Instruct |

과제 필수는 로컬 후보 2개이므로 3개는 그 이상이다.
부가 3개의 **실행 기록과 성능 측정값은 지우지 않는다** — 제외 근거도 산출물이다.

제원·License·Model Card 출처: [data/derived/tables/model_comparison.md](data/derived/tables/model_comparison.md)
후보 조사 원문: [docs/steps/step03.md](docs/steps/step03.md)

> **Model F 교체 이력** — 당초 이커머스 후보는 POLAR-14B-v0.5 였으나 GGUF 변환본이
> 응답 포맷 오류(500)로 호출 자체가 불가능했다. 12:43·14:42 두 차례 동일 실패를 확인하고
> 같은 도메인의 sam-1-base 로 교체했다. 삭제한 기록과 사유는
> [docs/steps/step06.md](docs/steps/step06.md) '실행 기록 삭제 이력' 에 남아 있다.

## 4. 실험 설계 — 조건을 어떻게 통제했는가

**질문 10개** (정상 6 / 경계 2 / 정보 부족 2), 고객 문의 5 + 셀러 업무 5.
Cloud 비교용 5문항(Q01·Q04·Q06·Q09·Q10)은 **결과를 보기 전에** 선정했다.

**실행 설정** — 6개 모델에 동일 적용

| 설정 | 값 | 이유 |
|---|---|---|
| `temperature` | 0 | 모델 차이인지 운인지 섞이면 비교가 성립하지 않는다 |
| `num_predict` | 768 | 가장 긴 답변도 잘리지 않는 선. 무한 생성 방지 |
| `num_ctx` | 4096 | 6개 모델 기본값이 같아 조건이 동일해진다 |
| `seed` | 0 | 재현성 |
| system prompt | 없음 | 모델마다 처리 방식이 달라 특정 모델에 유리해질 수 있다 |
| 반복 | 2회 | 한 번의 운을 배제 |
| 워밍업 | 모델당 1회 | 첫 호출의 로딩 시간을 본 실험에서 걷어낸다 |

**채점 기준** — 1~5점, 문제마다 해당 기준만 적용

| 코드 | 기준 | 출제 |
|---|---|---|
| A | 답변 적합성 | 10문항 |
| B | 논리성/실용성 | 9문항 |
| C | 한국어 표현 | 10문항 |
| D | 지시사항 준수 | 3문항 |
| E | 정보 부족 / 불확실성 대응 | 4문항 |

질문 원문·기대 결과·감점 요소: [docs/steps/step05.md](docs/steps/step05.md)

## 5. 실행 결과 — 성능 측정 (완료)

**호출 60/60 성공, 측정 결측 0건.**

| 지표 | Model C (금융) | Model D (코딩) | Model F (이커머스) |
|---|---|---|---|
| 호출 성공 / 시도 | 20 / 20 | 20 / 20 | 20 / 20 |
| 평균 응답 시간 | 2.89s | 4.05s | 3.33s |
| 평균 생성 속도 | 61.13 t/s | 66.97 t/s | 61.58 t/s |
| 평균 출력 토큰 | 158.4 | 252.0 | 187.1 |
| VRAM (관측 시점) | 5,027 MiB | 4,528 MiB | 4,528 MiB |
| CPU/GPU 적재 | 100% GPU | 100% GPU | 100% GPU |
| 출력 한도 도달 | 0회 | 0회 | 0회 |

부가 테스트 3개를 포함한 전체 표: [docs/steps/step06.md](docs/steps/step06.md)

> 워밍업 분리가 실제로 동작했다 — 워밍업에서 모델 로딩(약 4.6초)을 흡수해
> 본 실험 120회의 평균 로딩 시간이 0.2초다. 첫 실행 지연과 일반 응답 지연이 섞이지 않았다.

**부가 테스트에서 관찰된 것** (채점 대상은 아니나 기록)

- Model A: 20회 전부 `done_reason=length` — 정지 토큰을 내지 못하고 출력 한도까지 생성
- Model B: 20회 중 14회에서 응답에 통계 필드가 없어 속도 지표를 측정하지 못함 (`n=6`)

## 6. 현재 진행 — 품질 채점 15/60

| 질문 | Model C (금융) | Model D (코딩) | Model F (이커머스) |
|---|---|---|---|
| Q01 일반 고객 문의 대응 | 3.33 | 4.00 | 4.50 |
| Q02 상품 불량 고객 대응 | 3.33 | 3.67 | 4.67 |
| Q03 복수 요청 처리 | 2.50 | 진행 중 | 미채점 |
| Q04 ~ Q10 | 미채점 | 미채점 | 미채점 |

> **아직 판정할 수 없는 수치다.** 10문제 중 2~3문제만 반영됐고,
> 경계·정보 부족 사례(Q04·Q05·Q09·Q10)와 기준 D·E는 표본이 없다.
> 필수 조건 6(평균 3.5)은 60블록을 채운 뒤에 확정한다.

최신 값: `uv run python 11_finish.py`

### Run 1 · Run 2 가 같지 않다

`temperature=0` 인데도 두 회차 응답이 대부분 달랐다.

| | 응답 전문 완전 일치 |
|---|---|
| Model C | 2 / 10 문항 |
| Model D | 1 / 10 문항 |
| Model F | 3 / 10 문항 |

`temperature=0` 은 "매번 최고 확률 토큰을 고른다"는 뜻이지 "매번 같은 계산 결과"를 뜻하지 않는다.
GPU 부동소수점 연산의 미세한 차이가 비슷한 확률의 두 토큰 중 선택을 뒤집고, 한 번 갈리면 이후 문장이 통째로 달라진다.

→ 두 회차를 각각 채점한다. **점수 차이가 큰 모델은 품질이 불안정하다는 신호**로 본다.
→ STEP 8 한계 항목에 기재한다.

## 7. 남은 작업

| | 내용 |
|---|---|
| 1 | 품질 채점 45블록 (Q03~Q10) + 재검토 |
| 2 | Cloud(GPT LUNA) 5문항 실행 + 단가 기입 |
| 3 | `문서상 최대 Context` 3건 확인 — 필수 조건 5 판정 근거 |
| 4 | STEP 8 최종 선정 + 운영 권고 |
| 5 | 본인 재실행 기록 |

---

# 재현 방법

## 환경 준비

```bash
cd project1-python-start && uv sync
```

Ollama 앱을 실행해 두고 모델을 받는다.

```bash
ollama pull hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M
ollama pull hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
ollama pull hf.co/mradermacher/sam-1-base-GGUF:Q4_K_M
```

부가 테스트 3개까지 재현하려면:

```bash
ollama pull hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M
ollama pull hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M
ollama pull hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M
```

## 실행 파일은 네 개

| 파일 | 언제 | 바꿀 값 |
|---|---|---|
| `10_run.py` | 모델마다 | `MODEL` (A~F), `LIMIT` |
| `12_read.py` | 채점 전 / 채점 대상을 바꾼 뒤 | `RESET` (평소 False) |
| `11_finish.py` | 채점 중 수시로 | 없음 |
| `13_cloud.py` | STEP 7 | `DRY_RUN` |

**1. 로컬 실험**

```bash
cd project1-python-start && uv run python 10_run.py
```

`MODEL` 을 A~F 로 바꿔 가며 6번 실행한다. 중단해도 되고, 다시 실행하면 기록된 회차는 건너뛴다.
처음에는 `LIMIT = 3` 으로 확인한 뒤 `None` 으로 바꾼다.
실행 전에 `data/config/run_settings.json` 이 비어 있으면 무엇이 빠졌는지 알려주고 **실행을 거부한다.**

**2. 채점 준비**

```bash
uv run python 12_read.py
```

`docs/eval-results.md` 의 채점표를 `questions.json` + `models.json` 의 `tier` 에 맞춰 동기화하고,
질문별 응답 모음 `data/derived/responses/Q01~Q10.md` 를 만든다.
적어 둔 점수는 `run_id` 로 찾아 옮기므로 여러 번 실행해도 안전하다.

**3. 채점** — `responses/Q01.md` 를 왼쪽에, `docs/eval-results.md` 를 오른쪽에 두고 질문 단위로 채운다.

**4. 집계**

```bash
uv run python 11_finish.py
```

검사 → 진행률 → 집계표 생성 → STEP 06 표 출력. `docs/steps/step04.md` · `step06.md` 의 자동 구간이 갱신된다.

**5. Cloud 비교**

```bash
uv run python 13_cloud.py
```

`cloud_compare=true` 인 5문항을 각 1회 호출한다.
**API 키는 실행 시점에 입력받고 어떤 파일에도 저장하지 않는다.**

각 설정값의 의미와 문제 상황별 대처: [docs/usage.md](docs/usage.md)

---

# 파일 위치

## 입력 (1회 확정 후 고정)

| 경로 | 내용 |
|---|---|
| `data/config/models.json` | 모델 태그 · `tier`(채점 대상 여부) · 주요 특징 · Cloud 모델 |
| `data/config/questions.json` | 질문 10개 · 평가 기준 · Cloud 대상 문항 · 척도 |
| `data/config/run_settings.json` | 실행 설정 (설정마다 `_note` 에 이유) |
| `data/env/environment.json` | 실행 환경 · 모델 제원 (대부분 자동 수집) |

## 원본 기록 (append 전용 — 수정·삭제하지 않는다)

| 경로 | 내용 |
|---|---|
| `data/raw/local/runs.jsonl` | 로컬 실행 126건 (본 실험 120 + 워밍업 6) |
| `data/raw/cloud/runs.jsonl` | Cloud 실행 기록 *(STEP 7 실행 시 생성)* |
| `docs/eval-results.md` | **채점 입력면** — 여기에 직접 점수·근거를 적는다 |

## 생성물 (언제든 재생성 가능 — 직접 고치지 않는다)

| 경로 | 내용 |
|---|---|
| `data/derived/scores.jsonl` | 채점 결과 원본 (점수·근거·재검토, `run_id` 로 실행 기록과 연결) |
| `data/derived/local_summary.json` | 로컬 집계 + 품질 집계 (기여 `run_id` 포함) |
| `data/derived/cloud_summary.json` | Cloud 집계 |
| `data/derived/responses/Q01~Q10.md` | 채점용 응답 모음 |
| `data/derived/tables/model_comparison.md` | 산출물 2 — 제원 비교표 |
| `data/derived/tables/local_summary.md` | 산출물 3 — 성능·품질 집계표 |
| `data/derived/tables/local_cloud.md` | 산출물 4 — Local vs Cloud |

## 문서

| 경로 | 내용 |
|---|---|
| `docs/steps/step01~08.md` | 단계별 작업 기록 |
| `docs/deliverables.md` | 산출물 체크리스트 + 요구사항 충족도 평가표 |
| `docs/usage.md` | 설정값 의미 · 사용법 · 문제 상황별 대처 |
| `docs/data-flow.md` | 데이터 흐름 · 파일 역할 |
| `docs/roadmap.md` | 장기 로드맵 |

## 실행 코드

| 경로 | 내용 |
|---|---|
| `src/evalkit/config.py` | 경로 상수, 설정 로더, `run_id` 생성 |
| `src/evalkit/schema.py` | 레코드 필드 정의 |
| `src/evalkit/recorder.py` | 레코드 생성 / append 저장 / 중복 `run_id` 검사 |
| `src/evalkit/run_local.py` | 로컬 실험 실행 |
| `src/evalkit/run_cloud.py` | Cloud 실험 실행 |
| `src/evalkit/collect_env.py` | 실행 환경 자동 수집 |
| `src/evalkit/scoresheet.py` | 채점표 생성 |
| `src/evalkit/responses.py` | 채점용 응답 모음 생성 |
| `src/evalkit/scoring.py` | `eval-results.md` 채점 읽기 |
| `src/evalkit/validator.py` | 저장된 파일 재검증 |
| `src/evalkit/aggregator.py` | 원본에서 집계 계산 |
| `src/evalkit/exporter.py` | 집계 결과 → 마크다운 표 · `scores.jsonl` |
| `src/evalkit/report.py` | STEP 04/06 형식 출력 |
| `src/evalkit/peek.py` | 기록 훑어보기 |
| `0*_*.py`, `99_*.py` | 모델별 단발 호출 예제 (수동 확인용) |

## 저장소에 없는 것

모델 가중치 파일 (Ollama 보관) · API 키 · `.venv/`

---

# 기록 규칙

코드가 강제하고 `validator` 가 검사한다.

1. 측정하지 못한 값은 `0` 이 아니라 `null` + `measurement_notes` 에 사유
2. **호출 실패 / 측정 누락 / 품질 미달은 서로 다른 축** — 한 칸에 섞지 않는다
3. 워밍업은 기록하되 기본 집계에서 제외
4. 재시도는 별도 `run_id` 를 받으며 원래 실패 기록을 덮어쓰지 않음
5. `run_id` 중복 시 건너뛰고 경고
6. 원본 기록 파일은 append 모드로만 연다
7. 집계값은 `source_run_ids` 로 원본 회차까지 역추적된다

## 측정값 출처와 단위

| 지표 | 출처 | 변환 |
|---|---|---|
| `elapsed_sec` | 요청 직전 ~ 응답 수신 직후 | 초 (**TTFT 아님**) |
| `load_duration_sec` | `response.load_duration` | ns ÷ 1e9 |
| `tokens_per_sec` | `eval_count` / (`eval_duration` / 1e9) | — |
| `prompt_eval_count` | `response.prompt_eval_count` | 입력 토큰 수 |
| `size_vram_mib` | `client.ps()` 의 `size_vram` | bytes ÷ 1,048,576 |
| `processor` | `size` 와 `size_vram` 비율 | `size_vram==size` → 100% GPU |
| `done_reason` | `response.done_reason` | `length` 면 출력 한도에서 잘림 |

- `size_vram` 은 **관측 시점의 값이며 최대 VRAM 이 아니다**
- `processor` 는 CPU/GPU 적재 상태이며 **GPU 이용률이 아니다**
- `quantization_level` 은 `ps()` 가 `unknown` 을 돌려줄 수 있어 비교표에 모델 태그 기준값을 함께 적는다
- `done_reason="length"` 인 응답은 잘린 답변이므로 채점 시 "내용 부족"과 구분한다

## 보안

- API 키는 실행 시점에 입력받거나 환경변수에서 읽는다. **파일·기록·로그 어디에도 남기지 않는다**
- Cloud 호출은 자동 재시도하지 않는다 (`max_retries=0`) — 실패분도 과금되고 측정 정의가 깨진다
- 공개 자료와 가상 데이터만 사용한다

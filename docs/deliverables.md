# 최종 산출물

> 이 문서의 수치는 원본 기록에서 나온다. 특정 값이 어느 실행에서 나왔는지 확인하려면
> `run_id` 로 역추적한다 — `aggregator.trace("F_Q01_r1")` 이 실행 기록과 채점 기록을
> 함께 돌려준다. 경로와 흐름은 [data-flow.md](data-flow.md) 참조.

| | |
|---|---|
| 수행 형태 | 개인 |
| 사용 사례 | 이커머스 고객 문의 대응 + 셀러 업무 지원 자동 응답 |
| 입력 범위 | 상품 맥락을 프롬프트에 제공하지 않고 물었다 — 상세페이지 기반 응답은 평가 범위 밖 |
| 실행 환경 | Windows 11 · RTX 5060 Laptop (VRAM 8,151 MiB) · RAM 31.4 GB · Ollama 0.34.0 · Python 3.12 |
| 로컬 실험 | 6개 모델 × 10문항 × 2회 = **본 실험 120회** (+ 모델당 워밍업 1회 = 6회, 별도 기록) |
| 채점 | 비교 대상 3개 × 10문항 × 2회 = **60블록 완료** (재검토 포함) |
| Cloud 실험 | GPT LUNA × 공통 5문항 × 1회 = **5회** |
| 최종 선정 | **Model F (이커머스 특화, `sam-1-base` Q4_K_M)** |

> 발제문 필수는 로컬 후보 **2개**다. 이 프로젝트는 **3개**(C·D·F)를 채점·선정 대상으로 두었다.

---

# 7. 주요 산출물

## 1) GitHub Repository

저장소: <https://github.com/ho-yu/kant-llm-project-01>

| 포함 내용 | 위치 | 확인 |
|---|---|---|
| 모델 실행 코드 | `project1-python-start/10_run.py` · `13_cloud.py` · `src/evalkit/` | ✅ |
| 환경 설정 (자동 수집) | [`data/env/environment.json`](../data/env/environment.json) | ✅ |
| 실행 조건 (단일 출처) | [`data/config/execution_conditions.json`](../data/config/execution_conditions.json) | ✅ |
| 의존성 · Python 버전 | `project1-python-start/pyproject.toml` · `uv.lock` · `.python-version` (3.12) | ✅ |
| README — 실행 방법 | [README.md](../README.md) `재현 방법` | ✅ |
| README — 입력 질문 / 실행 설정 / 결과 파일 위치 | [README.md](../README.md) `파일 위치` | ✅ |
| 재실행 확인 기록 (개인 필수) | [`docs/steps/step04.md`](steps/step04.md) `재실행 확인 기록` | ✅ 2026-09-17 |

**저장소에 올리지 않은 것** — `.gitignore` 로 차단한다.

| 항목 | 처리 |
|---|---|
| 모델 가중치 | 올리지 않음. 모델 태그와 `ollama pull` 명령만 안내 ([step03.md](steps/step03.md)) |
| API 키 | **어떤 파일에도 저장하지 않음.** 실행 시점에 `getpass` 로 입력받거나 `OPENAI_API_KEY` 환경변수 사용 |
| 가상환경 | `.venv/` 를 `.gitignore` 에 등록 |

> Python 버전 주의 — `.venv` 는 3.12.13 이지만 실행 기록 126건은 **3.12.10 시점**에 만들어졌다.
> 실험 도중 패치 버전이 올라갔다. 모델 추론은 Ollama 서버가 수행하므로 측정값에는 영향이 없다.
> 기록은 그 시점의 사실이므로 그대로 둔다.

## 2) Model Comparison Table

**생성물 원본**: [`data/derived/tables/model_comparison.md`](../data/derived/tables/model_comparison.md) — `11_finish.py` 가 다시 만든다
**조사 원문**: [`docs/steps/step03.md`](steps/step03.md)

| 항목 | Model C (금융) | Model D (코딩) | Model F (이커머스) | Cloud (GPT LUNA) |
|---|---|---|---|---|
| Model Name | BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF | Qwen2.5-Coder-7B-Instruct-GGUF | sam-1-base-GGUF | gpt-5.6-luna |
| Parameter | 8.03B | 7.62B | 7.62B | 비공개 |
| Architecture | `LlamaForCausalLM` (Llama 3.1 8B 계열) | `Qwen2ForCausalLM` (Qwen2.5 계열) | `Qwen2ForCausalLM` (base Qwen2.5-7B-Instruct, LoRA 병합) | 비공개 |
| Language (문서상) | Korean 명시 | 카드에 언어 목록 미명시 (태그 English, Qwen2.5 계열은 다국어) | **English only 명시** — 한국어는 공식 지원 범위 밖 | 다국어 |
| Benchmark (문서상) | 공개 수치 없음 | 카드에 수치 없음 (공식 블로그 참조 안내) | SAM-Bench 90.55/100 (719 태스크) | 비공개 |
| License | Meta Llama 3 Community (base: Llama 3.1 Community) | Apache-2.0 | Apache-2.0 | 제공자 이용약관 |
| 문서상 최대 Context | 131,072 | 32,768 | 32,768 | 비공개 |
| 실험에 사용한 Context | 4,096 (`num_ctx`) | 4,096 | 4,096 | **요청에 미지정** |
| Quantization | Q4_K_M | Q4_K_M | Q4_K_M (Ollama 보고: unknown) | 해당 없음 |
| VRAM (관측 시점) | 5,027.5 MiB (n=20) | 4,528.1 MiB (n=20) | 4,528.1 MiB (n=20) | 해당 없음 (외부 API) |
| 다운로드 크기 | 4.58 GB | 4.36 GB | 4.36 GB | 해당 없음 |
| 주요 특징 | 한국어 금융 Q&A 특화, BC Card 금융 데이터 Fine-tuning | 코드 생성·수정·설명 특화, 한국어 프롬프트 가능 | 커머스 특화(상품 검색·추천·비교·리뷰 요약), Qwen2.5-7B-Instruct 기반 | 상용 Cloud API 모델 |
| Model Card (GGUF) | [featherless-ai-quants/…](https://huggingface.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF) | [bartowski/…](https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF) | [mradermacher/sam-1-base-GGUF](https://huggingface.co/mradermacher/sam-1-base-GGUF) | — |
| Model Card (원본) | [BCCard/…](https://huggingface.co/BCCard/Llama-3.1-Kor-BCCard-Finance-8B) | [Qwen/…](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | [snapcart-ai/sam-1-base](https://huggingface.co/snapcart-ai/sam-1-base) | [단가 페이지](https://developers.openai.com/api/docs/pricing) |
| 실제 모델 태그 | `hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M` | `hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` | `hf.co/mradermacher/sam-1-base-GGUF:Q4_K_M` | `gpt-5.6-luna` |
| digest (식별값) | `3dc693e518d8` | `f218460127af` | `90130fbbb57b` | 해당 없음 |

**부가 테스트 3개** — 채점·선정 대상은 아니지만 실행 기록과 성능 측정값은 남아 있다.

| 라벨 | 도메인 | Model Name | 제외 사유 |
|---|---|---|---|
| A | 법률 | Llama-3.1-Korean-8B-Instruct-Law-GGUF | 20/20 회 `done_reason=length`, 12회 특수토큰 노출 — 정상 조건 채점 불가 |
| B | 의료·바이오 | KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF | 20회 중 14회 통계 필드 결측 — 같은 n 으로 비교 불가 |
| E | 수학 | Math-IIO-7B-Instruct-GGUF | 문제 없음. 범위를 좁히기 위해 이번 회차에서만 제외 (사이드 비교용) |

> **문서상 최대 Context ≠ 실험 Context** — 세 후보 모두 실험에서는 `num_ctx=4096` 을 썼다.
> `doc_max_context`·Architecture·Language·Benchmark 의 출처는 [step03.md](steps/step03.md) 와
> [`environment.json`](../data/env/environment.json) 에 모델별로 적었다.
> A·B·E 의 문서상 Context 와 조사 항목은 확인하지 않았다(부가 테스트라 판정에 쓰지 않는다).
>
> **F 의 Language 는 실측과 어긋난다.** 모델 카드는 English only 를 명시하는데
> 실측 한국어 표현 점수는 4.15 로 세 후보 중 가장 높았다. base 인 Qwen2.5-7B-Instruct 의
> 다국어 능력을 상속한 것으로 보이며, **필수 조건 1(한국어 가능) 판정은 문서가 아니라
> 실측 근거로 내렸다.** 공식 지원 언어가 아니므로 향후 모델 업데이트에서 한국어 성능이
> 보장되지 않는다는 운영 리스크가 남는다.

## 3) Model Test / Benchmark 결과

**원본 기록**

| 파일 | 형식 | 건수 |
|---|---|---|
| [`data/raw/local/runs.jsonl`](../data/raw/local/runs.jsonl) | JSONL | 126건 (본 실험 120 + 워밍업 6) |
| [`data/raw/cloud/runs.jsonl`](../data/raw/cloud/runs.jsonl) | JSONL | 5건 |
| [`docs/eval-results.md`](eval-results.md) | Markdown (채점 입력면) | 60블록 |
| [`docs/cloud-compare.md`](cloud-compare.md) | Markdown (Cloud 채점면) | 5블록 |
| [`data/derived/scores.jsonl`](../data/derived/scores.jsonl) | JSONL (채점 결과 추출) | 65건 |

**요구 항목 포함 여부**

| 항목 | 어디에 있는가 |
|---|---|
| Prompt / Response | `runs.jsonl` 의 `prompt` · `response_text`, 읽기용 [`data/derived/responses/Q01~Q10.md`](../data/derived/responses/) |
| Latency (전체 응답 시간) | `elapsed_sec` |
| VRAM Usage | `size_vram_mib` (`client.ps()` 바이트 → MiB) |
| 품질 평가 · 점수 근거 | `eval-results.md` 각 블록의 기준별 점수 + `근거` 줄 |
| 질문 ID / 실행 ID / 반복 회차 | `question_id` · `run_id`(`C_Q01_r1` 형식) · `repeat` |
| 실행 설정 | `options` (`temperature` 0 / `num_predict` 768 / `num_ctx` 4096 / `seed` 0), `settings_version` |
| 성공 · 오류 상태 | `status`, `error_type`, `error_message`, `done_reason` |
| 워밍업 여부 | `phase` (`main` / `warmup` / `retry` / `extra`) — 집계는 `main` 만 |
| 로딩 시간 | `load_duration_sec` (`load_duration` ÷ 1e9) |
| 출력 토큰 수 | `eval_count` |
| 생성 속도 | `tokens_per_sec` (`eval_count` ÷ (`eval_duration` ÷ 1e9)) |
| 실패 사례 | [`step06.md`](steps/step06.md) `실패 / 측정 누락`, [`step08.md`](steps/step08.md) `개선이 필요한 실패 사례` |
| 호출 성공 수 / 전체 시도 수 | [`local_summary.md`](../data/derived/tables/local_summary.md) 첫 행 — 3개 모두 **20/20** |
| 지표별 집계 응답 수(n) | 같은 표의 모든 칸에 `(n=…)` 표기 |

**측정 결과 — 비교 대상 3개 (본 실험만, phase=main)**

| 지표 | Model C (금융) | Model D (코딩) | Model F (이커머스) |
|---|---|---|---|
| 호출 성공 / 전체 시도 | 20 / 20 | 20 / 20 | 20 / 20 |
| 평균 전체 응답 시간 | 2.89s (n=20) | 4.05s (n=20) | 3.33s (n=20) |
| 평균 로딩 시간 | 0.21s (n=20) | 0.21s (n=20) | 0.20s (n=20) |
| 평균 출력 토큰 수 | 158.4 (n=20) | 252.0 (n=20) | 187.1 (n=20) |
| 평균 생성 속도 | 61.13 t/s (n=20) | 66.97 t/s (n=20) | 61.58 t/s (n=20) |
| VRAM (관측 시점) | 5,027.5 MiB (n=20) | 4,528.1 MiB (n=20) | 4,528.1 MiB (n=20) |
| **품질 평균** | **2.31 (n=72)** | **3.00 (n=72)** | **3.65 (n=72)** |

**품질 점수 — 기준별**

| 평가 기준 | 출제 문항 | C | D | F | n (모델당 점수 수) |
|---|---|---|---|---|---|
| A 답변 적합성 | Q01~Q10 (10문항) | 1.70 | 3.10 | **3.70** | 20 = 10문항 × 2회 |
| B 논리성/실용성 | Q05 제외 9문항 | 1.78 | 2.83 | **3.28** | 18 = 9문항 × 2회 |
| C 한국어 표현 | Q01~Q10 (10문항) | 3.35 | 3.15 | **4.15** | 20 = 10문항 × 2회 |
| D 지시사항 준수 | Q03·Q06·Q08 (형식 지정 문항) | 3.67 | 3.67 | 3.67 | 6 = 3문항 × 2회 |
| E 정보 부족/불확실성 대응 | Q04·Q05·Q09·Q10 (정보 부족·경계 문항) | 1.38 | 2.25 | **3.12** | 8 = 4문항 × 2회 |

> **`n` = 그 기준으로 매겨진 모델당 개별 점수의 개수**다. 기준마다 출제 문항이 달라
> `n` 이 다르다 — 형식을 지정하지 않은 문항에 D(지시사항 준수)를 매기지 않는 식이다.
> 품질 평균 `n=72` 는 위 다섯 개를 모두 합친 수(20+18+20+6+8)이며, 문항이 많은
> A·C 가 D·E 보다 더 크게 반영된다.
>
> 문항별·사례 유형별·Run 간 일관성 집계는 [`local_summary.md`](../data/derived/tables/local_summary.md) 에 있다.

**측정 불가 처리**

| 사례 | 처리 |
|---|---|
| Model B 20회 중 14회 통계 필드 결측 | 해당 지표의 평균·n 에서 제외하고 사유를 [`step06.md`](steps/step06.md) `실패 / 측정 누락` 에 기록 |
| Cloud 생성 속도 | 내부 생성 시간이 응답에 없어 **계산하지 않음** (`tokens/s` 공란) |
| 첫 토큰 지연(TTFT) | 측정하지 않았으므로 전체 응답 시간을 TTFT 로 표기하지 않음 |

## 4) Local LLM vs Cloud API 비교

**서술 원문**: [`docs/steps/step07.md`](steps/step07.md)
**채점면**: [`docs/cloud-compare.md`](cloud-compare.md)
**생성물**: [`data/derived/tables/local_cloud.md`](../data/derived/tables/local_cloud.md)

Cloud 는 공통 5문항(Q01·Q04·Q06·Q09·Q10)을 **각 1회**, 로컬은 같은 문항을 **각 2회** 실행했다.
아래 Local 열은 최종 선정 모델 F 의 **공통 5문항 기준** 값이다(10문항 전체 평균 3.65와 다르다).

| 비교 축 | Local (Model F) | Cloud (GPT LUNA) | 구분 |
|---|---|---|---|
| **품질** | 3.50 (5문항) | **4.53** (5문항) | 둘 다 실측. Cloud 우위 |
| **속도** | **3.86s** | 6.97s | 둘 다 실측. **Cloud 값에는 네트워크 왕복 포함** — 모델 자체 속도 비교 아님 |
| **비용** | API 과금 없음 | 추정 **$0.0029544** (5회 합산 / 평균 $0.0005909) | Cloud 는 토큰 × 단가 추정치. **실제 청구액 아님** |
| **보안** (STEP 1 중요 제약) | 문의가 내부에 머문다. 접근 제어·패치·로그는 운영자 책임 | **문의 원문이 외부 API 로 전송됨.** 개인정보 비식별화·최소화와 제공자 정책 검토가 선행돼야 함 | 운영 조건 분석 (실측 아님) |
| **인프라** | GPU·PC 확보, 모델 다운로드·저장·업데이트·서빙을 직접 관리 | 자체 GPU 불필요. 인터넷 연결·API 장애·사용량 관리 필요 | 운영 조건 분석 |
| **운영 난이도** | 장비·모델·서빙 관리 부담 | 인프라 부담 낮음, API 의존 | 운영 조건 분석 |
| **커스터마이징** | 모델 선택·양자화·내부망 배치 가능 (이번엔 Fine-tuning 미수행) | 제공 모델·API 범위에 의존 | 운영 조건 분석 |

**Cloud 실행 기록 5건**

| run_id | 상태 | 입력 토큰 | 출력 토큰 | 응답 시간 | 추정 비용 | 품질 |
|---|---|---|---|---|---|---|
| `CLOUD_Q01_r1` | completed | 37 | 433 | 7.78s | $0.000527 | 4.67 |
| `CLOUD_Q04_r1` | completed | 44 | 380 | 5.03s | $0.000465 | 4.50 |
| `CLOUD_Q06_r1` | completed | 38 | 303 | 4.47s | $0.000371 | 4.50 |
| `CLOUD_Q09_r1` | completed | 35 | 547 | 8.15s | $0.000663 | 5.00 |
| `CLOUD_Q10_r1` | **incomplete** | 32 | **768** (한도 도달) | 9.42s | $0.000928 | 4.00 |
| **합계** | 5/5 성공 | **186** | **2,431** | — | **$0.0029544** | 평균 4.53 |

단가: 입력 $0.2 / 1M, 출력 $1.2 / 1M (USD, Standard). 출처 [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing), 확인일 2026-09-16.

**동일하지 않은 조건**

| 축 | Local | Cloud | 상태 |
|---|---|---|---|
| 반복 수 | 질문당 2회 | 질문당 **1회** | **차이** — 로컬은 2회 평균을 쓰고, 좋은 회차만 골라 비교하지 않았다 |
| Temperature | 0 | 0 (요청에 전달됨) | 동일 |
| 최대 출력 | `num_predict` 768 | `max_output_tokens` 768 | 동일 (토크나이저는 다름) |
| Context 창 | `num_ctx` 4096 | 요청에 지정 불가 | **차이** |
| seed | 0 | 요청에 지정 불가 | **차이** |

## 5) 최종 Model Selection Report

**원문**: [`docs/steps/step08.md`](steps/step08.md)

### 선정 결과

**Model F (이커머스 특화, `sam-1-base` Q4_K_M)** — 필수 통과 조건 7개를 모두 충족한 유일한 후보.

### 요구사항 → 평가 항목 → 실험 기록 → 선택·탈락 이유

| STEP 1 요구사항 | STEP 2 평가 항목 | STEP 6~7 실험 기록 | 선정에 미친 영향 |
|---|---|---|---|
| 정보가 없으면 지어내지 않기 | 기준 **E** · 선호 우선순위 **1위** | F 3.12 / D 2.25 / C 1.38 (n=8) | **F만 3점대.** 정보 부족 사례에서 C·D 는 나란히 1.67로 실패 |
| 질문 의도 정확 파악 | 기준 **A**+**B** · 우선순위 2위 | A: F 3.70 / D 3.10 / C 1.70 · B: F 3.28 / D 2.83 / C 1.78 | F 우위 |
| 한국어 성능 중요 | 필수 조건 1 · 기준 **C** · 우선순위 3위 | F 4.15 / C 3.35 / D 3.15 (n=20) | F 우위 |
| 응답 속도 중요 | 필수 조건 7 (평균 5초 이내) | C 2.89s / F 3.33s / D 4.05s | 3개 모두 Pass — 변별 없음 |
| 상업적 활용 | 필수 조건 4 | F·D Apache-2.0 / C Llama 커뮤니티(조건부) | F 유리 |
| 8GB VRAM 제약 | 필수 조건 3 · 우선순위 5위 | F·D 4,528 MiB / C 5,027 MiB | F·D 동일, C 열세 |
| 최소 품질 | 필수 조건 6 (평균 3.5 이상) | **F 3.65 Pass / D 3.00 Fail / C 2.31 Fail** | **결정적 — 통과 후보가 F 하나** |

### 필수 통과 조건 판정

| # | 조건 | C | D | F |
|---|---|---|---|---|
| 1 | 한국어 Chat/QA 가능 | Pass (3.35) | Pass (3.15) | Pass (4.15) |
| 2 | Ollama 실행 가능 | Pass (20/20) | Pass (20/20) | Pass (20/20) |
| 3 | 현재 PC에서 안정 실행 | Pass | Pass | Pass |
| 4 | 상업적 활용 가능 License | Pass | Pass | Pass |
| 5 | Context Length | Pass (131,072) | Pass (32,768) | Pass (32,768) |
| 6 | 품질 평균 3.5 이상 | **Fail (2.31)** | **Fail (3.00)** | **Pass (3.65)** |
| 7 | 평균 응답 5초 이내 | Pass (2.89s) | Pass (4.05s) | Pass (3.33s) |
| | **최종** | **Fail** | **Fail** | **Pass** |

### 선택 이유

1. 필수 조건 7개를 모두 통과한 **유일한 후보**이며, 집계 방식을 바꿔도(기준 동일 가중 3.58 / 문항 동일 가중 3.73) 결론이 같다
2. 최우선 기준인 **사실 정확성·추정 방지(E)에서 유일하게 3점대** — 경계 사례에서 D 대비 +41.4%, 정보 부족 사례에서 +84.4%
3. **D를 품질·응답 시간·출력 토큰·VRAM 전 축에서 앞선다** (생성 속도만 8.8% 열세)
4. 토큰 효율 51.3(출력 토큰 ÷ 품질)로 최고 — 간결하게 답하면서 품질이 높다
5. 회차 간 편차 0.01로 재현성이 가장 높고, 라이선스가 Apache-2.0 으로 깔끔하다

### 탈락 이유

| 후보 | 탈락 사유 | 핵심 수치 |
|---|---|---|
| C (금융) | 조건 6 미달. 1순위 기준 E 에서 1.38 — 정보 부족 대응이 사실상 불가능 | 품질 2.31 / E 1.38 / 정보 부족 1.67 |
| D (코딩) | 조건 6 미달. 생성 속도만 우위이고 품질 계열 전 기준에서 F 에 열세 | 품질 3.00 / E 2.25 / 정보 부족 1.67 |

### 한계

| 구분 | 내용 |
|---|---|
| 평가셋 | 질문 10개 × 2회. 기준별 표본 불균형 (A·C 20건 / B 18건 / **E 8건 · D 6건**) — **가장 중요한 1순위 기준의 표본이 가장 작다** |
| 입력 범위 | 프롬프트에 상품 상세페이지 정보를 넣지 않고 물었다. **제공된 정보를 정확히 인용하는 능력은 검증되지 않았다** — 실제 운영 형태로 재평가 필요 |
| 장비 | VRAM 8GB 노트북 GPU · Q4_K_M 고정. 다른 환경에서는 속도·자원 수치가 달라진다 |
| 비교 범위 | 6개 중 3개만 채점. 도메인 전이 결론의 표본이 3개뿐 |
| Cloud | 질문당 1회(n=1)라 실행 간 변동을 확인하지 못했다 |
| 조건 7 | STEP 8 검토 중 **사후 추가**한 조건. 실험 전 확정이 아니며 세 후보 모두 통과해 판별력이 없었다 |
| 조건 1 | 사전 등록된 정량 통과선 없음. 특수토큰 오염 여부로 판단한 해석적 기준 |
| 비용 | 토큰 × 단가 추정치. 실제 청구 내역과 대조하지 않았다 |
| 라이선스 | "확인 완료"는 문서 확인 수준이며 법무 검토가 아니다 |

### 개선이 필요한 실패 사례

| 사례 | Model F | 참고 | 문제 |
|---|---|---|---|
| 정보 부족 사례 유형 (n=4) | **3.08** | C 1.67 / D 1.67 | 정상 사례(3.97)보다 0.89점 낮다 |
| Q10 데이터 부족 판매 문제 | **2.50** (최저 문항) | Cloud 4.00 (`incomplete`) | **어느 모델도 "어떤 상품인지" 되묻지 않았다** |
| 기준 E 불확실성 대응 (n=8) | **3.12** | C 1.38 / D 2.25 | 1순위 기준인데 5점 만점 중간 수준 |

### Local–Cloud 운영 방식 권고

Cloud 가 공통 5문항에서 더 높은 품질(4.53 vs 3.50)을 보였지만, **최종 선정은 로컬 후보 중에서만** 했다.
Cloud 결과는 아래 운영 권고의 근거로만 쓴다.

STEP 1 이 **데이터 보안을 중요 제약으로 정의**했다 — 고객 문의에 주문번호·연락처·배송지
같은 개인정보가 섞여 들어올 수 있다. 품질이 높아도 **문의 원문을 외부 API 로 내보내는
경로**라는 점이 함께 걸린다.

| 문의 유형 | 처리 위치 | 근거 |
|---|---|---|
| 일반 상품 문의 (정상 사례) | **Local F** | F 3.97로 충분, API 과금 0, 응답 3.86s, 문의가 외부로 나가지 않음 |
| 경계 사례 (책임 소재 불명확 등) | **Local F + 사람 검수** | F 3.62로 대응 가능하나 오답 시 영향이 크다 |
| 정보 부족 사례 (F 의 최약점) | **상담원 연결** | F 3.08 / Cloud 4.00 이지만, 고객이 주문·배송 정보를 덧붙이기 쉬워 **개인정보 노출 위험이 가장 큰 구간** |
| 대량·상시 트래픽 | **Local F** | Cloud 는 호출당 과금이 누적되고 전송량도 늘어난다 |

**Cloud 사용 범위** — 고객 문의 원문을 보내는 용도로는 권장하지 않는다. 개인정보가
들어가지 않는 작업(셀러용 FAQ 초안, 상품 설명 문구 다듬기 등)에 한정하고, 그 경우에도
제공자의 데이터 처리·보관 정책을 먼저 확인한다.

> 보안 제약은 **선정 결론을 바꾸지 않는다.** 필수 조건 7개는 로컬 후보 간 판정 기준이고
> 데이터 통제 수준은 C·D·F 가 같다. 보안은 로컬 우선 처리의 근거이자 Cloud 사용 범위를
> 제한하는 조건으로 작용한다.

**도입 판단**: 조건부 가능. 전면 자동화는 권장하지 않는다 — 통과 여유가 +0.15(기준 동일 가중 시 +0.08)로 얇고
E 점수가 3.12다. "확인되지 않은 정보는 단정하지 않는다"는 지시를 프롬프트에 명시하고,
확인 불가 시 상담원 전환 경로를 두는 안전장치가 필요하다.

---

# 8. 필수 완료 기준과 평가표

## 프로젝트 수행 평가표

- [x] 사용 사례와 모델 요구사항, 로컬 후보의 정보·출처·실행 조건을 정의했습니다.
      → [step01.md](steps/step01.md) · [step02.md](steps/step02.md) · [step03.md](steps/step03.md)
- [x] 고정 질문 10개를 로컬 모델에 각각 2회 적용하고 원본 응답·측정값·실패 기록을 저장했습니다.
      → `data/raw/local/runs.jsonl` 126건 (본 실험 120 + 워밍업 6)
- [x] 동일 품질 기준으로 평가하고 점수 근거·대표 실패 사례를 설명했습니다. 평균과 성공 수/전체 시도 수, 지표별 n을 표시했습니다.
      → [eval-results.md](eval-results.md) 60블록 · [local_summary.md](../data/derived/tables/local_summary.md)
- [x] Cloud 모델 1개에 공통 질문 5개를 적용하고 응답·측정값·토큰 사용량·비용을 기록했습니다.
      → `data/raw/cloud/runs.jsonl` 5건 · [cloud-compare.md](cloud-compare.md) · [step07.md](steps/step07.md)
- [x] 필수 통과 조건과 선호 우선순위에 따라 최종 로컬 모델 1개를 선정했습니다.
      → [step08.md](steps/step08.md) — **Model F**
- [x] GitHub 저장소와 README를 정리하고 재실행 결과를 확인했습니다.
      → 저장소·README 정리 완료 · [step04.md](steps/step04.md) `재실행 확인 기록` (2026-09-17)

## 요구사항 평가표

> **충족** — 필요한 작업과 증빙이 있고 결과를 설명할 수 있다
> **보완 필요** — 작업은 했지만 기록·비교 조건·설명의 일부가 부족하다
> **미수행** — 작업을 하지 않았거나 확인할 증빙이 없다

| # | 요구사항 | 평가 관점 | 판정 | 근거 위치 |
|---|---|---|---|---|
| 1 | 문제·요구사항 정의 | 모델 선정 기준이 실험 전에 명확한가 | **충족** | [step01.md](steps/step01.md) · [step02.md](steps/step02.md). 사용 사례·제약조건과 **필수 조건 1~6, 통과선 3.5를 본 실험(120회) 전에 확정**(통과선은 `questions.json` 에 값으로 고정). 이후 조정한 둘은 시점을 함께 적었다 — **조건 7은 STEP 8 검토 중 추가**, **선호 우선순위의 순서는 채점 도중 조정**(필수 조건·통과선·채점 기준·질문 세트는 불변이라 Pass/Fail 에 영향 없음) |
| 2 | 후보 모델 조사 | Use Case·실행 환경에 맞는 서로 다른 후보를 선정했는가 | **충족** | [step03.md](steps/step03.md) · [model_comparison.md](../data/derived/tables/model_comparison.md). 도메인이 다른 6개(법률·의료·금융·코딩·수학·이커머스), Model Card·License 출처·태그·digest·문서상 Context 기록 |
| 3 | 실행 환경·기록 확인 | 실제 환경에서 재현 가능하게 실행했는가 | **충족** | [step04.md](steps/step04.md) 모델별 연결 확인 · [environment.json](../data/env/environment.json) 자동 수집(GPU·VRAM·RAM·패키지 버전) · `01_ollama_chat.py` 단발 호출 |
| 4 | 평가 질문·기준 확정 | 모델마다 공정한 비교 조건을 통제했는가 | **충족** | [step05.md](steps/step05.md) · [questions.json](../data/config/questions.json). 질문 10개(정상 6·경계 2·정보 부족 2), 기준 A~E 정의, **Cloud용 5문항을 결과 보기 전에 `cloud_compare=true` 로 확정** |
| 5 | 로컬 비교 실험 | 필수 반복 횟수와 동일 조건을 지키고 실패도 기록했는가 | **충족** | `runs.jsonl` 126건 — 본 실험 120회(6모델×10문항×2회), 워밍업 6회를 `phase` 로 분리. 호출 성공 120/120, 지표별 n 표기, 측정 누락은 0으로 채우지 않고 사유 기록 |
| 6 | 품질 평가·해석 | 점수와 원본 응답 근거·한계를 함께 설명했는가 | **충족** | [eval-results.md](eval-results.md) 60블록 전건 채점 + `근거` 줄 + **재검토 완료** · 문항별 관찰 메모 · [step06.md](steps/step06.md) 실패/측정 누락 구분 |
| 7 | Local–Cloud 비교 | 품질·비용·보안·운영·인프라·커스터마이징을 비교했는가 | **충족** | [step07.md](steps/step07.md) 6개 축 전부 작성, 반복 수 차이(2회 vs 1회)·Cloud 응답 시간의 네트워크 포함 사실 명시, 실측과 운영 조건 분석 구분. 비용은 **토큰 × 단가 추정치이며 실제 청구액이 아니라는 점을 기록마다 구분해 표기**(발제문 요구는 추정과 실제 사용 내역의 *구분*) |
| 8 | 최종 선정·발표 | 요구사항과 실측 근거를 연결해 합리적으로 결정했는가 | **충족** | [step08.md](steps/step08.md). 필수 조건 판정 → 우선순위 → 선정, 탈락 사유·한계·실패 사례·운영 권고 구분 서술 |
| 9 | 제출·재실행 확인 | 제3자가 실험 흐름과 결과를 이해·재현할 수 있는가 | **충족** | 저장소 하나에 코드·환경·질문·원본 기록·비교표·선정 근거 집결, [README](../README.md) 에 실행 방법·파일 위치 정리. 재실행 확인 기록은 [step04.md](steps/step04.md) `재실행 확인 기록` (2026-09-17, 검사·집계 재생성·모델 호출·단위 테스트) |

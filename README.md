# 오픈소스 LLM 비교·선정 프로젝트

이커머스 고객 문의·셀러 업무 질문에 답변할 로컬 LLM 후보를 비교하고 1개를 선정한다.

- 사용 사례와 요구사항: [docs/steps/step01.md](docs/steps/step01.md), [step02.md](docs/steps/step02.md)
- 장기 로드맵: [docs/roadmap.md](docs/roadmap.md)
- 산출물 체크리스트: [docs/deliverables.md](docs/deliverables.md)

## 실험 규모

| 구분 | 규모 |
|---|---|
| 로컬 본 실험 | 모델 6개 (A~F) × 질문 10개 × 각 2회 = 120회 |
| 워밍업 | 모델당 1회 (본 집계에서 분리) |
| Cloud 비교 | 모델 1개 × 공통 질문 5개 × 각 1회 |

A·F는 CLI 사전 확인에서 문제가 보였으나 본 실험 결과로 판정한다 — [docs/eval-results.md](docs/eval-results.md)

---

## 파일 위치 안내

### 실행 코드

| 경로 | 내용 |
|---|---|
| `project1-python-start/src/evalkit/config.py` | 경로 상수, 설정 로더, `run_id` 생성 |
| `project1-python-start/src/evalkit/schema.py` | 레코드 필드 정의 |
| `project1-python-start/src/evalkit/recorder.py` | 레코드 생성 / append 저장 / 중복 `run_id` 검사 |
| `project1-python-start/src/evalkit/validator.py` | 저장된 파일 재검증 |
| `project1-python-start/src/evalkit/aggregator.py` | 원본에서 집계 계산 |
| `project1-python-start/src/evalkit/exporter.py` | 집계 결과 → 마크다운 표 |
| `project1-python-start/src/evalkit/run_local.py` | 로컬 실험 실행 |
| `project1-python-start/src/evalkit/run_cloud.py` | Cloud 실험 실행 |
| `project1-python-start/src/evalkit/collect_env.py` | 실행 환경 자동 수집 |
| `project1-python-start/src/evalkit/peek.py` | 기록 훑어보기 / 진행 상황 |
| `project1-python-start/10_run.py` | **모델 하나 실행 + STEP 04/06 출력** |
| `project1-python-start/11_finish.py` | 검사 · 채점 준비 · 집계 · 표 생성 |
| `project1-python-start/src/evalkit/report.py` | STEP 04/06 형식 출력 |
| `project1-python-start/src/evalkit/scoring.py` | `eval-results.md` 채점 읽기 |
| `project1-python-start/0*.py`, `99_*.py` | 모델별 단발 호출 예제 (수동 확인용) |

### 입력 (1회 작성 후 고정)

| 경로 | 내용 |
|---|---|
| `data/config/run_settings.json` | 모든 모델에 동일 적용하는 실행 설정 |
| `data/config/models.json` | 대상 모델 목록, 제외 모델, Cloud 모델·단가 |
| `data/config/questions.json` | 질문 10개 (원본: `docs/steps/step05.md`) |
| `data/env/environment.json` | OS / 런타임 / 패키지 / GPU / 모델 제원 |

### 원본 기록 (append 전용 — 수정·삭제하지 않는다)

| 경로 | 내용 |
|---|---|
| `data/raw/local/runs.jsonl` | 로컬 실행 1회 = 1줄. 원본 응답 + 측정값 + 설정 |
| `data/raw/cloud/runs.jsonl` | Cloud 실행 1회 = 1줄. 응답 + 토큰 사용량 + 추정 비용 |

### 생성물 (언제든 재생성 가능)

| 경로 | 내용 |
|---|---|
| `data/derived/local_summary.json` | 로컬 집계 + 품질 집계 (기여 `run_id` 포함) |
| `data/derived/cloud_summary.json` | Cloud 집계 |
| `data/derived/tables/model_comparison.md` | 산출물 2 — 제원 비교표 |
| `data/derived/tables/local_summary.md` | 산출물 3 — 성능·품질 집계표 |
| `data/derived/tables/local_cloud.md` | 산출물 4 — Local vs Cloud |
| `data/derived/step04.md` | STEP 04 절 (모델마다 누적) |
| `data/derived/step06.md` | STEP 06 성능 표 (전체 모델) |

### 문서

| 경로 | 내용 |
|---|---|
| `docs/steps/step01~08.md` | 단계별 작업 기록 |
| `docs/eval-results.md` | **품질 채점 입력면** — 점수와 근거를 여기에 적는다 |
| `docs/deliverables.md` | 산출물 인덱스 / 제출 체크리스트 |
| `docs/usage.md` | **상세 사용법** — 설정값 의미, MODE별 설명, 문제 상황 |
| `docs/data-flow.md` | 파일 간 연동과 역추적 경로 |

### 저장소에 없는 것

모델 가중치 파일, API 키, `.venv/` — 루트 `.gitignore` 로 제외한다.
모델은 아래 태그로 직접 내려받는다.

```bash
ollama pull hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M
ollama pull hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M
ollama pull hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
ollama pull hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M
```

---

## 실행 방법

### 환경 준비

```bash
cd project1-python-start
uv sync
```

Ollama 앱도 실행해 둔다.

### 실행 순서

파일은 두 개뿐이다.

| 파일 | 언제 | 바꿀 값 |
|---|---|---|
| `10_run.py` | 모델마다 | `MODEL`, `LIMIT` |
| `11_finish.py` | 80회를 다 채운 뒤 한 번 | 없음 |

```bash
cd project1-python-start
uv run python 10_run.py
```

`10_run.py` 는 실행한 뒤 진행 상황과 함께
**STEP 04 / STEP 06 문서에 그대로 붙일 수 있는 표**를 출력한다.

### 모델 하나씩 도는 흐름

실험 시작 전에 `data/config/run_settings.json` 을 채운다.
비어 있으면 `10_run.py` 가 무엇이 빠졌는지 알려주고 실행을 거부한다.

1. `MODEL = "B"`, `LIMIT = 3` 으로 실행
   출력에서 **VRAM 이 `집계 불가` 면 멈추고 `keep_alive` 를 확인한다**
2. 문제없으면 `LIMIT = None` 으로 바꿔 재실행 (기록된 회차는 건너뜀)
3. `MODEL` 을 `"B"`…`"F"` 로 바꿔 1~2 반복
4. 120회를 채우면 `11_finish.py` 실행
5. `docs/eval-results.md` 에 점수·근거를 채우고 `11_finish.py` 재실행

각 설정값의 의미와 문제 상황별 대처는 [docs/usage.md](docs/usage.md) 참조.

### Cloud 비교 (STEP 7)

```bash
uv run python -m evalkit.run_cloud
```

`cloud_compare=true` 인 질문 5개를 각 1회 호출한다.
API 키는 실행 시점에 입력받고 어떤 파일에도 저장하지 않는다.

## 기록 규칙

이 규칙들은 코드가 강제하며 `validator` 가 검사한다.

1. 측정하지 못한 값은 `0` 이 아니라 `null` + `measurement_notes` 에 사유
2. 호출 실패(`status="error"`) / 지표 측정 누락(값만 `null`) / 품질 미달(채점 결과)은 서로 다른 축
3. 워밍업은 기록하되 기본 집계에서 제외
4. 재시도는 별도 `run_id` 를 받으며 원래 실패 기록을 덮어쓰지 않음
5. `run_id` 중복 시 건너뛰고 경고
6. 원본 기록 파일은 append 모드로만 연다

측정값 출처와 단위:

| 지표 | 출처 | 변환 |
|---|---|---|
| `elapsed_sec` | 요청 직전 ~ 응답 수신 직후 | 초 (TTFT 아님) |
| `load_duration_sec` | `response.load_duration` | ns ÷ 1e9 |
| `tokens_per_sec` | `response.eval_count` / (`response.eval_duration` / 1e9) | — |
| `prompt_eval_count` | `response.prompt_eval_count` | 입력 토큰 수 |
| `size_vram_mib` | `client.ps()` 의 `size_vram` | bytes ÷ 1,048,576 |
| `processor` | `size` 와 `size_vram` 비율 | `size_vram==size` → 100% GPU |
| `done_reason` | `response.done_reason` | `length` 면 출력 한도에서 잘림 |

`size_vram` 은 관측 시점의 값이며 최대 VRAM 이 아니다.
`processor` 는 CPU/GPU 적재 상태이며 GPU 이용률이 아니다.
`quantization_level` 은 `ps()` 가 `unknown` 을 돌려줄 수 있으므로 비교표에는 모델 태그 기준값을 함께 적는다.
`done_reason="length"` 인 응답은 잘린 답변이므로 품질 채점 시 "내용 부족"과 구분한다.

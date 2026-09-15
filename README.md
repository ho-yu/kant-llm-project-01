# 오픈소스 LLM 비교·선정 프로젝트

이커머스 고객 문의·셀러 업무 질문에 답변할 로컬 LLM 후보를 비교하고 1개를 선정한다.

- 사용 사례와 요구사항: [docs/steps/step01.md](docs/steps/step01.md), [step02.md](docs/steps/step02.md)
- 장기 로드맵: [docs/roadmap.md](docs/roadmap.md)
- 산출물 체크리스트: [docs/deliverables.md](docs/deliverables.md)

## 실험 규모

| 구분 | 규모 |
|---|---|
| 로컬 본 실험 | 모델 4개 (B/C/D/E) × 질문 10개 × 각 2회 = 80회 |
| 워밍업 | 모델당 1회 (본 집계에서 분리) |
| Cloud 비교 | 모델 1개 × 공통 질문 5개 × 각 1회 |

제외한 후보와 사유: [docs/eval-results.md](docs/eval-results.md) '제외된 모델' 절

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
| `project1-python-start/0*.py`, `99_*.py` | 모델별 단발 호출 예제 |

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
| `data/scoring/scores.jsonl` | 품질 채점. `run_id` 로 실행 기록과 연결 |

### 생성물 (언제든 재생성 가능)

| 경로 | 내용 |
|---|---|
| `data/derived/local_summary.json` | 로컬 집계 + 품질 집계 (기여 `run_id` 포함) |
| `data/derived/cloud_summary.json` | Cloud 집계 |
| `data/derived/tables/model_comparison.md` | 산출물 2 — 제원 비교표 |
| `data/derived/tables/local_summary.md` | 산출물 3 — 성능·품질 집계표 |
| `data/derived/tables/local_cloud.md` | 산출물 4 — Local vs Cloud |

### 문서

| 경로 | 내용 |
|---|---|
| `docs/steps/step01~08.md` | 단계별 작업 기록 |
| `docs/eval-results.md` | 문제별 채점 블록 (사람이 읽는 형태) |
| `docs/deliverables.md` | 산출물 인덱스 / 제출 체크리스트 |
| `docs/data-flow.md` | **파일 간 연동과 역추적 경로** |

### 저장소에 없는 것

모델 가중치 파일, API 키, `.venv/` — 루트 `.gitignore` 로 제외한다.
모델은 아래 태그로 직접 내려받는다.

```bash
ollama pull hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M
ollama pull hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M
ollama pull hf.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
ollama pull hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M
```

---

## 실행 방법

### 환경 준비

```bash
cd project1-python-start
uv sync
uv run python --version
```

Python 3.12.x 가 나오면 준비된 것이다. Ollama 앱도 실행해 둔다.

### 실험 실행

아래 명령은 모두 `project1-python-start/src` 에서 실행한다.

```bash
python -m evalkit.run_local --dry-run
```

호출 없이 실행 계획만 출력한다.

```bash
python -m evalkit.run_local
```

모델을 하나씩 올려 워밍업 1회 + 질문 10개 × 2회를 실행하고 `data/raw/local/runs.jsonl` 에 append 한다.
중단해도 다시 실행하면 이미 기록된 `run_id` 는 건너뛰고 이어서 진행한다.

```bash
python -m evalkit.run_cloud
```

`cloud_compare=true` 인 질문 5개를 각 1회 호출한다. API 키는 실행 시점에 입력받고 어떤 파일에도 저장하지 않는다.

### 검증과 집계

```bash
python -m evalkit.validator
```

저장된 JSONL 을 다시 열어 파싱·필드 누락·`run_id` 중복·규칙 위반·실험 커버리지를 검사한다.

```bash
python -m evalkit.aggregator
python -m evalkit.exporter
```

원본에서 집계를 계산하고 마크다운 표를 만든다. `data/derived/` 는 지워도 이 두 명령으로 복원된다.

---

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
| `size_vram_mib` | `client.ps()` 의 `size_vram` | bytes ÷ 1,048,576 |

`size_vram` 은 관측 시점의 값이며 최대 VRAM 이 아니다.
`processor` 는 CPU/GPU 적재 상태이며 GPU 이용률이 아니다.

# 사용법

실행 파일은 네 개다.

| 파일 | 언제 | 바꿀 값 |
|---|---|---|
| `10_run.py` | 모델마다 | `MODEL`, `LIMIT` |
| `12_read.py` | 채점 전 / 채점 대상을 바꾼 뒤 | `RESET` (평소 False) |
| `11_finish.py` | 채점하는 동안 수시로 / 다 채운 뒤 한 번 | 없음 |

```bash
cd project1-python-start
uv run python 10_run.py
```

`uv run` 을 반드시 쓴다. 그냥 `python` 으로 돌리면 venv 밖의 인터프리터가 잡혀
`openai` 가 없고, 기록되는 Python 버전도 실제 실험 환경과 달라진다.

---

## 1. 시작 전 준비

### 1-1. 패키지 설치 (최초 1회)

```bash
cd project1-python-start
uv sync
```

Ollama 앱이 실행 중이어야 한다.

### 1-2. `data/config/execution_conditions.json` 채우기

Local·Cloud의 완료된 실험값, 비교 지표, 설정 위치와 보완 항목은
[실험 조건 및 실행 전 점검표](experiment-conditions.md) 한곳에서 확인한다.
현재 `execution_conditions.json`의 768토큰 설정이 완료된 실험의 기준이다.

### 1-3. 환경 정보 수집

`10_run.py` 를 실행하면 매번 자동으로 갱신된다.

OS / Python / Ollama / 패키지 버전, GPU·VRAM·CPU·RAM,
모델별 digest·양자화·다운로드 크기가 `data/env/environment.json` 에 들어간다.

출력 마지막의 **"직접 채워야 하는 항목"** 은 웹에서 확인해야 하는 값들이다.

- `platform.execution_type` — 예: `Local PC`
- 모델별 `model_card_url`, `license_declared`, `license_base_model`, `doc_max_context`

`doc_max_context`(Model Card 문서상 최대 Context)와 실행 기록의
`context_length`(실제 설정값)는 **산출물에서 반드시 구분해서 적어야 하므로**
서로 다른 곳에 저장된다.

---

## 1-4. STEP 04 요구 항목이 어디에 쌓이는가

과제가 STEP 04 에서 기록하라고 한 것과, 그게 어느 파일에 들어가는지.

| STEP 04 요구 항목 | 저장 위치 | 어떻게 |
|---|---|---|
| 모델 전체 태그 | `data/config/models.json` → `model_tag` | 사람이 확정 |
| 모델 식별값 (digest) | `data/raw/local/runs.jsonl` + `environment.json` | **자동** (`client.ps()` / `list()`) |
| Parameter | `environment.json` → `parameter_size` | **자동** (`client.list()`) |
| 양자화 | `environment.json` → `quantization_level` | **자동** (`client.list()`) |
| 다운로드 파일 크기 | `environment.json` → `download_size_bytes` | **자동** (`client.list()`) |
| Python / Ollama / 패키지 버전 | `environment.json` → `runtime` | **자동** |
| GPU / VRAM / CPU / 시스템 RAM | `environment.json` → `hardware` | **자동** |
| 실행 환경 구분 (Local PC vs Colab) | `environment.json` → `platform.execution_type` | 사람이 1회 |
| 실행 설정 | `data/config/execution_conditions.json` → `options` | 사람이 1회, 회차마다 기록에 복사됨 |
| 실험에서 실제 확인한 Context | `runs.jsonl` → `context_length` | **자동** |
| 문서상 최대 Context | `environment.json` → `doc_max_context` | **사람이 Model Card 에서 확인** |
| Model Card / License 출처 | `environment.json` → `model_card_url`, `upstream_model_card_url`, `license_*` | `step03.md` 조사 결과를 옮겨둠 |
| Python 호출 성공 + 결과 1건 저장 후 재확인 | `runs.jsonl` | **자동**, STEP 04 블록에 발췌 출력 |
| CLI 대화 성공 | `docs/eval-results.md` → 'STEP 4 CLI 스모크 테스트' 절 | 사람이 기록 |
| 오류 증상 (미설치 / 연결 실패 등) | `runs.jsonl` → `error_type`, `error_message` | **자동** |

`10_run.py` 를 실행하면 자동 항목이 매번 갱신되고, 사람이 채울 항목이 남아 있으면
"직접 채워야 하는 항목" 으로 목록이 뜬다.

### 결과는 스텝 문서에 직접 써진다

`10_run.py` 를 실행하면 `docs/steps/step04.md` · `step06.md` 의
아래 마커 사이 구간이 매번 다시 계산되어 갈아끼워진다.

```
<!-- evalkit:auto:start — 아래는 자동 생성 구간입니다. 직접 고치지 마세요. -->
...
<!-- evalkit:auto:end -->
```

**마커 밖에 직접 쓴 서술은 건드리지 않는다.** 복사해 붙일 필요도,
두 곳을 오가며 볼 필요도 없다. 마커 안쪽만 수정하지 않으면 된다.

### 지금 남은 수동 항목

`doc_max_context` (모델 6개) 하나뿐이다. GGUF 저장소 카드에 없으면
`environment.json` 의 `upstream_model_card_url` 에 적힌 원본 모델 카드에서 확인한다.

**실험에서 실제 설정한 Context(4096)와 반드시 구분해서 적어야 하는 산출물 요구사항이다.**

## 2. 로컬 실험 — 모델 하나씩

### 2-1. 첫 모델은 몇 건만 먼저

```python
MODEL = "A"     # A~F — 라벨이다. 태그가 아니다
LIMIT = 3       # 먼저 3건만
```

실행이 끝나면 진행 상황과 검사 결과가 자동으로 출력된다.
확인하려고 따로 돌릴 것은 없다.

실행 중에는 회차마다 한 줄씩 값이 나온다. 20회가 끝나기 전에 이상을 알아챌 수 있다.

```
  ok   A_Q02_r1        11.8s    768tok    66t/s    5028MiB  [한도까지 생성]
  ok   A_Q02_r2         4.8s    288tok    61t/s    5028MiB
  ok   A_Q03_r1         5.0s    300tok    60t/s       null  [VRAM 못 읽음 — keep_alive 확인]
  ERR  A_Q03_r2     TimeoutError: 응답 시간 초과
```

- `[한도까지 생성]` — `done_reason=length`. 실패가 아니라 `num_predict` 에 걸린 것
- `[VRAM 못 읽음]` — 응답 직후 `client.ps()` 에서 모델을 못 찾음. **여기서 멈추고 확인한다**
- `ERR` — 호출 실패. 회차를 건너뛰지 않고 `status="error"` 로 기록된다

**여기서 반드시 볼 것**

| 증상 | 원인 | 조치 |
|---|---|---|
| `VRAM=null` | `keep_alive=0` 이라 응답 직후 언로드됨 | 멈추고 `execution_conditions.json` 수정. **기록은 append 전용이라 되돌릴 수 없다** |
| `생성속도=null` | `eval_duration` 이 0 이하이거나 통계 필드 없음 | 사유가 `!` 줄에 나온다 |
| `[ERR]` | 호출 실패 | 예외 종류와 메시지가 같이 나온다. 모델 태그를 먼저 의심한다 |
| `done_reason=length` | `num_predict` 한도에서 잘림 | 실패가 아니다. 채점 시 "내용 부족"과 구분해서 본다 |

### 2-2. 문제없으면 나머지를 채운다

```python
LIMIT = None
```

다시 실행하면 이미 기록된 3건은 건너뛰고 나머지 17건을 채운다.
중간에 Ctrl+C 로 끊어도 되고, 다시 실행하면 이어진다.

### 2-3. 다음 모델

```python
MODEL = "B"     # 이후 "C" … "F"
```

모델은 한 번에 하나만 메모리에 올린다. 한 모델이 끝나면 언로드하고
다음 모델을 올린다. 8GB VRAM 에서 두 개를 동시에 올리지 않기 위해서다.
Model F 는 14B 라 일부 CPU offloading 이 발생할 수 있다.

### 2-4. 진행 상황

`10_run.py` 실행 때마다 함께 출력된다.

```
모델      본실험    성공   실패  워밍업
B        20/20     20     0    있음
C        20/20     19     1    있음
D         0/20      0     0    없음
```

한 회차의 원본 응답 전문은 `data/raw/local/runs.jsonl` 에서 해당 `run_id` 줄을 본다.

---

## 3. 채점

**`docs/eval-results.md` 에 직접 적는다.** 별도 파일은 없다.

원본 응답은 `runs.jsonl` 에 한 줄짜리 JSON 으로 들어 있어 눈으로 읽기 어렵다.
아래를 실행하면 질문마다 읽을 수 있는 파일이 만들어진다.

```bash
uv run python 12_read.py
```

```
data/derived/responses/Q01.md   ← Q01 의 채점 대상 3개 모델 × 2회 응답 전문
data/derived/responses/Q02.md
...
```

질문·기대 결과·감점 요소가 맨 위에 함께 들어 있어 그 파일 하나만 보고 채점할 수 있다.
`responses/Q01.md` 를 열어 읽고, `eval-results.md` 의 같은 `Q01` 블록에 점수를 적는다.
한 질문의 답을 나란히 놓고 채점하면 같은 기준을 유지하기 쉽다.

### 채점 대상

실행은 6개 모델 전부 했지만, **품질 채점은 3개만** 한다.

| 구분 | 모델 | 채점 블록 |
|---|---|---|
| 비교 대상 | C (금융) · D (코딩) · F (이커머스) | 60 |
| 부가 테스트 | A (법률) · B (의료·바이오) · E (수학) | 없음 |

`eval-results.md` 와 `responses/*.md` 에는 **비교 대상만** 나온다.
부가 테스트의 실행 기록 120회분은 `data/raw/local/runs.jsonl` 에 그대로 있고,
STEP 6 의 '부가 테스트' 표에 성능 측정값이 나온다.

60개 블록이 만들어져 있고, 블록 제목이 곧 `run_id` 다.
문제마다 평가 기준이 다르게 들어가 있으므로 있는 항목만 채우면 된다.

### 채점 대상을 바꾸려면

`data/config/models.json` 의 `tier` 를 고치고 `12_read.py` 를 다시 실행한다.

| 값 | 뜻 |
|---|---|
| `primary` | 채점하고 최종 선정 후보로 삼는다 |
| `supplementary` | 실행 기록과 성능 측정만 쓰고 채점하지 않는다 |

`eval-results.md` 의 **질문 구간은 생성물**이다. `12_read.py` 가 `questions.json` 과
`tier` 를 보고 다시 만든다. 적어 둔 점수는 `run_id` 로 찾아 옮기므로 여러 번 실행해도
안전하다. 블록을 손으로 지우거나 추가하지 않는다.

파일 앞머리(채점 방법·실행 환경·모델 목록)는 직접 쓰는 부분이라 건드리지 않는다.

`12_read.py` 의 `RESET = True` 는 적어 둔 점수를 **전부 지운다.** 되돌릴 수 없다.

```
## Q01 / Model B / Run 1        <- run_id = B_Q01_r1

원본 기록 ID: B_Q01_r1
상태: 성공

답변 적합성: 4
근거: 주문 상태 확인을 먼저 제안했으나 배송사 문의 순서가 불명확했음

논리성/실용성: 5
근거: 단계적 확인 순서를 제시하고 다음 행동이 분명함

한국어 표현: 5
근거: 문장이 자연스럽고 장황하지 않음

평균: 4.7
```

- `원본 기록 ID` 는 적어도 되고 비워도 된다. 제목에서 자동으로 만든다
- `평균` 은 비워도 된다. 집계가 기준별 평균을 따로 계산한다
- 점수를 비워 두면 미채점으로 본다. `0` 과 구분된다
- 호출이 실패한 회차는 채점하지 않는다. 점수를 적으면 검사에서 경고가 나온다

원본 응답은 `data/raw/local/runs.jsonl` 의 해당 `run_id` 줄에서 본다.

채운 뒤 `11_finish.py` 를 실행하면 집계표에 반영된다.

## 4. 집계와 표 생성

`11_finish.py` 가 이어서 처리한다.

`data/derived/` 에 다음이 만들어진다.

| 파일 | 내용 |
|---|---|
| `local_summary.json` | 집계 결과 + 각 수치에 기여한 `run_id` 목록 |
| `cloud_summary.json` | Cloud 집계 |
| `tables/model_comparison.md` | 산출물 2 — 제원 비교표 |
| `tables/local_summary.md` | 산출물 3 — 성능·품질 집계표 |
| `tables/local_cloud.md` | 산출물 4 — Local vs Cloud |

이 파일들은 **생성물**이다. 저장된 값을 읽는 게 아니라 매번
`runs.jsonl` 에서 다시 계산한다. 통째로 지우고 다시 실행하면 복원된다.
직접 수정하지 않는다.

생성된 표를 `docs/steps/step06.md` 등에 붙여넣는다.

---

## 5. 출력 읽는 법

### 집계표의 "집계 불가"

```
| 평균 생성 속도 | 집계 불가 (유효한 측정값 없음) |
```

평균을 `0` 으로 적지 않는다. 유효한 측정값이 한 건도 없다는 뜻이다.
과제 스펙이 요구하는 표기다.

### `(n=18)`

평균 계산에 쓰인 응답 수다. **지표마다 다르다.**
모델당 20회를 돌렸어도 VRAM 을 18번만 읽었다면 `n=18` 이다.
평가 기준도 마찬가지다. A 는 10문항, D 는 3문항(Q03·Q06·Q08),
E 는 4문항(Q04·Q05·Q09·Q10)에서만 나온다.

### 세 가지 "실패"의 구분

| 무엇 | 어디에 | 집계에서 |
|---|---|---|
| 호출 실패 | `status="error"` | 성공 수 / 전체 시도 수에 반영 |
| 지표 측정 누락 | 값이 `null` + `measurement_notes` 에 사유 | 그 지표의 평균과 `n` 에서만 제외 |
| 답변 품질 미달 | `scores.jsonl` 의 낮은 점수 | 품질 평균에 포함 |

**품질이 낮은 것은 호출 실패가 아니다.** 정상적으로 받은 응답이므로
채점에 포함한다. 반대로 호출 실패는 채점 대상이 아니다.

---

## 6. 수치를 원본까지 역추적하기

집계표의 숫자가 어디서 나왔는지 3단계로 내려간다.

```
tables/local_summary.md    "평균 전체 응답 시간 3.42 (n=18)"
        ↓
local_summary.json         models.B.metrics.elapsed_sec.source_run_ids
        ↓
runs.jsonl 의 해당 run_id 줄       원본 응답 + 측정값 + 설정
```

`source_run_ids` 는 평균에 쓰인 회차, `excluded_run_ids` 는 값이 없어
빠진 회차다. 둘을 합치면 왜 `n` 이 20이 아닌지 설명된다.

---

## 7. 문제 상황

### 모델 태그가 틀렸을 때

호출이 전부 실패로 나온다. `10_run.py` 가 실행 때마다 환경을 수집하면서
`client.list()` 목록에 없는 모델은 "아직 pull 하지 않았을 수 있음" 으로
알려준다. `data/config/models.json` 의 `model_tag` 를 실제 값으로 고친다.

### 잘못 기록된 회차를 지우고 싶을 때

기록은 append 전용이라 코드에는 지우는 경로가 없다. 의도적인 설계다.
실수로 남은 회차가 있다면 `runs.jsonl` 을 직접 편집해야 하며,
**무엇을 왜 지웠는지 `docs/steps/step06.md` 에 남긴다.**

### 실패한 회차를 다시 돌리고 싶을 때

재시도는 원본과 다른 `run_id` 를 받는다 (`B_Q01_r1_retry1`).
원래 실패 기록은 그대로 남고, 재시도 결과는 기본 집계에서 제외된다.
과제 스펙이 "재시도 성공 결과로 원래 실패 기록을 덮어쓰지 않는다" 를
요구하기 때문이다.

### 검사에서 ERROR 가 날 때

```
B_Q03_r1: elapsed_sec 가 null 인데 measurement_notes 에 사유 없음
```

측정 실패를 조용히 넘기지 못하게 막는 장치다. 값이 없으면 반드시
사유가 있어야 한다. 보통 코드 쪽 문제이므로 그대로 두지 말고 확인한다.

---

## 8. Cloud 비교 (STEP 7)

`run_cloud` 의 호출부는 아직 구현 전이다. `data/config/models.json` 의
`cloud_model` (모델 ID, 단가)을 먼저 채워야 한다.

API 키는 실행 시점에 입력받고 **어떤 파일에도 저장하지 않는다.**
코드·저장소·실험 로그·스크린샷 어디에도 남기지 않는다.

Cloud 는 `cloud_compare=true` 인 질문 5개(Q01·Q04·Q06·Q09·Q10)를 각 1회
호출한다. 로컬은 질문당 2회이므로 **반복 수가 다르다는 점을 표에 함께 적는다.**

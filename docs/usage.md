# 사용법

실행 파일은 `project1-python-start/10_experiment.py` 하나다.
파일 위쪽 상수만 바꾸고 아래 명령을 반복한다.

```bash
cd project1-python-start
uv run python 10_experiment.py
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

### 1-2. `data/config/run_settings.json` 채우기

**본 실험을 시작하기 전에 확정한다.** 여기 적힌 값이 모든 모델에 동일하게
적용되고, 회차마다 기록에 복사된다. 실험 도중 바꾸면 앞뒤 회차의 조건이
달라져 비교가 성립하지 않는다.

| 항목 | 의미 | 비워두면 |
|---|---|---|
| `timeout_sec` | 한 번의 호출을 얼마나 기다릴지 | 무한 대기. 모델이 멈추면 실험이 멈춘다 |
| `options.temperature` | 생성의 무작위성 | Ollama 기본값이 적용되고 **기록에는 남지 않는다** |
| `options.num_predict` | 최대 출력 토큰 수 | **생성이 폭주한다.** 실측에서 한 질문에 40,960 토큰(73,000자)까지 생성하고 13분 넘게 걸렸다. 반드시 값을 정한다 |
| `options.num_ctx` | 입력+출력을 담을 context 크기 | 위와 같음. 산출물의 "실험에 사용한 Context" 근거가 없어진다 |
| `options.seed` | 재현용 시드 | 값을 넣지 않으면 전달하지 않는다 |
| `keep_alive` | 응답 뒤 모델을 메모리에 얼마나 둘지 | **기본값(5분)이 적용되며 VRAM 측정에 문제없다.** `0` 으로 두면 응답 직후 언로드되어 `size_vram` / `digest` / `context_length` 를 읽지 못한다 |
| `warmup_question_id` | 워밍업에 쓸 질문 | **워밍업이 통째로 건너뛰어진다.** 과제는 모델당 워밍업 1회를 요구한다 |
| `repeats` | 질문당 반복 횟수 | 이미 `2` 로 들어가 있다 |

값이 `null` 인 옵션은 Ollama 에 전달하지 않는다. 따라서 기록에 남은
`options` 는 실제로 넘긴 값과 항상 일치한다.

설정을 꼭 바꿔야 한다면 `settings_version` 을 올리고 `changed_reason` 을
적는다. 집계할 때 서로 다른 버전이 섞여 있으면 경고가 나온다.

### 1-3. 환경 정보 수집

```python
MODE = "env"
```

OS / Python / Ollama / 패키지 버전, GPU·VRAM·CPU·RAM,
모델별 digest·양자화·다운로드 크기가 `data/env/environment.json` 에 들어간다.

출력 마지막의 **"직접 채워야 하는 항목"** 은 웹에서 확인해야 하는 값들이다.

- `platform.execution_type` — 예: `Local PC`
- 모델별 `model_card_url`, `license_declared`, `license_base_model`, `doc_max_context`

`doc_max_context`(Model Card 문서상 최대 Context)와 실행 기록의
`context_length`(실제 설정값)는 **산출물에서 반드시 구분해서 적어야 하므로**
서로 다른 곳에 저장된다.

---

## 2. 로컬 실험 — 모델 하나씩

### 2-1. 첫 모델은 몇 건만 먼저

```python
MODE = "run"
MODEL = "B"     # B / C / D / E
LIMIT = 3       # 먼저 3건만
```

실행이 끝나면 진행 상황과 검사 결과가 자동으로 출력된다.
확인하려고 따로 돌릴 것은 없다.

```
[OK ] B_Q01_r1   응답=7.70s  로딩=5.05s  출력토큰=128  생성속도=50.9t/s  VRAM=5028MiB
```

**여기서 반드시 볼 것**

| 증상 | 원인 | 조치 |
|---|---|---|
| `VRAM=null` | `keep_alive=0` 이라 응답 직후 언로드됨 | 멈추고 `run_settings.json` 수정. **기록은 append 전용이라 되돌릴 수 없다** |
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
MODEL = "C"     # 이후 "D", "E"
```

모델은 한 번에 하나만 메모리에 올린다. 한 모델이 끝나면 언로드하고
다음 모델을 올린다. 8GB VRAM 에서 두 개를 동시에 올리지 않기 위해서다.

### 2-4. 진행 상황만 보고 싶을 때

```python
MODE = "check"
```

```
모델      본실험    성공   실패  워밍업
B        20/20     20     0    있음
C        20/20     19     1    있음
D         0/20      0     0    없음
```

한 회차의 원본 응답 전문을 보려면:

```python
MODE = "check"
RUN_ID = "B_Q01_r1"
```

---

## 3. 채점

80회를 다 채운 뒤에 한다.

```python
MODE = "score"
```

`data/scoring/scores.jsonl` 에 회차마다 빈 채점 레코드가 깔린다.
`run_id` / `question_id` / 평가 기준 코드는 원본에서 그대로 가져오므로
손으로 적을 필요가 없다.

```json
{
  "run_id": "B_Q01_r1",
  "question_id": "Q01",
  "scores": {"A": null, "B": null, "C": null},
  "rationales": {"A": null, "B": null, "C": null},
  "average": null,
  "reviewed": false
}
```

- 문제마다 기준이 다르다. Q01 은 A·B·C, Q03 은 A·B·C·D, Q09 는 A·B·C·E
- 점수와 `rationales`(근거)를 채운다. 근거는 응답의 어느 부분 때문인지 적는다
- `average` 는 비워도 된다. 집계가 기준별 평균을 따로 계산한다
- 호출 실패 회차는 `not_scored_reason` 이 채워진 채로 나온다. 점수는 비워 둔다
- 재검토 후 점수를 고쳤다면 `reviewed`, `revision_reason` 을 채운다

채점하면서 원본 응답을 볼 때는 `MODE = "check"`, `RUN_ID` 를 쓴다.

---

## 4. 집계와 표 생성

```python
MODE = "table"
```

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
20회를 돌렸어도 VRAM 을 18번만 읽었다면 `n=18` 이다.
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
MODE = "check", RUN_ID = "B_Q01_r1"    원본 응답 + 측정값 + 설정
```

`source_run_ids` 는 평균에 쓰인 회차, `excluded_run_ids` 는 값이 없어
빠진 회차다. 둘을 합치면 왜 `n` 이 20이 아닌지 설명된다.

---

## 7. 문제 상황

### 모델 태그가 틀렸을 때

호출이 전부 `[ERR]` 로 나온다. 실제로 내려받은 태그를 확인한다.

```python
MODE = "env"
```

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

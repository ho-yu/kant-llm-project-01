# 데이터 흐름 — 원본 기록에서 산출물까지

> 이 문서는 "집계표의 이 숫자가 어느 실행에서 나왔는가"를 역추적하기 위한 지도다.
> 파일 목록과 스키마는 [README](../README.md), 실행 코드는 `project1-python-start/src/evalkit/` 에 있다.

## 1. 전체 흐름

```
[1회 작성 후 고정]                      [append 전용]                [생성물 — 재생성 가능]

data/config/run_settings.json  ─┐
data/config/models.json        ─┼──> run_local.py ──> data/raw/local/runs.jsonl ─┐
data/config/questions.json     ─┘                                                │
                                │                                                │
                                └──> run_cloud.py ──> data/raw/cloud/runs.jsonl ─┤
                                                                                 │
data/env/environment.json ───────────────────────────────────────────┐           │
                                                                     │           │
              (사람이 원본 응답을 읽고 채점)                          │           │
                    data/raw/*/runs.jsonl ──> data/scoring/scores.jsonl           │
                                                      │              │           │
                                                      └──────────────┼───────────┤
                                                                     │           │
                                                                     ▼           ▼
                                                              aggregator.py (계산)
                                                                     │
                                                    ┌────────────────┴────────────────┐
                                                    ▼                                 ▼
                                      data/derived/*_summary.json          exporter.py (표 변환)
                                                                                      │
                                                                                      ▼
                                                                        data/derived/tables/*.md
                                                                                      │
                                                                                      ▼
                                                                          docs/ 문서에 붙여넣기
```

**핵심**: 집계표는 저장된 값을 읽는 게 아니라 매번 `data/raw/` 에서 다시 계산한다.
`data/derived/` 를 통째로 지우고 `python -m evalkit.aggregator && python -m evalkit.exporter` 만 다시 돌리면 복원된다.

## 2. 파일별 성격

| 파일 | 성격 | 쓰는 주체 | 규칙 |
|---|---|---|---|
| `data/config/run_settings.json` | 1회 작성 후 고정 | 사람 | 본 실험 시작 후 변경 금지. 바꿨다면 `settings_version` 을 올린다 |
| `data/config/models.json` | 1회 작성 후 고정 | 사람 | `model_label` 은 모든 표의 키. 확정 후 변경 금지 |
| `data/config/questions.json` | 1회 작성 후 고정 | 사람 | `docs/steps/step05.md` 의 전사본. `cloud_compare` 는 결과 보기 전에 확정 |
| `data/env/environment.json` | 1회 작성 후 고정 | 사람 | 환경이 바뀌면 새 버전 파일 + `applies_from_run_id` |
| `data/raw/local/runs.jsonl` | **append 전용** | `run_local.py` | `"a"` 모드 고정. 한 줄 = 한 회차. 수정·삭제 금지 |
| `data/raw/cloud/runs.jsonl` | **append 전용** | `run_cloud.py` | 위와 같음 |
| `data/scoring/scores.jsonl` | **append 전용** | 사람 | `run_id` 로 실행 기록과 연결 |
| `data/derived/*_summary.json` | 생성물 | `aggregator.py` | 직접 수정 금지 |
| `data/derived/tables/*.md` | 생성물 | `exporter.py` | 직접 수정 금지 |

저장소에 넣지 않는 것: 모델 가중치, API 키, `.venv/` (루트 `.gitignore` 로 제외).

## 3. 워밍업 / 본 실험 / 재시도 / 추가 실험 구분

한 파일에 함께 쌓이되 `phase` 필드와 `run_id` 접미사로 구분한다.

| 구분 | `phase` | `run_id` 예시 | 기본 집계 포함 |
|---|---|---|---|
| 워밍업 | `warmup` | `B_warmup` | 제외 |
| 본 실험 | `main` | `B_Q01_r1` | **포함** |
| 재시도 | `retry` | `B_Q01_r1_retry1` | 제외 |
| 추가 실험 | `extra` | `B_Q01_r1_extra1` | 제외 |

재시도는 원본과 **다른 `run_id`** 를 받고 `retry_of_run_id` 로 원본을 가리킨다.
append 전용이므로 원래 실패 기록이 재시도 성공 결과로 덮어써지는 경로가 존재하지 않는다.

## 4. 세 가지 축의 분리

같은 "실패"라도 성격이 다르므로 서로 다른 곳에 기록한다.

| 축 | 어디에 | 어떻게 | 집계에서 |
|---|---|---|---|
| 1. 호출 성공 여부 | `runs.jsonl` | `status` = `success` / `error` | 성공 수 / 전체 시도 수 |
| 2. 지표 측정 여부 | `runs.jsonl` | 지표 = `null` + `measurement_notes[지표]` 에 사유 | 해당 지표의 평균과 `n` 에서만 제외 |
| 3. 답변 품질 | `scores.jsonl` | `scores[기준코드]` | 품질 평균 |

- `status="success"` 인데 지표가 `null` 일 수 있다 (호출은 됐지만 통계를 못 읽음).
- `done_reason="length"` 는 실패가 아니다. 정상 응답이되 출력 한도에서 잘린 것이며, 채점 시 "내용이 부족한 것"과 구분한다.
- `status="error"` 면 채점 대상이 아니다 (`not_scored_reason` 에 사유).
- 품질 점수가 낮은 것은 호출 실패가 **아니다**. 정상 응답이므로 채점에 포함한다.

## 5. 역추적 경로

집계표의 숫자 → 원본까지 3단계로 내려간다.

```
data/derived/tables/local_summary.md   "평균 전체 응답 시간 3.42 (n=18)"
        │
        │  같은 셀의 원본
        ▼
data/derived/local_summary.json        models.B.metrics.elapsed_sec
        │                                ├ mean: 3.42
        │                                ├ n: 18
        │                                ├ source_run_ids: [...]   ← 평균에 쓰인 회차
        │                                └ excluded_run_ids: [...] ← 값이 없어 빠진 회차
        ▼
data/raw/local/runs.jsonl              해당 run_id 줄 = 원본 응답 + 측정값 + 설정
```

코드로 한 번에:

```python
from evalkit import aggregator
aggregator.trace("B_Q01_r1")   # 실행 기록 + 채점 기록을 함께 반환
```

품질 점수는 `scores.jsonl` 의 `run_id` → `runs.jsonl` 의 같은 `run_id` 로 이어진다.
`validator.validate_scores()` 가 대응되지 않는 `run_id` 를 에러로 잡는다.

## 6. 산출물 5가지가 나오는 위치

| 산출물 | 나오는 곳 | 근거 원본 |
|---|---|---|
| 1. GitHub Repository | 저장소 전체 + `README.md` | — |
| 2. Model Comparison Table | `data/derived/tables/model_comparison.md` | `data/env/environment.json` + `runs.jsonl` 의 `context_length` |
| 3. Model Test / Benchmark 결과 | `data/raw/local/runs.jsonl` (원본) + `data/derived/tables/local_summary.md` (집계) | 원본 그 자체 |
| 4. Local vs Cloud 비교 | `data/derived/tables/local_cloud.md` | `raw/local` + `raw/cloud` |
| 5. 최종 Model Selection Report | `docs/steps/step08.md` | 위 2~4 + `docs/steps/step02.md` 의 선정 기준 |

문서 쪽 대응:

| 문서 | 받는 내용 |
|---|---|
| `docs/steps/step04.md` | `data/env/environment.json` 의 실행 환경 |
| `docs/steps/step05.md` | `data/config/questions.json` 의 원본 (문서가 원본, JSON 이 전사본) |
| `docs/steps/step06.md` | `tables/local_summary.md` 의 집계표 |
| `docs/steps/step07.md` | `tables/local_cloud.md` |
| `docs/eval-results.md` | 문제별 채점 블록 — `scores.jsonl` 과 같은 내용을 사람이 읽는 형태로 |
| `docs/deliverables.md` | 위 전부의 위치 인덱스 |

## 7. 실행 순서

```bash
# 0) 설정 확정 — run_settings / questions / environment 를 먼저 채운다
# 1) 실행 계획 확인 (호출 없음)
python -m evalkit.run_local --dry-run

# 2) 로컬 실험 — 모델 하나씩, 중단해도 이어서 실행 가능(중복 run_id 는 건너뜀)
python -m evalkit.run_local

# 3) Cloud 실험
python -m evalkit.run_cloud

# 4) 저장된 파일 재검증
python -m evalkit.validator

# 5) 집계 + 표 생성
python -m evalkit.aggregator
python -m evalkit.exporter
```

2번은 언제든 중단하고 다시 실행할 수 있다. 이미 기록된 `run_id` 는 건너뛰고 경고만 낸다.

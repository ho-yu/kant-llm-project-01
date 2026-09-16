# Local–Cloud 실험 조건 및 실행 전 점검표

이 문서가 **완료된 실험의 환경 설정·테스트 조건·보완할 지표를 확인하는 단일 지점**이다. 기준은 저장된 원본 실행 기록의 `settings_version=v1`이다. 기존 기록이나 채점은 변경하지 않는다.

## 1. 완료된 실험의 적용 조건

| 항목 | 완료된 실험의 기준값 | 확인 결과·한계 |
|---|---|---|
| Temperature | Local 0; Cloud 요청에 미지정 | Local 적용 확인. Cloud의 파라미터 지원 여부와 실제 적용값은 원본에서 확인할 수 없음 |
| Context | Local `num_ctx=4096`; Cloud 요청에 미지정 | Cloud와 동일한 창 크기를 지정하지 못함 |
| Max Output | Local `num_predict=768`; Cloud `max_output_tokens=768` | **실제 양쪽 요청의 한도는 768토큰.** 서로 다른 토크나이저의 토큰 수가 같다거나 답변이 안 잘린다는 뜻은 아님 |
| Tools | 없음 | Local 도구 호출 없음; Cloud 실행 코드 `tools=[]`, `tool_choice=none`. Cloud JSONL에 독립 필드로 저장되지 않음 |
| RAG / Search | 없음 | 두 실행 경로에서 검색·검색결과 삽입을 하지 않음 |
| Prompt | 공통 5문항의 원문 완전 동일 | Local 30건·Cloud 5건 모두 `questions.json`의 Q01·Q04·Q06·Q09·Q10 원문과 일치 |
| System Instruction | 양쪽 모두 없음 | Local `system_prompt=null`; Cloud 요청에 system/developer 지시 없음. Cloud JSONL에는 독립 필드 없음 |
| Conversation History | 없음 | Local 매 호출 `user` 메시지 1개; Cloud 매 호출 독립 `input` |
| Local 반복 | 질문당 2회 | C·D·F 각각 공통 5문항 × 2회. 전체 Local 실험은 모델당 10문항 × 2회 |
| Cloud 반복 | 질문당 1회 | 공통 5문항 × 1회 |
| Local Warm-up | 모델당 1회, 본실험 제외 | A~F 각 1건 `phase=warmup`; 집계는 `phase=main`만 |
| 실패 | 대체 실행하지 않고 실패 기록 | 호출 예외를 `status=error`로 append하는 코드. 이번 비교 범위의 호출 오류는 0건이라 실패 사례 자체는 미검증 |
| Retry | 본실험과 별도 기록 | `phase=retry`, `retry_of_run_id` 구조. 자동 재시도 0; 이번 비교의 retry 기록 0건 |
| Finish Reason | Local `done_reason`; Cloud `api_status` | Local C·D·F 각 `stop` 10건. Cloud `completed` 4건, `incomplete` 1건. Cloud 상세 미완료 사유는 미기록 |
| Local C / D / F | 동일 옵션 | 공통 5문항 30건 모두 `temperature=0`, `num_predict=768`, `num_ctx=4096`, `seed=0` |
| Cloud | 공통 5문항에 가능한 공통 생성조건 | 동일 Prompt·출력 한도 768 적용. temperature·context·seed는 미전달 |

**종료 상태 해석:** Cloud Q10은 API 응답을 받아 호출 상태는 `success`였지만 API 종료 상태는 `incomplete`다. 출력 768토큰이 요청 한도 768과 일치한다. 상세 사유가 저장되지 않아 원인을 확정하지 않는다. 따라서 정상 종료는 4/5건이다.

## 2. 실행 전 설정 위치

값을 확인하거나 바꿀 때는 **이 표에서 시작한다.** 실행 가능한 설정과 질문·모델 식별값은 각각의 원본 파일에 남긴다. 기존 기록과 연결되는 값을 삭제하거나 소급 변경하지 않는다.

기존 Local 측정 환경(`data/env/environment.json`, 2026-09-15 기록): Windows Local PC, RTX 5060 Laptop GPU(기록된 VRAM 8,151 MiB), RAM 31.4 GB, Python 3.12.13, Ollama 0.34.0. 실행 타임아웃은 `execution_conditions.json`의 300초이며, 이는 성능 측정값이 아니라 호출 제한이다. Cloud의 서버 하드웨어와 네트워크 조건은 로컬 환경 파일에 기록되지 않았다.

| 설정할 것 | 실제 적용 위치 | 실행 전에 확인할 내용 |
|---|---|---|
| Local temperature, context, 출력 한도, seed | `data/config/execution_conditions.json` → `options` | 기존 `temperature=0`, `num_ctx=4096`, `num_predict=768`, `seed=0` |
| 설정 버전·호출 타임아웃 | 같은 파일 → `settings_version`, `changed_reason`, `timeout_sec` | 기존 `v1`/300초 |
| Local 반복·워밍업·시스템 지시·대화 이력 | 같은 파일 → `repeats`, `warmup_per_model`, `warmup_question_id`, `use_system_prompt`, `system_prompt`, `independent_questions` | `2`, `1`, `Q01`, `false`, `null`, `true` |
| Cloud 모델 ID·가격 | `data/config/models.json` → `cloud_model` | 모델 식별값과 기록 당시 단가 확인 |
| Cloud temperature·도구·reasoning·반복·재시도 | `data/config/execution_conditions.json` → `cloud` | 현재 temperature 요청은 생략. 지원 여부와 적용값을 확인하기 전에는 Local 0과 같다고 주장하지 않음. 반복 1회·자동 재시도 0회 |
| Cloud 출력 한도 | `config.cloud_options()`가 Local의 `num_predict`에서 생성 | 기존 요청은 `max_output_tokens=768` |
| 공통 5문항·Prompt | `data/config/questions.json` → `cloud_compare=true`, `prompt` | 정확히 5개인지 확인. 질문 내용은 기존 원본과 동일하게 유지 |
| Tools·RAG/Search·Reasoning | `data/config/execution_conditions.json` → `local_tools`, `rag_search`, `cloud` | Cloud `tools=[]`, `tool_choice=none`, `reasoning.effort=none`; 검색 호출 없음 |
| 오류·재시도·종료 상태 | `recorder.py`, `run_local.py`, `run_cloud.py` | 실패를 append하고 대체하지 않음. 재시도는 `phase=retry`. Local `done_reason`, Cloud `api_status` 확인 |
| 실제 환경 정보 | `data/env/environment.json` | OS, GPU/VRAM, RAM, Ollama·Python 버전은 실행 시점에 다시 수집 |

`execution_conditions.json`이 **현재 실행 코드**의 조건 출처다. 완료된 v1 실험의 적용값은 각 원본 실행 기록의 `options`와 상태 필드가 우선 증거다. 새 파일은 기존 `run_settings.json`의 v1 값을 옮겨 보존했으며, 실험 당시 그 파일명으로 실행됐다고 뜻하지 않는다. `models.json`에는 모델 ID·가격, `questions.json`에는 확정된 질문 원문과 Cloud 비교 대상이 있다.

## 3. 비교에 사용할 기준 지표 — 완료된 실험값

아래 수치는 **공통 5문항만** 사용한다. Local은 모델당 10응답(각 질문 2회), Cloud는 5응답(각 질문 1회)이다. 평균에는 유효값의 개수 `n`을 함께 표시한다. 품질은 STEP 05의 기존 A~E 기준에 따라 응답별 평균을 낸 뒤 공통 문항의 응답을 동일 가중 평균했다. 새 평가 기준이나 점수는 만들지 않았다.

| 모델 | 품질 평균 / n | 호출 성공 / 시도 | 정상 종료 / 한도·미완료 / 오류 | 전체 응답 시간 평균 / n |
|---|---:|---:|---:|---:|
| C 금융 | 2.32 / 10 | 10/10 | 10 / 0 / 0 | 3.40초 / 10 |
| D 코딩 | 3.00 / 10 | 10/10 | 10 / 0 / 0 | 4.77초 / 10 |
| F 이커머스 | 3.50 / 10 | 10/10 | 10 / 0 / 0 | 3.86초 / 10 |
| Cloud | 4.68 / 5 | 5/5 | 4 / 1 / 0 | 7.17초 / 5 |

| 모델 | 입력 토큰 평균 / n | 출력 토큰 평균 / n | 응답 글자 수 평균 / n | 생성 속도 평균 / n | 로딩 시간 평균 / n |
|---|---:|---:|---:|---:|---:|
| C 금융 | 53.0 / 10 | 179.7 / 10 | 351.6 / 10 | 62.25 tokens/s / 10 | 0.42초 / 10 |
| D 코딩 | 45.0 / 10 | 282.5 / 10 | 499.8 / 10 | 66.36 tokens/s / 10 | 0.42초 / 10 |
| F 이커머스 | 45.0 / 10 | 204.9 / 10 | 335.8 / 10 | 62.89 tokens/s / 10 | 0.39초 / 10 |
| Cloud | 37.2 / 5 | 504.8 / 5 | 899.2 / 5 | 미측정 | 미제공 |

Local 입력·출력 토큰은 Ollama의 `prompt_eval_count`·`eval_count`, Cloud는 API `input_tokens`·`output_tokens`다. 토크나이저가 달라 토큰 수를 답변 길이나 장황함의 동일 척도로 보지 않는다. Local `tokens_per_sec`와 Cloud의 네트워크 포함 `elapsed_sec`도 직접 비교하지 않는다. Cloud 내부 생성 시간이 없어 Cloud tokens/s를 계산하지 않는다.

| 비용·자원 지표 | 완료된 실험에서 확인한 값 | 한계 |
|---|---|---|
| Cloud API 사용량 | 입력 총 186, 출력 총 2,524토큰 | 실제 API 사용량 기록 |
| Cloud 적용 단가 | 입력 0.20 USD/1M, 출력 1.20 USD/1M | `models.json`의 2026-09-16 확인값; [공식 가격표](https://developers.openai.com/api/docs/pricing) |
| Cloud 추정 API 비용 | 총 0.0030660 USD, 5회 평균 0.0006132 USD | 기록 당시 단가 적용. **실제 청구액 아님** |
| Local 응답 직후 VRAM 평균 | C 5,027.5 MiB; D 4,528.1 MiB; F 4,528.1 MiB (각 n=10) | 최대 VRAM 또는 총 운영비가 아님 |
| Local 운영비 | API 토큰 과금 없음 | PC/GPU·전력·저장 공간·관리비 미측정, 임의 금액 계산 불가 |

## 4. 추가로 보완할 지표와 기록 방식

다음 항목은 **이번 원본 기록만으로 확인할 수 없는 부분**이다. 기존 값에 추정치를 채우지 않고, 후속 실행·운영 기록에서 확보한다.

| 지표 | 현재 상태 | 후속 기록에 필요한 값 |
|---|---|---|
| Cloud 미완료 상세 사유 | Q10 `api_status=incomplete`, 상세 사유 미기록 | API 응답의 `incomplete_details.reason`을 별도 필드에 저장. 종료 상태와 호출 성공을 분리 |
| Cloud 요청 조건 증거 | JSONL `options`에는 출력 한도만 저장 | 실제 전송한 `tools`, `tool_choice`, `reasoning`, system 지시 유무, 대화 이력 사용 여부를 요청 스냅샷으로 저장 |
| Temperature·context 동등성 | Cloud 요청에서 미지정 | API가 지원·적용한 값 또는 미지원 상태와 근거를 명시. Local과 같다고 가정하지 않음 |
| 네트워크와 서버 시간 | Cloud 전체 elapsed만 기록 | 측정 가능한 경우 네트워크 왕복·서버 처리 시간을 분리. 제공되지 않으면 계속 미측정으로 표시 |
| 실제 Cloud 청구액 | 토큰 기반 추정 비용만 있음 | 계정 사용량/청구 기록에서 기간·통화·실제 금액을 별도로 확인 |
| Local 총운영비 | API 과금 없음만 확인 | 전력, 장비 감가·유지, 저장 공간, 관리·서빙 시간을 측정한 뒤 산정 |
| 반복 변동성 | Local 2회, Cloud 1회 | 문항별 두 Local 점수·시간의 범위 표시. Cloud 반복 변동성은 현재 평가 불가 |
| 평가 표본 | 공통 질문 5개 | 더 넓은 질문군은 기존 결과와 분리하고, 질문 선정 시점·버전을 기록 |

**집계 원칙:** 호출 성공/시도, 정상 종료/한도·미완료/오류, 품질 `n`, 지표별 `n`을 각각 표시한다. 실패를 성공 응답으로 대체하지 않는다. 워밍업·재시도는 본실험 평균에서 제외한다. 품질·속도·비용·보안·운영·커스터마이징을 임의 총점으로 합치지 않는다.

## 5. 512토큰 제안과 기존 결과의 경계

512토큰은 완료된 실험의 설정이 **아니다**. 적용하려면 `settings_version`을 올리고 변경 사유를 남긴 별도 실험이 필요하다. 현재 실행기는 기존 `run_id`를 건너뛰므로 설정 숫자만 바꿔 재실행해도 새 결과가 생기지 않는다. 별도 기록 위치 또는 새 식별 체계를 준비하고, Local·Cloud 양쪽의 실제 요청을 확인한 후 기존 768 결과와 분리해 평가해야 한다.

## 6. 근거 파일

- 실제 요청과 응답: `data/raw/local/runs.jsonl`, `data/raw/cloud/runs.jsonl`
- 기존 실행 설정: `data/config/execution_conditions.json`, `data/config/models.json`, `data/config/questions.json`
- 실행 코드: `project1-python-start/src/evalkit/run_local.py`, `run_cloud.py`, `config.py`, `recorder.py`
- 결과 해석: `docs/steps/step06.md`, `docs/steps/step07.md`

이 점검표는 원본 결과를 변경하거나 512토큰 재실험을 완료했다는 뜻이 아니다.

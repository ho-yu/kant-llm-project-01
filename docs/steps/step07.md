# Step 07

이 문서의 STEP 07 본문은 기존 기록과 채점표에서 자동 생성된다. 재생성: `python -m evalkit.step07_report` (project1-python-start에서 실행).

---

<!-- evalkit:auto:start — 아래는 자동 생성 구간입니다. 직접 고치지 마세요. -->

## STEP 07 — Local LLM vs Cloud API

### 비교 범위

- Local: Model C 금융, Model D 코딩, Model F 이커머스. Cloud: `gpt-5.6-luna`.
- 공통 질문: Q01, Q04, Q06, Q09, Q10 (`questions.json`의 `cloud_compare=true`), 총 5개.
- 질문당 Local 2회 모두 집계, Cloud 1회. 워밍업과 재시도는 제외.
- 이 단계에서는 최종 Local 모델을 선정하지 않는다.

### 비교 조건

| 항목 | Local | Cloud | 상태 |
|---|---|---|---|
| 질문 | 동일한 원문 5개 | 동일한 원문 5개 | 동일 |
| Temperature | `0` | `0` (요청에 전달됨) | 동일 |
| Output limit | `num_predict=768` | `max_output_tokens=768` | 숫자는 같으나 토크나이저·한도 의미 차이 |
| Context | `num_ctx=4096` | API에서 창 크기 미지정 | 차이 |
| Tools | 사용 안 함 | `tools=[]`, `tool_choice=none` (실행 코드) | 도구 미사용 |
| Reasoning | 별도 설정 없음 | `effort=none` (실행 코드) | 모델 계열 차이 |
| Generation settings | `seed=0`, system prompt 없음 | seed 미지정, system prompt 없음 | 일부 차이 |
| 반복 횟수 | 2회/문항 | 1회/문항 | 의도적 차이 |

요청 설정은 로컬 원본의 `options`, Cloud 원본의 `options`, `run_cloud.py` 호출 코드에서 확인했다. Cloud의 tools·reasoning 요청값은 현재 JSONL에 독립 필드로 저장되지 않아 원본만으로 재검증할 수 없다. 토크나이저, 로컬 단일 Windows/GPU 추론 환경, Cloud 서버·네트워크가 서로 다르다.

### 공통 5문항

| 질문 | Model C | Model D | Model F | Cloud |
|---|---:|---:|---:|---:|
| Q01 | 3.33 (n=2) | 4.00 (n=2) | 4.50 (n=2) | 4.67 (n=1) |
| Q04 | 1.75 (n=2) | 2.50 (n=2) | 3.25 (n=2) | 4.50 (n=1) |
| Q06 | 3.00 (n=2) | 3.88 (n=2) | 3.25 (n=2) | 4.50 (n=1) |
| Q09 | 1.50 (n=2) | 2.62 (n=2) | 4.00 (n=2) | 5.00 (n=1) |
| Q10 | 2.00 (n=2) | 2.00 (n=2) | 2.50 (n=2) | 4.00 (n=1) |

### Quality

STEP 05의 A 답변 적합성, B 논리성/실용성, C 한국어 표현, 해당 문항의 D 지시사항 준수와 E 정보 부족·불확실성 대응을 그대로 사용했다. 각 응답의 기존 기준 점수 평균을 구한 뒤 공통 5문항의 응답을 동일 가중 평균했다. 점수 근거는 로컬 `docs/eval-results.md`, Cloud `docs/cloud-compare.md`의 각 run_id 블록에 있다.

| Model | 평균 (1~5) | Quality n (응답) | Success / Attempts |
|---|---:|---:|---:|
| Model C (금융) | 2.32 | 10 | 10 / 10 |
| Model D (코딩) | 3.00 | 10 | 10 / 10 |
| Model F (이커머스) | 3.50 | 10 | 10 / 10 |
| Cloud | 4.53 | 5 | 5 / 5 |

Cloud Q10은 `api_status=incomplete`이고 출력 한도 768토큰에 도달했다. 채점표의 기존 4.00점은 그 불완전한 응답에 대한 점수다. 정상 완료 4건만 따로 보면 평균이 달라지므로 임의로 제외하지 않았다.

### Latency

| Model | 평균 전체 응답 시간 (초) |
|---|---:|
| Model C (금융) | 3.40 (n=10) |
| Model D (코딩) | 4.77 (n=10) |
| Model F (이커머스) | 3.86 (n=10) |
| Cloud | 6.97 (n=5) |

현재 실험 환경에서 관측된 전체 응답 시간이다. Local은 로컬 호출, Cloud는 네트워크 왕복과 API 처리를 포함한다. 따라서 이 수치만으로 모델 자체의 생성 속도를 판정할 수 없다.

### Generation Performance

| Model | Local tokens/s | 출력 토큰 평균 | 입력 토큰 평균 | 로딩 시간 평균 (초) | 종료 상태 |
|---|---:|---:|---:|---:|---|
| Model C (금융) | 62.25 (n=10) | 179.70 (n=10) | 53.00 (n=10) | 0.42 (n=10) | stop 10 |
| Model D (코딩) | 66.36 (n=10) | 282.50 (n=10) | 45.00 (n=10) | 0.42 (n=10) | stop 10 |
| Model F (이커머스) | 62.89 (n=10) | 204.90 (n=10) | 45.00 (n=10) | 0.39 (n=10) | stop 10 |
| Cloud | 내부 생성 시간 없음 → 계산 불가 | 486.20 (n=5) | 37.20 (n=5) | 미제공 | completed 4, incomplete 1 |

Local 생성속도와 Cloud의 네트워크 포함 elapsed는 동일 지표가 아니다. Cloud는 내부 생성 시간이 없어 tokens/s를 계산하지 않았다. 입력·출력 토큰은 서로 다른 토크나이저로 측정되어 수치만으로 답변 길이와 장황함을 판단할 수 없다.

#### 종료 상태와 응답 길이

| Model | 정상 종료 | 한도 도달/미완료 | 호출 실패 | 평균 응답 글자 수 |
|---|---:|---:|---:|---:|
| Model C (금융) | 10 | 0 | 0 | 351.6 (n=10) |
| Model D (코딩) | 10 | 0 | 0 | 499.8 (n=10) |
| Model F (이커머스) | 10 | 0 | 0 | 335.8 (n=10) |
| Cloud | 4 | 1 | 0 | 882.8 (n=5) |

Cloud의 `incomplete` 1건은 API 응답이 돌아와 호출 성공 수에는 포함했지만 정상 종료로 세지 않았다. 원본에 `incomplete_details.reason`이 저장되지 않아 원인을 확정할 수 없다. 출력 768토큰과 요청 한도 768토큰이 같다는 점은 한도 도달의 근거다.

### Cost

Cloud 원본 API 사용량은 입력 186토큰, 출력 2431토큰이다. 기록 당시 입력 $0.2/1M, 출력 $1.2/1M, 통화 USD. 요청별 `estimated_cost` 합계는 0.0029544 USD (5회), 평균 0.0005909 USD (n=5)다.
가격 출처: [https://developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing) (설정 파일 확인일 2026-09-16, Standard 단가). 추정 비용은 원본에 저장된 토큰 사용량 × 단가이며 실제 청구액은 기록되지 않았다. 실제 API 청구·사용량은 계정의 사용량 페이지에서 별도 확인이 필요하다.
Local은 API 토큰 과금이 없다. GPU/PC 구입·유지, 전력, 모델 저장 공간, 관리와 운영 비용은 측정하지 않았으므로 금액으로 환산하지 않았다.

### Security

- Local: 데이터와 모델을 직접 통제하고 내부망 서빙으로 외부 전송을 줄일 수 있다. 접근 제어·패치·로그·로컬 보안은 운영자 책임이다.
- Cloud: 질문이 외부 API로 전송된다. 개인정보 최소화와 제공자의 데이터 처리 정책 검토, 서비스 의존 관리가 필요하다.

### Infrastructure / Operations

- Local: 이 실험은 Windows, NVIDIA GeForce RTX 5060 Laptop GPU, RAM 31.4 GB, Ollama 환경에서 수행했다. GPU/PC·모델 다운로드·저장 공간·모델 관리·업데이트·장애 대응·서빙을 운영자가 맡는다.
- Cloud: API 사용에는 자체 GPU가 필요하지 않고 서버 운영 부담이 낮다. 인터넷 연결, API 장애·변경, 사용량·예산 관리는 필요하다.

### Customization

- Local: 모델 선택, 양자화, 자체 서빙과 내부망 배치가 가능하다. 이번 실험은 Q4_K_M 모델을 Ollama로 실행했으며 Fine-tuning은 수행하지 않았다.
- Cloud: 제공 모델과 API 기능 범위에 의존하고 설정 및 서버 내부 제어에 제한이 있다. 이번 실험은 별도 Fine-tuning을 수행하지 않았다.

### Main Trade-offs

- Quality: 공통 질문의 기존 채점에서 Cloud가 높았으나 Q10 미완료와 반복 수 차이를 함께 본다.
- Latency: 이번 환경에서는 Local 전체 응답 시간이 짧았다. Cloud 수치에 네트워크가 포함되어 모델 자체 속도 비교는 불가하다.
- Cost: Cloud의 기록 기반 추정 API 비용은 계산 가능하다. Local 총소유비용은 미측정이다.
- Security: Local은 데이터 통제 범위가 넓고 자체 보안 책임이 따른다. Cloud는 외부 전송과 제공자 정책 확인이 필요하다.
- Operations: Local은 장비·모델·서빙을 관리한다. Cloud는 API·인터넷·사용량 관리에 의존한다.
- Customization: Local은 양자화·자체 서빙 등 제어 범위가 넓다. Cloud는 제공 API 범위에서 설정한다.

### Representative Success / Failure Cases

- Local 성공: F의 Q01 두 회차는 평균 4.50점. 배송 확인 순서를 제시했다 (원본 점수·근거: `docs/eval-results.md`).
- Local 실패: C의 Q04 두 회차 평균 1.75점. 확인되지 않은 환불 가능성을 단정한 응답이 있다.
- Cloud 성공: Q06은 기존 채점 5.00점이며 요청한 FAQ 유형을 제시했다 (`docs/cloud-compare.md`).
- Cloud 실패/제한: Q10은 4.00점으로 채점되었지만 `api_status=incomplete`, 출력 768토큰으로 응답이 끝나 정상 완료되지 않았다.

### Limitations

공통 질문은 5개뿐이고 Local은 질문당 2회, Cloud는 1회다. Local은 단일 Windows/GPU 환경에서 측정했고 Cloud elapsed에는 네트워크가 포함된다. 토크나이저와 모델 계열, 도메인 Fine-tuning 이력이 다르므로 점수·토큰·시간 차이를 단일 원인으로 돌릴 수 없다. 작은 평가셋이며 Cloud Q10 미완료 사유와 실제 청구액은 원본에 없다.

### STEP 08 Handoff

STEP 07에서는 최종 Local 모델을 선정하지 않는다. STEP 08에서 사전 확정한 필수 통과 조건과 모델 선호 우선순위를 적용하고, 최종 Local 1개 선정·선택 및 탈락 이유·운영 권고를 기록한다.

<!-- evalkit:auto:end -->

# Commerce Decision Intelligence — Long-term Roadmap

> **문서 목적**
> 이 문서는 `commerce-decision-intelligence` 저장소의 장기 설계 기준 문서다.
> 향후 각 Phase를 구현할 때 "무엇을 만들 것인가"보다 **"무엇을 만들지 않을 것인가"와 "어떤 기준으로 판단할 것인가"**를 결정하기 위해 참조한다.
> 선언적 비전 문서가 아니라, 설계 결정 시 근거로 인용할 수 있는 운영 문서로 유지한다.

| 항목 | 값 |
|---|---|
| Document version | 0.1 (initial) |
| Status | Draft — Phase 0 진행 중 |
| Current Phase | **Phase 0 — Foundation Model Evaluation** |
| Scope of this doc | Phase 0 ~ Phase 11 장기 계획 |
| Last updated | 2026-09-14 |

---

## 1. Project Vision

### 1.1 한 문장 정의

> 외부 변수와 불확실성이 큰 이커머스 환경에서, **개인 셀러가 자신의 데이터를 근거로 판매 문제를 진단하고, 자신이 통제 가능한 개선안을 저비용으로 선택·실험하며, 그 결과를 축적하여 다음 의사결정의 품질을 높일 수 있도록 지원하는 AI 시스템.**

### 1.2 이 시스템이 하는 일 / 하지 않는 일

| 하는 일 | 하지 않는 일 |
|---|---|
| 관측된 지표 변화로부터 문제를 탐지한다 | 매출 상승을 보장한다 |
| 가능한 원인 가설을 생성하고 근거를 연결한다 | 단일 원인을 단정한다 |
| 통제 가능 요인과 외부 요인을 분리한다 | 외부 요인을 셀러 책임으로 귀속시킨다 |
| 저비용·저위험 개선안을 우선순위화한다 | 고비용 전략을 자동 실행한다 |
| 실험을 설계하고 전후 KPI를 추적한다 | 인과관계를 확정적으로 주장한다 |
| 의사결정 이력을 데이터로 축적한다 | 사람의 최종 판단을 대체한다 |

### 1.3 성공 기준 (장기)

이 프로젝트의 성공은 "매출이 올랐는가"가 아니라 다음으로 측정한다.

1. **진단 재현성** — 동일한 데이터에 대해 일관된 문제 탐지 결과를 내는가
2. **근거 추적성** — 모든 주요 주장에 대해 원본 데이터까지 역추적 가능한가
3. **의사결정 기록률** — 제안된 Action 중 승인/거절/결과가 기록된 비율
4. **실험 전환율** — 제안이 실제 실험으로 연결된 비율
5. **운영 비용** — 월 단위 LLM/인프라 비용이 개인 셀러가 감당 가능한 수준인가
6. **회귀 안정성** — 모델·프롬프트 변경 시 기존 평가 Dataset에서 성능이 유지되는가

---

## 2. Core Problem

### 2.1 문제 정의

개인 이커머스 셀러는 다음 상황에 반복적으로 놓인다.

```text
관측: "지난주 대비 매출이 30% 떨어졌다"
      ↓
현실: 원인 후보가 최소 10개 이상이고, 대부분 셀러가 통제할 수 없다
      ↓
결과: 근거 없이 가격을 내리거나 광고비를 올린다 → 비용만 증가
```

### 2.2 왜 기존 도구로 해결되지 않는가

| 기존 접근 | 한계 |
|---|---|
| 플랫폼 기본 대시보드 | 지표는 보여주지만 원인 해석과 행동 제안이 없다 |
| 일반 LLM 챗봇 | 셀러의 실제 데이터에 근거하지 않는다 (Hallucination) |
| PDF RAG | 문서는 검색하지만 정형 데이터 분석·의사결정이 없다 |
| 컨설팅 / 대행사 | 개인 셀러의 비용 감당 범위를 초과한다 |
| 자동화 Agent 데모 | 신뢰성·근거·비용 통제가 없어 실무 적용이 어렵다 |

### 2.3 핵심 난점

1. **귀인(attribution) 문제** — 매출 변화의 원인을 단일 요인으로 특정할 수 없다.
2. **통제 가능성 문제** — 원인을 알아도 셀러가 바꿀 수 없는 것이 다수다.
3. **비용 제약** — 개인 셀러는 대규모 인프라·API 비용을 감당할 수 없다.
4. **데이터 희소성** — 개인 셀러의 표본(주문 수, 리뷰 수)은 통계적으로 작다.
5. **신뢰 문제** — LLM의 자연어 추론만으로는 금전적 의사결정을 맡길 수 없다.

이 다섯 가지 난점이 이후 모든 설계 원칙의 근거다.

---

## 3. Design Principles

### P1. 매출 직접 보장 금지 — Observation-to-Feedback Loop 준수

시스템은 아래 흐름을 벗어나지 않는다. 중간 단계를 건너뛴 결론은 출력하지 않는다.

```text
Observation
→ Problem Detection
→ Hypothesis Generation
→ Evidence Collection
→ Internal / External Factor Classification
→ Controllability Assessment
→ Improvement Candidate Generation
→ Cost / Risk / Expected Impact Evaluation
→ Human Approval
→ Execution
→ Outcome Measurement
→ Feedback
```

금지 패턴:

```text
[X] 매출 하락 → "가격이 비쌉니다" → 가격 인하 제안
[O] 매출 하락 → CVR/CTR/노출 분해 → 가설 3개 + 각 근거/신뢰도/통제가능성 → 저비용 실험 제안
```

### P2. 비용 최소화는 기능이 아니라 제약조건이다

| 원칙 | 구체 기준 |
|---|---|
| Local-first | 기본 추론은 로컬(Ollama)에서 수행 |
| Open-source 우선 | 유료 대안 도입 전 OSS 대안을 먼저 검토·기록 |
| 계산은 코드로 | 집계·통계·이상치 탐지는 Python/SQL. LLM에 맡기지 않는다 |
| Cloud는 제한적으로 | 고난도 추론 또는 Local confidence 미달 시에만 |
| 가벼운 저장소부터 | 초기 SQLite / DuckDB / 파일 기반. 필요 시 교체 가능하도록 추상화 |
| 인프라 종속 회피 | 관리형 Vector DB, 상시 과금 서비스, 클러스터 인프라는 초기 도입 금지 |

**설계 규칙:** 새 컴포넌트 도입 시 "이것 없이 동작하는가?"와 "월 고정비가 발생하는가?"를 먼저 기록한다.

### P3. 역할 분리 — LLM이 모든 판단을 하지 않는다

```text
Python / SQL          LLM                      Rules / Policy        Human
─────────────────     ─────────────────        ───────────────       ──────────────
데이터 계산           상황 해석                 금지 행동             고위험 승인
KPI 산출              가설 생성                 실행 제약             최종 판단
통계 분석             Evidence 연결             Risk Control          피드백 제공
이상치 탐지           개선안 생성               비용 상한
세그먼트 분해         설명 및 보고              데이터 접근 범위
```

**판정 기준:** 결정적(deterministic) 답이 존재하는 작업은 코드로 처리한다. LLM은 "여러 해석이 가능한 영역"에만 투입한다.

### P4. Evidence-grounded Decision

모든 주요 판단은 다음 구조를 갖는다.

```text
Claim:
  최근 각도조절 관련 고객 불만이 증가했다.

Evidence:
  - review_2026_08 (n=142, 각도 관련 언급 18건, 12.7%)
  - review_2026_07 (n=130, 각도 관련 언급 6건,  4.6%)
  - cs_inquiry_2026_08 (각도 관련 문의 9건)

Confidence:
  MEDIUM   # 표본 작음, 관측 기간 짧음

Controllability:
  PARTIAL  # 상세페이지 설명은 통제 가능, 제품 구조 변경은 단기 불가

Recommended Action:
  상세페이지 사용 방법 안내 개선 (저비용 / 저위험 / 되돌리기 가능)

Expected Signal:
  각도 관련 CS 문의 비율, 상세페이지 체류시간
```

**규칙:**
- Evidence가 없는 Claim은 출력하지 않거나 `INSUFFICIENT_EVIDENCE`로 표기한다.
- Evidence는 원본 레코드 ID까지 추적 가능해야 한다.
- Confidence는 표본 크기·기간·데이터 품질을 반영한다.
- 단순히 LLM의 자연어 추론만으로 중요한 판단을 확정하지 않는다.

### P5. Controllability First

원인 후보는 반드시 다음 4분류 중 하나로 태깅한다.

| 분류 | 정의 | 시스템 동작 |
|---|---|---|
| `CONTROLLABLE` | 셀러가 직접 변경 가능 (상세페이지, 가격, 광고 소재, 재고) | 개선안 생성 대상 |
| `PARTIALLY_CONTROLLABLE` | 간접 영향만 가능 (노출, 리뷰 평점, 검색 순위) | 영향 경로를 명시하고 제안 |
| `EXTERNAL` | 통제 불가 (시장 수요, 계절성, 플랫폼 정책, 경쟁사 가격, 광고 환경, 소비 트렌드) | **행동 제안 금지. 모니터링/적응만 제안** |
| `UNKNOWN` | 근거 부족 | 추가 데이터 수집을 제안 |

**핵심:** 매출 하락의 원인이 `EXTERNAL`로 판정되면 시스템은 "지금 할 수 있는 통제 가능한 행동이 없다 + 관측 유지"를 명확히 말해야 한다. 억지 개선안 생성은 실패로 간주한다.

### P6. 저위험·되돌릴 수 있는 개선 우선

개선안은 다음 축으로 점수화한다.

```text
Priority Score ~ f(Expected Impact, Cost, Risk, Reversibility, Time-to-signal)
```

| 축 | 설명 | 비고 |
|---|---|---|
| Cost | 금전/시간 비용 | 무료 텍스트 수정 < 광고비 증액 |
| Risk | 실패 시 손실 | 가격 인하는 고위험(마진 직접 훼손) |
| Time-to-signal | 결과 확인까지 걸리는 기간 | 표본이 적으면 길어짐 |
| Reversibility | 되돌릴 수 있는가 | 되돌릴 수 없는 Action은 반드시 Human Approval |

### P7. Human-in-the-loop by Default

자동 실행은 기본값이 아니다. 초기에는 **외부에 영향을 주는 모든 Action에 대해 사람 승인**을 요구한다. 자동화는 다음 조건이 모두 충족된 Action 유형에 한해 점진적으로 허용한다.

1. 충분한 승인 이력 축적 (해당 유형에서 반복 승인)
2. 되돌리기 가능
3. 비용 상한 내
4. 회귀 테스트 통과

### P8. Evaluation-first Development

새 기능은 "평가 방법"을 먼저 정의한 뒤 구현한다. 평가 불가능한 기능은 도입을 보류한다.

### P9. 점진적 복잡도 (Progressive Complexity)

Agent를 처음부터 복잡하게 만들지 않는다. 다음 순서로만 복잡도를 올린다.

```text
단일 프롬프트
→ 프롬프트 + 검색(RAG)
→ + 코드 기반 데이터 분석
→ + 단일 Tool Call
→ + 다중 Tool + 상태 관리
→ + Planning / Retry
→ + Multi-step Agent
```

**승급 조건:** 이전 단계가 평가 Dataset에서 안정적으로 동작하고, **다음 단계 없이는 해결할 수 없는 실패 사례가 실제로 관측될 때만** 다음 단계로 간다. 복잡도는 목표가 아니라 관측된 필요에 대한 대응이다.

---

## 4. Data Strategy

### 4.1 데이터 계층

#### (A) Internal / Owned Data — 셀러가 이미 보유

| 그룹 | 항목 | 형태 |
|---|---|---|
| Product | 상품 정보, 상품 스펙, 상품 이미지, 상세페이지 | 정형 + 텍스트 + 이미지 |
| Commerce | 판매 데이터, 주문 데이터, 가격, 재고 | 정형 (시계열) |
| Marketing | 광고 데이터 (노출/클릭/비용/전환) | 정형 (시계열) |
| Voice | 리뷰, VOC, CS 데이터, FAQ | 비정형 텍스트 (+ 이미지) |
| History | 상품 변경 이력, 광고 변경 이력, 가격 변경 이력, 상세페이지 변경 이력 | 이벤트 로그 |

> **History가 가장 중요하다.** "언제 무엇을 바꿨는가"가 없으면 전후 비교 자체가 불가능하다.
> Phase 3 이전에 변경 이력 기록 체계를 먼저 확보한다.

#### (B) External / Context Data — 참고용, 통제 불가

시장 수요, 계절성, 플랫폼 노출 변화, 경쟁 상품, 경쟁사 가격, 광고 환경, 플랫폼 정책, 소비 트렌드.

→ 수집 가능한 범위에서만 다루고, **항상 `EXTERNAL`로 태깅**한다. 실험 해석 시 교란 변수(confounder) 확인용으로 사용한다.

#### (C) AI-generated Operational Data — 시스템이 스스로 생성

| 항목 | 용도 |
|---|---|
| 문제 상황 (Situation) | 진단 재현성 검증 |
| Agent가 확인한 Evidence | Groundedness 평가 |
| 생성된 가설 / 선택한 가설 | Reasoning 품질 평가 |
| Confidence | Calibration 평가 |
| 추천 Action | 제안 품질 평가 |
| 사용자 승인 / 거절 (+사유) | Preference Dataset |
| 실제 실행 Action | 실행 정확도 |
| Tool call history | Tool selection / argument 정확도 |
| 실패 및 retry 기록 | Recovery 성공률 |
| Action 전후 KPI | Outcome 측정 |
| 최종 Outcome | 의사결정 품질 |
| 사용자 피드백 | Feedback Loop |

### 4.2 목표 축적 구조

```text
Situation + Evidence + Decision + Action + Outcome + Human Feedback
```

이 6-튜플이 **이 프로젝트의 가장 중요한 자산**이다. 코드보다 이 데이터가 오래 남는다.

개념 스키마 (구현체는 Phase 4~5에서 확정):

```text
decision_record
├── id, created_at, product_id
├── situation        : 관측 지표 스냅샷 + 탐지된 이상
├── evidence[]       : {source_type, source_ids[], summary, strength}
├── hypotheses[]     : {text, factor_class, confidence, supporting_evidence_ids[]}
├── selected_hypothesis_id
├── recommended_actions[] : {text, cost, risk, reversibility, expected_signal}
├── human_decision   : APPROVED | REJECTED | MODIFIED (+ reason)
├── executed_action  : {type, params, executed_at, tool_calls[]}
├── outcome          : {before_kpi, after_kpi, window, external_conditions}
├── feedback         : {useful: bool, comment, rating}
└── versions         : {model, prompt_version, rules_version}
```

### 4.3 이 데이터의 향후 용도

* Evaluation Dataset — 진단/제안 품질 평가
* Regression Test Dataset — 모델·프롬프트 변경 시 회귀 검증
* Preference Dataset — 승인/거절 쌍으로부터 선호 학습
* Fine-tuning Dataset — 충분히 축적된 후에만
* Model Routing 개선 — 어떤 Task에 어떤 모델이 충분했는지
* Decision Model 개선 — 어떤 유형의 제안이 실제로 효과가 있었는지

> **Fine-tuning은 초기 목표가 아니다.** 데이터가 충분하고, 프롬프트·RAG·Routing으로 해결되지 않는 명확한 실패 패턴이 확인되었을 때만 검토한다.

### 4.4 데이터 원칙

1. **Raw 보존** — 원본은 절대 덮어쓰지 않는다. 파생 데이터는 별도 레이어.
2. **Provenance 필수** — 모든 파생 지표는 계산식과 소스 레코드를 기록한다.
3. **Local 우선** — 개인정보/주문 데이터는 기본적으로 외부 API로 보내지 않는다.
4. **PII 최소화** — 고객 식별 정보는 저장 단계에서 마스킹/제거.
5. **표본 크기 명시** — 모든 지표는 `n`을 함께 보고한다. 개인 셀러 데이터는 작다.

---

## 5. System Architecture Vision

### 5.1 최종 지향 구조

```text
Commerce Data
     │
     ├─ Product
     ├─ Sales
     ├─ Ads
     ├─ Reviews
     ├─ VOC
     ├─ CS
     └─ Operational History
             ↓
        Data Layer
             ↓
    Metrics / Analytics
             ↓
   Knowledge / Retrieval
             ↓
 Situation Understanding
             ↓
 Hypothesis / Diagnosis
             ↓
 Evidence Validation
             ↓
 Decision Intelligence
             ↓
 Cost / Risk Evaluation
             ↓
    Human Approval
             ↓
     Tool Execution
             ↓
    Outcome Tracking
             ↓
 Evaluation / Observability
             ↓
     Feedback Dataset
             ↓
 Continuous Improvement
```

### 5.2 레이어별 책임과 도입 Phase

| # | Layer | 책임 | 주 구현 수단 | 도입 Phase |
|---|---|---|---|---|
| 1 | Data Layer | 원본 수집·정규화·이력 저장 | SQLite / DuckDB / Parquet | 3 |
| 2 | Metrics / Analytics | KPI 산출, 세그먼트 분해, 이상치 탐지 | Python / SQL | 3 |
| 3 | Knowledge / Retrieval | 문서·정책·상품지식 검색 | Embedding + Vector Search | 1 |
| 4 | Situation Understanding | 지표 + 문맥을 상황으로 서술 | LLM | 3~4 |
| 5 | Hypothesis / Diagnosis | 원인 가설 생성 | LLM | 4 |
| 6 | Evidence Validation | 가설↔근거 연결, 신뢰도 산정 | Code + LLM | 4 |
| 7 | Decision Intelligence | 통제가능성 분류, 개선안 생성 | LLM + Rules | 4 |
| 8 | Cost / Risk Evaluation | 비용·위험·우선순위 점수화 | Rules / Code | 4 |
| 9 | Human Approval | 승인 인터페이스, 사유 기록 | CLI / UI | 4~6 |
| 10 | Tool Execution | 도구 호출, 실행 기록 | Tool Calling | 6 |
| 11 | Outcome Tracking | 전후 KPI 비교, 교란 변수 기록 | Code | 5 |
| 12 | Evaluation / Observability | Trace, 평가, 회귀 테스트 | 자체 하네스 | 2, 8 |
| 13 | Feedback Dataset | 6-튜플 축적 | Storage | 4~11 |
| 14 | Continuous Improvement | 실패 사례 → 개선 | Process | 11 |

### 5.3 아키텍처 제약

* 각 레이어는 **아래 레이어의 출력만** 입력으로 받는다. 레이어 건너뛰기 금지.
* LLM 호출은 **레이어 4 이상**에서만 발생한다. 레이어 1~2는 순수 코드.
* 모든 레이어는 **입출력을 Trace에 기록**한다 (Phase 8).
* 저장소·모델·Vector DB는 **인터페이스 뒤에 둔다.** 교체 비용을 낮게 유지한다.

---

## 6. Development Phases

> 각 Phase는 **이전 Phase의 Exit Criteria가 충족된 뒤**에만 시작한다.
> Phase 번호는 우선순위이자 의존 순서다.

### Phase 0 — Foundation Model Evaluation ← **현재**

**목표:** 이후 모든 Phase의 기반이 될 Local LLM을 근거를 갖고 선정한다.

| 항목 | 내용 |
|---|---|
| 범위 | Ollama 기반 Local LLM 2개 비교 + Cloud API LLM 1개 소규모 비교 |
| 입력 | 동일한 이커머스 평가 질문 세트 |
| 평가축 | 한국어 성능, Instruction Following, Groundedness, Hallucination, 응답 속도, 실행 자원, 비용 |
| 산출물 | 평가 질문 세트, 응답 기록, 비교표, 기반 모델 선정 근거 |
| 기간 | 4일 |

**Exit Criteria**
- [ ] 동일 질문 세트에 대한 3개 모델 응답이 기록되어 있다
- [ ] 각 평가축에 대한 비교 결과가 표로 정리되어 있다
- [ ] 기반 모델 1개가 **근거와 함께** 선정되었다
- [ ] 로컬 실행 자원(RAM/VRAM/토큰 속도) 실측치가 기록되어 있다
- [ ] Phase 1에서 재사용할 평가 질문 세트가 파일로 남아 있다

---

### Phase 1 — Domain Knowledge / RAG

**목표:** 상품 정보·운영 문서·FAQ·정책·내부 자료를 검색하여 근거 있는 답변을 생성하는 Knowledge Layer 구축.

| 항목 | 내용 |
|---|---|
| 학습/구현 대상 | Chunking, Embedding, Vector Search, Retrieval, Reranking, Metadata filtering, Grounded generation |
| 비용 기준 | Local embedding 모델 우선. 관리형 Vector DB 도입 금지 |
| 저장소 후보 | SQLite + 벡터 확장 / 파일 기반 인덱스 / 경량 로컬 Vector DB |

**핵심 설계 결정**
- 답변에는 항상 **출처(문서 ID + chunk)를 첨부**한다.
- 검색 결과가 부족하면 **답변하지 않고 `INSUFFICIENT_CONTEXT`를 반환**한다.
- Metadata filtering(상품 ID, 기간, 문서 유형)을 초기부터 설계에 포함한다.

**Exit Criteria**
- [ ] 내부 문서 질의에 대해 출처가 첨부된 답변이 생성된다
- [ ] 근거 부족 시 답변을 거부하는 동작이 확인된다
- [ ] Retrieval 품질을 수동으로라도 측정한 기록이 있다

---

### Phase 2 — LLM / RAG Evaluation System

**목표:** 단발 평가가 아니라 **반복 실행 가능한 평가 시스템**을 만든다. 이후 모든 변경의 안전망.

**평가 항목 후보**

| 구분 | 항목 |
|---|---|
| 정확성 | Answer correctness, Groundedness, Hallucination |
| 검색 | Retrieval relevance, Retrieval recall |
| 순응성 | Instruction following |
| 운영 | Latency, Token usage, Cost |

**요구사항**
- 동일 Dataset으로 **모델/프롬프트 변경 전후 Regression Test** 가능
- 결과는 버전과 함께 저장되어 시계열 비교 가능
- 평가 자체의 비용도 측정 (LLM-as-judge 사용 시 특히)

**Exit Criteria**
- [ ] 고정 평가 Dataset이 존재한다
- [ ] 단일 명령으로 전체 평가가 재실행된다
- [ ] 두 모델/프롬프트 버전의 점수 비교표가 생성된다
- [ ] 평가 실행 비용이 기록된다

---

### Phase 3 — Commerce Data Intelligence

**목표:** 정형 데이터 분석을 시스템에 편입한다. **LLM은 계산하지 않는다.**

```text
Raw Data → Metrics → Detection → LLM Interpretation
```

| 단계 | 수단 | 산출 |
|---|---|---|
| Raw Data | 파일/DB 적재 | 정규화된 테이블 + 변경 이력 |
| Metrics | Python / SQL | 판매량, CTR, CVR, 광고 지표(ROAS 등), 가격, 재고, 리뷰 변화 |
| Detection | 통계 코드 | 이상치, 추세 변화, 세그먼트 이상 |
| Interpretation | LLM | 지표 변화의 서술적 해석 (원인 단정 금지) |

**설계 규칙**
- LLM에는 **계산된 지표와 그 정의만** 전달한다. 원시 행(raw rows)을 대량으로 넣지 않는다.
- 모든 지표는 `n`(표본 크기)과 기간을 함께 전달한다.
- 이상치 판정 기준(임계값/방법)은 코드와 문서에 명시한다.

**Exit Criteria**
- [ ] 판매/광고/리뷰 데이터가 조회 가능한 형태로 적재된다
- [ ] 핵심 KPI가 코드로 재현 가능하게 산출된다
- [ ] 이상 구간 탐지가 규칙 기반으로 동작한다
- [ ] LLM 해석 출력이 계산 결과를 인용한다

---

### Phase 4 — Diagnosis & Decision Intelligence

**목표:** 데이터 요약을 넘어 **진단과 의사결정**으로 간다. 이 프로젝트의 핵심 Phase.

```text
Problem
→ Cause Candidates
→ Evidence
→ Hypothesis
→ Confidence
→ Controllability
→ Recommended Experiment
```

**필수 구성요소**
1. **Factor Classification** — `CONTROLLABLE` / `PARTIALLY_CONTROLLABLE` / `EXTERNAL` / `UNKNOWN` (P5)
2. **Evidence Binding** — 가설마다 근거 레코드 ID 연결 (P4)
3. **Confidence Calibration** — 표본 크기·기간·데이터 품질 반영
4. **Cost / Risk Scoring** — 개선안 우선순위 (P6)
5. **Decision Record 저장** — §4.2 스키마

**실패로 간주하는 동작**
- 근거 없이 가설을 생성한다
- `EXTERNAL` 요인에 대해 개선안을 만들어낸다
- 표본이 극히 작은데 `HIGH` confidence를 부여한다
- 가장 비싼 안(광고비 증액, 가격 인하)을 최우선으로 제안한다

**Exit Criteria**
- [ ] 하나의 문제 상황에서 복수 가설 + 각각의 근거/신뢰도/통제가능성이 출력된다
- [ ] 개선안이 비용·위험 기준으로 정렬된다
- [ ] Decision Record가 저장된다
- [ ] 근거 부족 시 "판단 불가"를 반환하는 경로가 동작한다

---

### Phase 5 — Experimentation System

**목표:** AI가 제안한 개선안을 실제 실험으로 연결하고 결과를 측정한다.

```text
Problem             CVR 하락
Hypothesis          사용방법 전달 부족
Action              상세페이지 설명 수정
Before KPI          CVR 4.2%  (n=310, 2026-08-01~08-14)
After  KPI          CVR 5.0%  (n=295, 2026-08-15~08-28)
External Conditions 가격 동일, 광고 예산 동일, 시즌 이벤트 없음
Result              Possible improvement (표본 작음 — 확정 아님)
```

**설계 규칙**
- **매출 하나만으로 성공 여부를 판정하지 않는다.** 가설과 직접 연결된 중간 KPI를 주 지표로 쓴다.
- 실험 전 **성공 기준과 관측 기간을 미리 선언**한다 (사후 기준 변경 금지).
- **교란 변수(External Conditions)를 반드시 기록**한다. 기록이 없으면 결과 해석을 보류한다.
- 표본이 작으면 결과는 `INCONCLUSIVE`로 남긴다. 억지 결론 금지.
- 한 번에 하나의 변경만 적용하는 것을 기본으로 한다.

**Exit Criteria**
- [ ] 실험 정의(가설/Action/지표/기간/기준)가 사전 기록된다
- [ ] 전후 KPI가 자동 산출된다
- [ ] 교란 변수 체크리스트가 결과에 포함된다
- [ ] `IMPROVED / NO_CHANGE / WORSENED / INCONCLUSIVE` 판정이 나온다

---

### Phase 6 — Tool Calling & Workflow

**목표:** 시스템이 필요한 도구를 호출할 수 있도록 확장한다. 단, **자동 실행보다 Human Approval 우선.**

**도구 후보**

| 유형 | 예시 | 부작용 |
|---|---|---|
| 조회 | 상품 데이터 조회, 데이터베이스 조회, 검색 | 없음 (자동 허용) |
| 분석 | 리뷰 분석, CSV 분석 | 없음 (자동 허용) |
| 생성 | 보고서 생성 | 낮음 |
| 변경 | Task 생성, 상세페이지 수정안 저장 | **Human Approval 필수** |

**설계 규칙**
- 도구를 **부작용 유무로 분류**하고, 부작용 있는 도구는 승인 게이트를 통과해야 실행된다.
- 모든 Tool call은 인자·결과·소요시간·성공여부를 Trace에 기록한다.
- Stateful Workflow는 중간 상태를 저장하여 중단·재개가 가능해야 한다.

**Exit Criteria**
- [ ] 조회/분석 도구가 안정적으로 호출된다
- [ ] 부작용 있는 도구는 승인 없이 실행되지 않는다
- [ ] Tool call 이력이 저장된다

---

### Phase 7 — Agent Reliability Engineering

**목표:** 일반적인 Agent 데모와의 결정적 차이. **실패를 전제로 설계한다.**

```text
Plan → Execute → Observe → Validate → Retry / Replan → Escalate
```

**대응 대상**

| 실패 유형 | 대응 |
|---|---|
| Tool failure | 재시도(백오프) → 대체 도구 → Escalate |
| Invalid arguments | 스키마 검증 후 인자 수정 재시도 (횟수 제한) |
| Missing evidence | 추가 수집 시도 → 실패 시 `INSUFFICIENT_EVIDENCE` 반환 |
| Hallucination | 출력 검증(근거 ID 실재 여부 확인) → 실패 시 재생성 |
| Conflicting evidence | 충돌 명시 + confidence 하향 + 사람 판단 요청 |
| Timeout | 부분 결과 반환 + 미완료 표시 |
| Loop / 반복 실패 | 시도 상한 도달 시 즉시 Escalate |

**설계 규칙**
- 재시도 횟수·총 비용·총 시간에 **명시적 상한**을 둔다 (비용 폭주 방지, P2).
- 실패를 조용히 숨기지 않는다. 부분 실패는 결과에 표기한다.
- Escalate는 정상 경로다. "사람에게 넘김"을 실패로 취급하지 않는다.

**Exit Criteria**
- [ ] 주요 실패 유형별 처리 경로가 구현·테스트되었다
- [ ] 재시도/비용 상한이 강제된다
- [ ] Escalation 경로가 동작한다
- [ ] 실패 및 recovery 기록이 저장된다

---

### Phase 8 — Agent Evaluation & Observability

**목표:** 최종 응답만이 아니라 **실행 궤적(trajectory) 전체**를 평가한다.

**평가 항목 후보**

| 구분 | 항목 |
|---|---|
| 도구 | Tool selection accuracy, Tool argument accuracy |
| 추론 | Plan quality, Evidence usage, Trajectory quality |
| 결과 | Task completion, Recovery success |
| 운영 | Latency, Cost, Failure rate |

**추적 대상**

```text
User Request → Retrieval → Model Call → Decision → Tool Call → Result → Retry → Final Decision
```

**요구사항**
- 각 단계의 입력/출력/소요시간/토큰/비용을 기록한다.
- 하나의 요청은 단일 trace ID로 전 과정을 재구성할 수 있어야 한다.
- Observability 도구는 **로컬에서 동작하는 가벼운 것**을 우선 검토한다 (P2).

**Exit Criteria**
- [ ] 단일 요청의 전체 궤적을 재구성할 수 있다
- [ ] Trajectory 기반 평가가 Phase 2 하네스와 통합된다
- [ ] 요청당 비용/지연이 집계된다

---

### Phase 9 — Local / Cloud Model Routing

**목표:** 모든 작업을 같은 모델에 보내지 않는다. **품질과 비용의 명시적 교환.**

```text
Simple classification   → Local LLM
Internal Q&A            → Local LLM
Sensitive data          → Local LLM (외부 전송 금지)
Complex reasoning       → Cloud LLM
High-risk decision      → High-capability model + Human Approval
```

**Routing 기준**

| 기준 | 설명 |
|---|---|
| Task complexity | 작업 유형별 사전 분류 |
| Confidence | Local 결과의 신뢰도가 임계 미만이면 승급 |
| Latency | 대화형 응답은 Local 우선 |
| Cost | 일/월 Cloud 비용 상한을 강제 |
| Privacy | 주문/고객 데이터 포함 시 Local 고정 |
| Context length | 긴 문맥이 필요하면 승급 |
| Model capability | 요구 능력이 Local 한계를 넘으면 승급 |

**설계 규칙**
- Routing 결정과 사유를 Trace에 기록한다. 이후 Routing 개선의 학습 데이터가 된다.
- Cloud 비용 상한 도달 시 **자동으로 Local로 강등**하고 사용자에게 고지한다.
- Privacy 규칙은 Routing 최우선 조건이며 비용/품질 사유로 우회되지 않는다.

**Exit Criteria**
- [ ] Task 유형별 기본 라우팅 정책이 정의·구현되었다
- [ ] Cloud 비용 상한이 강제된다
- [ ] 민감 데이터의 외부 전송 차단이 검증되었다
- [ ] Routing 결정이 기록된다

---

### Phase 10 — Multimodal Commerce Intelligence

**목표:** 텍스트뿐 아니라 이미지까지 분석 범위를 확장한다.

```text
Image + Product Metadata + Review + Sales Data
                 ↓
         Multimodal Analysis
```

**대상:** 상품 이미지, 상세페이지 이미지, 리뷰 이미지, 경쟁상품 이미지, 상품 스펙 + 텍스트

**활용 예시**
- 리뷰 이미지에서 반복 등장하는 불량/오해 패턴 탐지
- 상세페이지 이미지가 실제 스펙과 불일치하는지 확인
- 썸네일 변경 이력과 CTR 변화의 대응 관계 관측

**설계 규칙**
- 이미지 분석은 비용이 크다. **텍스트로 해결되지 않는 경우에만** 사용한다 (P2).
- 로컬 멀티모달 모델을 우선 검토하고, 실행 자원 실측 후 도입을 결정한다.
- 이미지 기반 주장도 동일하게 Evidence 구조를 따른다 (P4).

**Exit Criteria**
- [ ] 로컬 멀티모달 실행 가능성과 자원 소요가 실측되었다
- [ ] 이미지 기반 주장에 출처(이미지 ID)가 첨부된다
- [ ] 이미지 분석 호출 빈도/비용이 통제된다

---

### Phase 11 — Learning / Continuous Improvement

**목표:** 장기간 축적된 운영 데이터로 시스템 자체를 개선한다.

```text
Production Trace → Failure Cases → Evaluation Dataset → Regression Test → Prompt / Model Improvement
```

**기본 루프 (저비용)**
1. Trace에서 실패·거절 사례 수집
2. 평가 Dataset에 편입
3. 개선 (프롬프트 → 검색 → 규칙 순)
4. Regression Test로 회귀 없음 확인
5. 배포 및 재관측

**고급 옵션 (조건부)**

| 옵션 | 도입 조건 |
|---|---|
| Fine-tuning | 충분한 고품질 데이터 + 프롬프트/RAG로 해결 불가한 반복 실패 패턴 확인 |
| Preference optimization | 승인/거절 쌍이 충분히 축적 |
| Specialized classifier | 특정 분류 작업이 반복되고 LLM 비용이 과다 |
| Routing model | Routing 결정 데이터 축적 후 |
| Reward / scoring model | 평가 비용이 과다하고 판정 기준이 안정화된 후 |

> **원칙:** Fine-tuning은 목표가 아니라 수단이다. "데이터가 충분하고, 더 싼 방법으로 해결되지 않을 때"만 도입한다.

**Exit Criteria**
- [ ] 실패 사례가 평가 Dataset으로 편입되는 경로가 있다
- [ ] 개선 → 회귀 테스트 → 배포 루프가 반복 실행된다
- [ ] 개선 전후의 평가 점수 변화가 기록된다

---

### 6.12 Phase 요약표

| Phase | 이름 | 핵심 산출물 | 주 기술 | 상태 |
|---|---|---|---|---|
| 0 | Foundation Model Evaluation | 기반 모델 선정 근거 | Ollama, 평가 질문 세트 | **진행 중** |
| 1 | Domain Knowledge / RAG | Knowledge Layer | Embedding, Vector Search | 예정 |
| 2 | LLM / RAG Evaluation System | 평가 하네스 | 자체 하네스 | 예정 |
| 3 | Commerce Data Intelligence | Metrics + Detection | Python / SQL / DuckDB | 예정 |
| 4 | Diagnosis & Decision Intelligence | Decision Record | LLM + Rules | 예정 |
| 5 | Experimentation System | 실험 기록·판정 | Code | 예정 |
| 6 | Tool Calling & Workflow | Tool Layer | Tool Calling | 예정 |
| 7 | Agent Reliability Engineering | 실패 복구 경로 | Plan / Retry / Escalate | 예정 |
| 8 | Agent Evaluation & Observability | Trace + 궤적 평가 | Tracing | 예정 |
| 9 | Local / Cloud Model Routing | Routing 정책 | Router | 예정 |
| 10 | Multimodal Commerce Intelligence | 이미지 분석 | Multimodal LLM | 예정 |
| 11 | Learning / Continuous Improvement | 개선 루프 | Dataset / (옵션) FT | 예정 |

---

## 7. Evaluation Strategy

### 7.1 평가 계층

| Level | 대상 | 도입 Phase | 예시 지표 |
|---|---|---|---|
| L1 | 모델 단독 | 0 | 한국어 품질, Instruction following, 속도, 실행 자원 |
| L2 | RAG 파이프라인 | 1~2 | Retrieval relevance/recall, Groundedness, Hallucination |
| L3 | 분석 정확성 | 3 | KPI 계산 정확도(단위 테스트), 이상치 탐지 정밀도/재현율 |
| L4 | 진단·의사결정 품질 | 4 | 가설 타당성, Evidence 연결률, Controllability 분류 정확도, Confidence calibration |
| L5 | Agent 궤적 | 7~8 | Tool selection/argument accuracy, Plan quality, Recovery success |
| L6 | 결과(Outcome) | 5, 11 | 실험 판정 정확성, 제안 채택률, 사용자 피드백 |

### 7.2 평가 원칙

1. **고정 Dataset** — 평가 데이터는 버전 고정. 무단 변경 금지.
2. **Regression 우선** — 모든 변경은 기존 Dataset에서 회귀 여부를 먼저 확인.
3. **결정적 항목은 코드로** — KPI 계산 정확도는 LLM 판정이 아니라 단위 테스트로.
4. **LLM-as-judge는 제한적으로** — 비용이 들고, 판정자도 평가 대상이다. 사용 시 판정 기준과 판정 모델 버전을 기록.
5. **비용도 지표다** — 정확도 향상이 비용 증가를 정당화하는지 항상 함께 본다.
6. **표본 크기 표기** — 개인 셀러 데이터는 작다. 평가 결과에도 `n`을 명시한다.

### 7.3 회귀 테스트 트리거

다음 변경 시 전체 평가를 재실행한다.

- 기반 모델 교체 / 버전 변경
- 프롬프트 수정
- 검색 파라미터(chunk size, top-k, reranker) 변경
- 규칙(Controllability 분류, Risk scoring) 변경
- Routing 정책 변경

---

## 8. Cost Strategy

### 8.1 비용 통제 규칙

| # | 규칙 |
|---|---|
| C1 | 계산 가능한 것은 LLM에 맡기지 않는다 (집계·통계·수식) |
| C2 | 기본 경로는 Local LLM. Cloud는 예외 경로다 |
| C3 | Cloud 호출은 일/월 비용 상한을 강제하고, 초과 시 Local로 강등 |
| C4 | 상시 과금 인프라(관리형 DB, 관리형 Vector DB, 상시 서버)는 초기 도입 금지 |
| C5 | 저장소는 SQLite / DuckDB / Parquet 등 파일 기반에서 시작 |
| C6 | 컨텍스트 길이를 통제한다. 원시 데이터 대량 투입 금지 (집계 후 투입) |
| C7 | 반복되는 동일 질의는 캐싱한다 |
| C8 | 이미지/멀티모달은 텍스트로 해결 불가할 때만 (Phase 10) |
| C9 | 평가 실행 비용도 측정 대상에 포함한다 |
| C10 | 새 의존성 도입 시 "월 고정비 발생 여부"를 문서에 기록한다 |

### 8.2 비용 관측

Phase 8 이후 다음을 요청 단위로 기록한다.

```text
request_id, phase, model, route_reason, input_tokens, output_tokens,
latency_ms, estimated_cost, cache_hit
```

집계 대상: 일/월 총비용, Task 유형별 비용, Cloud 대비 Local 비율, 캐시 적중률.

### 8.3 인프라 교체 경로

초기 선택은 **교체를 전제로** 한다. 아래 시점에만 상위 기술을 검토한다.

| 현재 | 교체 검토 시점 | 후보 |
|---|---|---|
| SQLite / DuckDB | 데이터 규모·동시성 한계 도달 | PostgreSQL |
| 파일 기반 벡터 인덱스 | 검색 지연/규모 한계 도달 | 로컬 Vector DB |
| 단일 머신 | 처리량 한계 | 수평 확장 검토 |

> 한계에 도달했다는 **측정 근거 없이 교체하지 않는다.**

---

## 9. Reliability Strategy

### 9.1 신뢰성의 정의

이 시스템에서 신뢰성은 "항상 답을 내는 것"이 아니라 **"틀린 답을 확신 있게 내지 않는 것"**이다.

### 9.2 계층별 방어

| 계층 | 방어 수단 |
|---|---|
| 입력 | 데이터 스키마 검증, 결측/이상 데이터 표시 |
| 계산 | 코드 단위 테스트, 지표 정의 고정 |
| 검색 | 근거 부족 시 `INSUFFICIENT_CONTEXT` 반환 |
| 생성 | 출력 스키마 검증, Evidence ID 실재 여부 확인 |
| 판단 | Confidence 하한, Controllability 필수 태깅 |
| 실행 | 부작용 도구 승인 게이트, 비용/재시도 상한 |
| 전체 | Trace 기록, Escalation 경로 |

### 9.3 명시적 실패 상태

다음 상태를 정상 출력으로 취급한다. 억지로 답을 만들지 않는다.

```text
INSUFFICIENT_EVIDENCE   근거 부족으로 판단 불가
INSUFFICIENT_CONTEXT    검색 결과 부족
CONFLICTING_EVIDENCE    근거 충돌 — 사람 판단 필요
EXTERNAL_FACTOR_ONLY    통제 가능한 원인 없음 — 관측 유지 권고
INCONCLUSIVE            실험 결과 판정 불가 (표본/기간 부족)
ESCALATED               자동 처리 상한 도달 — 사람에게 이관
```

### 9.4 Human-in-the-loop 게이트

| 상황 | 처리 |
|---|---|
| 되돌릴 수 없는 Action | 항상 승인 필요 |
| 비용 발생 Action (광고비, 가격 변경) | 항상 승인 필요 |
| Confidence LOW | 승인 필요 + 근거 부족 명시 |
| 근거 충돌 | 승인 필요 + 충돌 내용 제시 |
| 조회 / 분석 | 자동 허용 |

승인/거절은 **사유와 함께** 기록되어 Preference 데이터가 된다 (§4.2).

---

## 10. Long-term Learning Strategy

### 10.1 학습 루프

```text
운영(Production)
  → Trace / Decision Record 축적
  → 실패·거절·불일치 사례 선별
  → 평가 Dataset 편입
  → 개선 (프롬프트 → 검색 → 규칙 → Routing → 모델 순)
  → Regression Test
  → 배포
  → 재관측
```

### 10.2 개선 수단의 우선순위 (비용 오름차순)

```text
1. 프롬프트 개선          (비용 최저)
2. 검색 / Chunking 개선
3. 규칙(Rules) 보강
4. 데이터 품질 개선
5. Routing 정책 조정
6. 더 큰 모델 사용        (운영비 증가)
7. Specialized classifier
8. Preference optimization
9. Fine-tuning            (비용 최고)
```

**규칙:** 상위 단계로 해결되지 않는다는 증거 없이 하위(비싼) 수단으로 내려가지 않는다.

### 10.3 Fine-tuning 도입 조건

다음이 **모두** 충족될 때만 검토한다.

- [ ] 고품질 6-튜플 데이터가 충분히 축적됨
- [ ] 프롬프트/RAG/규칙으로 해결되지 않는 **반복되는** 실패 패턴이 식별됨
- [ ] 평가 Dataset으로 개선 여부를 측정할 수 있음
- [ ] 학습·운영 비용이 개인 셀러 제약 내에 있음
- [ ] 회귀 위험(기존 능력 손상)을 검증할 방법이 있음

### 10.4 데이터 자산 관리

- Decision Record는 **버전과 함께** 보존한다 (당시 모델/프롬프트/규칙 버전 포함).
- 개인정보는 저장 시점에 제거·마스킹한다.
- 평가 Dataset과 학습 Dataset은 **분리**한다 (누출 방지).

---

## 11. Differentiation

### 11.1 이 프로젝트가 아닌 것

* 일반 Chatbot
* PDF RAG 데모
* 단순 Tool Calling Agent
* 멀티에이전트 데모
* 자동 상품 생성기

### 11.2 차별화 포인트

| # | 포인트 | 문서 내 구현 위치 |
|---|---|---|
| 1 | 실제 이커머스 운영 도메인 기반 | 전 Phase |
| 2 | 개인 셀러의 비용 제약 반영 | §8, P2 |
| 3 | Local-first architecture | P2, Phase 0 / 9 |
| 4 | Evidence-grounded decision making | P4, Phase 1 / 4 |
| 5 | 외부 요인과 통제 가능 요인 분리 | P5, Phase 4 |
| 6 | 데이터 분석 + LLM 결합 (역할 분리) | P3, Phase 3 |
| 7 | 실험 기반 개선 | Phase 5 |
| 8 | Decision / Action / Outcome 기록 | §4.2, Phase 4~5 |
| 9 | Agent reliability | §9, Phase 7 |
| 10 | Evaluation-first development | P8, Phase 2 / 8 |
| 11 | Observability | Phase 8 |
| 12 | Human-in-the-loop | P7, §9.4 |
| 13 | 장기적인 학습 데이터 축적 | §10, Phase 11 |
| 14 | Local / Cloud adaptive routing | Phase 9 |

### 11.3 가장 핵심적인 차이

대부분의 LLM 데모는 **"답을 잘 만드는 것"**을 목표로 한다.
이 프로젝트는 **"근거 있는 답만 내고, 근거가 없으면 없다고 말하며, 그 판단의 결과를 끝까지 추적하는 것"**을 목표로 한다.

---

## 12. Current Phase

### 12.1 현재 위치

```text
[ Phase 0 ] ← 현재 (4일 프로젝트)
  Phase 1 ~ 11  : 장기 계획 (미착수)
```

현재 진행 중인 4일 프로젝트는 위 전체 시스템을 한 번에 구현하지 않는다. **Phase 0 — Foundation Model Evaluation** 에만 해당한다.

### 12.2 Phase 0 범위 (이번 4일 프로젝트)

| 구분 | 내용 |
|---|---|
| 목적 | 이후 Phase의 기반이 될 Local LLM 선정 |
| 대상 | Ollama 기반 Local LLM 2개 + Cloud API LLM 1개 (소규모 비교) |
| 입력 | 동일한 이커머스 평가 질문 세트 |
| 평가축 | 한국어 성능 / Instruction Following / Groundedness / Hallucination / 응답 속도 / 실행 자원 / 비용 |
| 산출물 | 평가 질문 세트, 응답 기록, 비교표, 선정 근거 |

### 12.3 Phase 0에서 남겨야 할 것

Phase 0의 진짜 산출물은 "어떤 모델이 좋았다"가 아니라 **이후 Phase에서 재사용 가능한 자산**이다.

- [ ] 재사용 가능한 **평가 질문 세트** (Phase 1~2 평가 Dataset의 시드)
- [ ] 모델별 응답 원본 기록 (향후 비교 기준선)
- [ ] 실행 자원 실측치 (RAM/VRAM/토큰 속도 — Phase 9 Routing 판단 근거)
- [ ] 선정 근거 문서 (왜 그 모델인가)

### 12.4 Repository 연속성

현재 프로젝트 종료 후에도 **동일 repository를 유지**하며 Phase를 점진적으로 추가한다.

예상 디렉터리 진화 (참고용, 확정 아님):

```text
docs/                 # 로드맵, 설계 결정, Phase별 기록
  roadmap.md          # 이 문서
eval/                 # Phase 0~2: 평가 질문 세트, 결과, 하네스
knowledge/            # Phase 1: 문서·인덱스
data/                 # Phase 3: 원본/파생 데이터 (원본 불변)
analytics/            # Phase 3: KPI·탐지 코드
decision/             # Phase 4: 진단·의사결정
experiments/          # Phase 5: 실험 정의·결과
tools/                # Phase 6: Tool 정의
agent/                # Phase 7: Plan / Retry / Escalate
observability/        # Phase 8: Trace
routing/              # Phase 9: Routing 정책
```

> 위 구조는 **각 Phase 착수 시점에** 실제 필요에 따라 생성한다. 미리 만들지 않는다.

---

## 13. Out of Scope for Phase 0

### 13.1 Phase 0에서 하지 않는 것

| 항목 | 해당 Phase |
|---|---|
| RAG 구현 / Vector DB 도입 | Phase 1 |
| 자동화된 평가 하네스 | Phase 2 |
| 판매·광고 데이터 적재 및 KPI 계산 | Phase 3 |
| 문제 진단 / 가설 생성 / 통제가능성 분류 | Phase 4 |
| 실험 설계 및 결과 추적 | Phase 5 |
| Tool Calling / Stateful Workflow | Phase 6 |
| Retry / Replan / Escalation | Phase 7 |
| Tracing / Agent 평가 | Phase 8 |
| Model Routing 구현 | Phase 9 |
| 이미지 · 멀티모달 분석 | Phase 10 |
| Fine-tuning / Preference optimization | Phase 11 (조건부) |
| 웹 UI / 대시보드 | 미정 |
| 실제 상용 데이터 수집 · 플랫폼 연동 | Phase 3 이후 |
| 유료 인프라 구축 | 도입 안 함 (§8 C4) |

### 13.2 Phase 0의 경계 판단 기준

작업을 시작하기 전에 다음을 자문한다.

> "이 작업이 **기반 모델 선정 근거**를 강화하는가?"

- **예** → Phase 0 범위
- **아니오** → 이 문서의 해당 Phase 항목에 메모만 남기고 **지금은 하지 않는다**

### 13.3 범위 이탈 위험 신호

다음이 나타나면 Phase 0 범위를 벗어나고 있는 것이다.

- Vector DB, Agent 프레임워크를 설치하고 있다
- 4일 안에 끝나지 않을 데이터 파이프라인을 설계하고 있다
- 평가보다 "동작하는 데모"를 만드는 데 시간을 쓰고 있다
- 모델 선정과 무관한 UI를 만들고 있다

---

## Appendix A. 용어 정의

| 용어 | 정의 |
|---|---|
| Evidence | 주장을 뒷받침하는, 원본 레코드까지 추적 가능한 근거 |
| Groundedness | 생성된 답변이 제공된 근거에 실제로 기반하는 정도 |
| Controllability | 셀러가 해당 요인을 직접 변경할 수 있는 정도 |
| Decision Record | Situation~Feedback 6-튜플을 담은 의사결정 기록 |
| Trajectory | Agent의 요청부터 최종 응답까지의 실행 궤적 |
| Escalate | 자동 처리를 중단하고 사람에게 판단을 넘기는 정상 경로 |
| Time-to-signal | Action 이후 결과 신호를 확인하기까지 필요한 기간 |
| Confounder | 실험 결과 해석을 왜곡할 수 있는 외부 교란 변수 |

## Appendix B. 설계 결정 기록 (ADR) 운영 방침

Phase 진행 중 되돌리기 어려운 선택(저장소, 임베딩 모델, 프레임워크, Routing 정책 등)은
`docs/decisions/NNNN-<title>.md` 형태로 짧게 기록한다.

기록 항목: **Context / Decision / Alternatives / Cost impact / Reversibility / Status**

## Appendix C. 문서 갱신 규칙

- Phase 착수·종료 시 §12(Current Phase)와 §6.12 Phase 요약표의 상태를 갱신한다.
- 설계 원칙(§3)을 위반하는 구현이 필요해지면, 구현을 먼저 하지 말고 **이 문서를 먼저 수정**한다.
- Exit Criteria는 Phase 착수 시점에 구체화할 수 있으나, 축소할 때는 사유를 남긴다.

# Step 03

<일반적인 이커머스 고객 문의와 셀러 업무 질문에 적절하게 답변할 수 있는 로컬 LLM을 비교·평가하여 가장 적합한 모델을 선정한다.>

1. 후보 모델 탐색
--- 서로 다른 로컬 모델들을 선정한다. (동일 모델의 양자화 버전은 사용하지 않는다.) ---


2. 확인할 정보

- model name
- license
- context length
- architecture
- language
- benchmark
- model card
- quantization 지원 여부
(Model Card의 최대 Context Length와 실험에서 실제 설정/확인한 Context Length는 따로 기록합니다. 다운로드 파일 크기, 시스템 RAM, VRAM 사용량도 구분한다.)



3. 선정 이유

>: 6개 모델의 특화가 전부 다르기 때문에, 실제 성능 비교에 적합할 것 같다.

# 6개 도메인 특화 모델

## (1) 법률 — Korean Law 8B

Model Card:
https://huggingface.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF

Repository declared license:
Apache-2.0

Base model license:
Llama 3.1 Community License

Ollama Pull:
ollama pull hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M

특징:
- 한국어 법률 특화를 표방하는 Llama 3.1 8B 기반 모델
- 법률 관련 질의응답 및 문서 이해 비교용
- 법률 학습 데이터와 벤치마크 상세 정보는 비교적 부족함

---

## (2) 의료·바이오 — KoBioMed Llama 3.1 8B Instruct

Model Card:
https://huggingface.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF

Original Model Card:
https://huggingface.co/Lowenzahn/KoBioMed-Llama-3.1-8B-Instruct

Repository declared license:
Llama 3.1 Community License

Base model license:
Llama 3.1 Community License

Ollama Pull:
ollama pull hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M

특징:
- 한국어·영어 Biomedical / Medical 특화
- 의학·생명과학 질의응답
- 의학 용어 및 Biomedical 지식 이해
- 의료·바이오 문서 이해 및 요약 비교용

---

## (3) 금융 — BCCard Korean Finance 8B

Model Card:
https://huggingface.co/BCCard/Llama-3.1-Kor-BCCard-Finance-8B

GGUF:
https://huggingface.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF

Repository declared license:
Meta Llama 3 Community License Agreement

Base model license:
Llama 3.1 Community License

Ollama Pull:
ollama pull hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M

특징:
- 한국어 금융 Q&A 특화
- BC Card 금융 데이터 기반 Fine-tuning
- 금융 용어, 카드, 결제, 금융 상품 관련 질의 비교용
- 한국어 금융 도메인 Fine-tuning 효과 확인에 적합

---

## (4) 코딩 — Qwen2.5 Coder 7B Instruct

Model Card:
https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct

GGUF:
https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

Repository declared license:
Apache-2.0

Base model license:
Apache-2.0

Ollama Pull:
ollama pull hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M

특징:
- 코드 생성 특화
- 코드 수정 및 디버깅
- 코드 설명
- 알고리즘 및 프로그래밍 문제 해결
- 한국어 프롬프트 사용 가능

---

## (5) 수학 — Math-IIO 7B Instruct

Model Card:
https://huggingface.co/prithivMLmods/Math-IIO-7B-Instruct

GGUF:
https://huggingface.co/QuantFactory/Math-IIO-7B-Instruct-GGUF

Repository declared license:
CreativeML Open RAIL-M

Base model license:
Apache-2.0

Base Model:
Qwen/Qwen2.5-7B-Instruct

Ollama Pull:
ollama pull hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M

특징:
- 수학 문제 해결 특화
- Equation 및 논리 문제
- 단계적 수학 추론
- Qwen2.5 7B 기반
- 한국어를 포함한 다국어 입력 비교 가능

---

## (6) 이커머스 — SAM-1 Base 7B

Model Card:
https://huggingface.co/snapcart-ai/sam-1-base

GGUF:
https://huggingface.co/mradermacher/sam-1-base-GGUF

Repository declared license:
Apache-2.0

Base model license:
Apache-2.0

Parent Model:
Qwen/Qwen2.5-7B-Instruct

Ollama Pull:
ollama pull hf.co/mradermacher/sam-1-base-GGUF:Q4_K_M


특징:
- 한국어 기반 LLM
- Plateer AI-Lab의 POLAR 계열
- 커머스 / 이커머스 활용을 목적으로 개발된 모델 계열
- 상품 검색, 추천, 비교, 리뷰 요약 등 커머스 작업 비교에 적합

주의:
- 다른 후보는 7B~8B이지만 POLAR는 14B
- Q4_K_M 파일도 약 8GB 수준
- 현재 8GB VRAM 환경에서는 CPU/RAM Offloading이 발생할 수 있음
- 다른 모델보다 응답 속도가 느릴 수 있음


# 최종 도메인 구성

1. 법률
   - Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF
   - 8B / Q4_K_M

2. 의료·바이오
   - KoBioMed-Llama-3.1-8B-Instruct
   - 8B / Q4_K_M

3. 금융
   - BCCard/Llama-3.1-Kor-BCCard-Finance-8B
   - 8B / Q4_K_M

4. 코딩
   - Qwen/Qwen2.5-Coder-7B-Instruct
   - 7B / Q4_K_M

5. 수학
   - Math-IIO-7B-Instruct
   - 7B / Q4_K_M

6. 이커머스
   - x2bee/POLAR-14B-v0.5
   - 14B / Q4_K_M



일단 1, 4, 6 모델 다운로드 진행.

---

## 산출물 정리

> 연결 산출물: [deliverables.md](../deliverables.md)
> - `2. Model Comparison Table` ← **이 스텝이 원본**
> - 요구사항 충족도 평가표 **#2. 후보 모델 조사 (STEP 3)**

### Model Comparison Table 작성용 원본 표

> 필수 요구사항은 **서로 다른 로컬 후보 2개**. 아래는 다운로드 예정인 3개 기준.
> 빈 칸은 STEP 4~6에서 실측 후 채운다.

**기본 정보** (Model Card 확인 완료분)

| 라벨 | 도메인 | Model Name | Parameter | Quantization | License (저장소 선언) | License (Base model) |
|---|---|---|---|---|---|---|
| A | 법률 | Llama-3.1-Korean-8B-Instruct-Law | 8B | Q4_K_M | Apache-2.0 | Llama 3.1 Community |
| B | 의료·바이오 | KoBioMed-Llama-3.1-8B-Instruct | 8B | Q4_K_M | Llama 3.1 Community | Llama 3.1 Community |
| C | 금융 | Llama-3.1-Kor-BCCard-Finance-8B | 8B | Q4_K_M | Meta Llama 3 Community | Llama 3.1 Community |
| D | 코딩 | Qwen2.5-Coder-7B-Instruct | 7B | Q4_K_M | Apache-2.0 | Apache-2.0 |
| E | 수학 | Math-IIO-7B-Instruct | 7B | Q4_K_M | CreativeML Open RAIL-M | Apache-2.0 |
| F | 이커머스 | POLAR-14B-v0.5 | 14B | Q4_K_M | Apache-2.0 | Apache-2.0 |

**모델 태그** (`ollama pull` 대상)

| 라벨 | 태그 |
|---|---|
| A | `hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M` |
| B | `hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M` |
| C | `hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M` |
| D | `hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` |
| E | `hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M` |
| F | `hf.co/RichardErkhov/x2bee_-_POLAR-14B-v0.5-gguf:Q4_K_M` |

**Context / 자원** (STEP 4~6에서 실측 후 기입)

| 라벨 | 문서상 최대 Context | 실험에 사용한 Context | 다운로드 파일 크기 | VRAM 사용량 | 시스템 RAM 사용량 |
|---|---|---|---|---|---|
| A | | | | | |
| B | | | | | |
| C | | | | | |
| D | | | | | |
| E | | | | | |
| F | | 약 8GB | | | |

> 라벨 A~F는 [eval-results.md](../eval-results.md)의 Model A~F와 동일하다.
> `문서상 최대 Context`와 `실험에 사용한 Context`는 반드시 구분해서 기재한다 (산출물 요구사항).

**STEP 4 CLI 스모크 테스트 결과 — 후보 확정**

| 라벨 | CLI 실행 결과 | 처리 |
|---|---|---|
| A (법률) | FAIL — 특수토큰 노출, 프롬프트 반복 | 본 실험으로 판정 |
| B (의료·바이오) | PASS | 본 실험 진행 |
| C (금융) | PASS | 본 실험 진행 |
| D (코딩) | PASS | 본 실험 진행 |
| E (수학) | PASS | 본 실험 진행 |
| F (이커머스) | FAIL — server_error (peg-native format) | 본 실험으로 판정 |

> A·F는 사전 확인에서 문제가 보였으나 제외하지 않고 본 실험을 돌린다. 재현되면 필수 조건 3 미충족으로 판정한다.
> 상세 로그는 [eval-results.md](../eval-results.md) 'STEP 4 CLI 스모크 테스트에서 관찰된 문제' 절 참조.

### 미확정 — 채워야 할 것

- [ ] 후보별 **문서상 최대 Context Length** (Model Card 확인)
- [ ] **실험에서 실제 설정한 Context Length** (STEP 6 실행 설정) — 위 항목과 반드시 구분 기재
- [ ] 다운로드 파일 크기 / VRAM / 시스템 RAM **각각 구분해서** 실측 (STEP 4, 6)
- [x] 최종 비교 대상 후보 확정 → **6개 전부** (6모델 × 10문제 × 2회 = 본 실험 120회). A·F는 CLI 사전 확인에서 문제가 보였으나 본 실험 결과로 판정한다
- [ ] 각 후보의 architecture / language / benchmark 정보 (본문 `2. 확인할 정보` 목록 중 미기재분)

### 제출 시 확인

- [ ] License는 **저장소 선언**과 **Base model** 둘 다 기재 (Llama 계열은 상업적 활용 조건 별도 확인)
- [ ] **Model E의 CreativeML Open RAIL-M** 은 사용 목적 제한 조항이 있는 라이선스다. STEP 2 필수 조건 4(상업적 활용 가능)를 판정하려면 원문 확인 필요
- [ ] 모델 가중치 파일은 저장소에 올리지 않고 **정확한 태그 + `ollama pull` 명령만** 안내
- [ ] 후보 선정 이유가 기록되어 있음 (평가표 #2 증빙)

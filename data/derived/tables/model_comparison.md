<!-- 자동 생성됨: python -m evalkit.exporter
     직접 수정하지 말 것. 원본: data/raw/, docs/eval-results.md -->

# Model Comparison Table (생성물)

| 항목 | Model C (금융) | Model D (코딩) | Model F (이커머스) |
|---|---|---|---|
| Model Name | BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF | Qwen2.5-Coder-7B-Instruct-GGUF | sam-1-base-GGUF |
| Parameter | 8.03B | 7.62B | 7.62B |
| License (선언) | Meta Llama 3 Community | Apache-2.0 | Apache-2.0 |
| License (Base) | Llama 3.1 Community | Apache-2.0 | Apache-2.0 |
| Architecture | LlamaForCausalLM (Llama 3.1 8B 계열) | Qwen2ForCausalLM (Qwen2.5 계열) | Qwen2ForCausalLM (base: Qwen2.5-7B-Instruct, LoRA 병합) |
| Language (문서상) | Korean — 모델 카드가 'Korean financial knowledge model based on Meta-Llama-3.1 8B' 로 명시 | 모델 카드에 지원 언어 목록 미명시 (저장소 태그는 English). Qwen2.5 계열은 다국어를 지원하며 이번 실험에서 한국어 프롬프트로 정상 응답 | 모델 카드는 English only 명시 ('English only. The model has been fine-tuned and evaluated exclusively on English-language tasks.', language 메타데이터도 en 단독). 한국어는 공식 지원 범위가 아니며 base Qwen2.5-7B-Instruct 의 다국어 능력을 상속한 것으로 보인다 — 실측은 한국어 표현 4.15 로 세 후보 중 최고 |
| Benchmark (문서상) | 공개 벤치마크 없음 — 모델 카드에 사용 예시와 Q&A 샘플만 있고 평가 수치 미제시 | 모델 카드에 수치 미기재 — 공식 블로그(qwenlm.github.io/blog/qwen2.5-coder-family) 참조 안내만 있음 | SAM-Bench 90.55/100 (719 태스크). Query Understanding 98.37 / Attribute Extraction 97.57 / Product Comparison 94.88 / Purchase Decision 94.11 / Review Synthesis 92.45 / Price Analysis 89.39 / Product Recommendation 77.76 / Personalization 77.59. 모델 카드 기준이며 이번 실험에서 재현한 값이 아니다 |
| 문서상 최대 Context | 131072 | 32768 | 32768 |
| 실험 Context | 4096 | 4096 | 4096 |
| Quantization | Q4_K_M | Q4_K_M | unknown |
| VRAM (관측 시점) | 5027.5 (n=20) | 4528.1 (n=20) | 4528.1 (n=20) |
| 다운로드 크기 | 4.58 GB | 4.36 GB | 4.36 GB |
| 주요 특징 | 한국어 금융 Q&A 특화<br>BC Card 금융 데이터 기반 Fine-tuning<br>금융 용어, 카드, 결제, 금융 상품 관련 질의 비교용<br>한국어 금융 도메인 Fine-tuning 효과 확인에 적합 | 코드 생성 특화<br>코드 수정 및 디버깅<br>코드 설명<br>알고리즘 및 프로그래밍 문제 해결<br>한국어 프롬프트 사용 가능 | 커머스 특화 LLM — 모델 카드는 English only 를 명시하며 한국어는 공식 지원 범위가 아니다<br>Qwen2.5-7B-Instruct 기반 (LoRA 병합) — 한국어 응답은 base 의 다국어 능력을 상속한 것으로 보인다<br>상품 검색, 추천, 비교, 리뷰 요약 등 커머스 작업 비교에 적합<br>SAM-Bench 90.55/100 (모델 카드 기준, 이번 실험에서 재현한 값 아님) |
| Model Card (GGUF) | https://huggingface.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF | https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF | https://huggingface.co/mradermacher/sam-1-base-GGUF |
| Model Card (원본) | https://huggingface.co/BCCard/Llama-3.1-Kor-BCCard-Finance-8B | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | https://huggingface.co/snapcart-ai/sam-1-base |
| 모델 태그 | `hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M` | `hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` | `hf.co/mradermacher/sam-1-base-GGUF:Q4_K_M` |
| digest | `3dc693e518d8` | `f218460127af` | `90130fbbb57b` |

> 비교 대상: Model C (금융), Model D (코딩), Model F (이커머스). 최종 선정은 이 중에서 한다.
> `문서상 최대 Context` 는 Model Card 값(문서 기반), `실험 Context` 는 실행 기록의 context_length(실측)다.
> VRAM 은 응답 직후 관측값의 평균이며 최대 VRAM 이 아니다.
> `주요 특징` 은 Model Card 기반 설명이며 측정 결과가 아니다.
> 출처: `data/env/environment.json`, `data/raw/local/runs.jsonl`, `data/config/models.json`

### 부가 테스트 (참고)

| 라벨 | Model Name | Parameter | License (선언) | 모델 태그 |
|---|---|---|---|---|
| A | Llama-3.1-Korean-8B-Instruct-Law-GGUF | 8.03B | Apache-2.0 | `hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M` |
| B | KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF | 8.03B | Llama 3.1 Community | `hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M` |
| E | Math-IIO-7B-Instruct-GGUF | 7.62B | CreativeML Open RAIL-M | `hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M` |

> 채점·선정 대상이 아니다. 제외 근거로 남긴다.

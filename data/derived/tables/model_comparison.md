<!-- 자동 생성됨: python -m evalkit.exporter
     직접 수정하지 말 것. 원본: data/raw/, data/scoring/ -->

# Model Comparison Table (생성물)

| 구분 | 라벨 | 모델 태그 | digest | 양자화 | 다운로드 크기 | 문서상 최대 Context | 실험 Context | License(선언) | License(Base) |
|---|---|---|---|---|---|---|---|---|---|
| 비교 대상 | C | `hf.co/featherless-ai-quants/BCCard-Llama-3.1-Kor-BCCard-Finance-8B-GGUF:Q4_K_M` | 3dc693e518d8 | Q4_K_M | 4.58 GB |  | 4096 | Meta Llama 3 Community | Llama 3.1 Community |
| 비교 대상 | D | `hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M` | f218460127af | Q4_K_M | 4.36 GB |  | 4096 | Apache-2.0 | Apache-2.0 |
| 비교 대상 | F | `hf.co/mradermacher/sam-1-base-GGUF:Q4_K_M` | 90130fbbb57b | unknown | 4.36 GB |  | 4096 | Apache-2.0 | Apache-2.0 |
| 부가 | A | `hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M` | 70c771a2fa93 | Q4_K_M | 4.58 GB |  | 4096 | Apache-2.0 | Llama 3.1 Community |
| 부가 | B | `hf.co/mradermacher/KoBioMed-Llama-3.1-8B-Instruct-i1-GGUF:Q4_K_M` | c58b1f5d134e | unknown | 4.58 GB |  | 4096 | Llama 3.1 Community | Llama 3.1 Community |
| 부가 | E | `hf.co/QuantFactory/Math-IIO-7B-Instruct-GGUF:Q4_K_M` | d88001f453f0 | Q4_K_M | 4.36 GB |  | 4096 | CreativeML Open RAIL-M | Apache-2.0 |

> 비교 대상: Model C (금융), Model D (코딩), Model F (이커머스). 최종 선정은 이 중에서 한다.
> `문서상 최대 Context` 는 Model Card 값, `실험 Context` 는 실행 기록의 context_length 다.
> 출처: `data/env/environment.json`, `data/raw/local/runs.jsonl`

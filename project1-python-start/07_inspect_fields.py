"""응답에 어떤 필드가 들어 있는지 확인합니다.

STEP 6에서 기록해야 하는 값들(로딩 시간 / 출력 토큰 수 / 생성 속도 / VRAM)이
이 환경의 Ollama 응답에서 실제로 어떤 이름으로 오는지 먼저 확인하는 용도입니다.
확인한 필드명에 맞춰 evalkit 의 측정 코드를 맞춥니다.

MODEL 한 줄만 바꿔 모델별로 실행합니다.
"""

import json
import sys
from time import perf_counter

from ollama import Client

# 확인할 모델을 여기서 바꿉니다.
MODEL = "hf.co/Arc1el/Llama-3.1-Korean-8B-Instruct-Law-GGUF:Q4_K_M"
QUESTION = "온라인 쇼핑몰 고객 문의에 답변할 때 중요한 점 3가지를 간단히 설명해 주세요."

# Windows 콘솔(cp949)에서 한국어 출력이 깨지지 않게 합니다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def dump(obj):
    """pydantic 모델이든 dict든 보기 좋게 출력합니다."""
    data = obj.model_dump() if hasattr(obj, "model_dump") else obj
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


client = Client(host="http://127.0.0.1:11434", timeout=180)

print(f"모델: {MODEL}")
print("질문을 보냈습니다. 답변을 기다려 주세요.\n")

start = perf_counter()
response = client.chat(
    model=MODEL,
    messages=[{"role": "user", "content": QUESTION}],
    stream=False,
    options={"temperature": 0, "num_predict": 128},
)
elapsed = perf_counter() - start

# 응답을 받은 직후, 모델이 아직 메모리에 있을 때 조회해야 VRAM을 읽을 수 있습니다.
ps = client.ps()

print("=" * 60)
print("[1] 답변")
print("=" * 60)
print(response.message.content)

print()
print("=" * 60)
print("[2] 측정에 쓸 필드")
print("=" * 60)
print(f"elapsed (직접 측정)   : {elapsed:.3f} 초")
for name in ("load_duration", "eval_count", "eval_duration",
             "prompt_eval_count", "prompt_eval_duration",
             "total_duration", "done_reason"):
    value = getattr(response, name, "<없음>")
    print(f"{name:<22}: {value}")

print()
print("나노초로 보이면 1e9로 나눠 초로 기록합니다.")
print(f"  load_duration -> {getattr(response, 'load_duration', 0) / 1e9:.3f} 초")
ec = getattr(response, "eval_count", None)
ed = getattr(response, "eval_duration", None)
if ec and ed and ed > 0:
    print(f"  tokens/s      -> {ec / (ed / 1e9):.2f}")
else:
    print("  tokens/s      -> 계산 불가 (eval_count 또는 eval_duration 없음/0)")


# size 와 size_vram 비율이 ollama ps 의 PROCESSOR 열이 된다.
for entry in ps.models:
    if entry.model == MODEL:
        size, vram = entry.size, entry.size_vram
        if vram == 0:
            proc = "100% CPU"
        elif vram == size:
            proc = "100% GPU"
        else:
            cpu = round((size - vram) / size * 100)
            proc = f"{cpu}%/{100 - cpu}% CPU/GPU"
        print(f"  processor     -> {proc}  (size={size}, size_vram={vram})")
        break

print()
print("=" * 60)
print("[3] client.ps() — VRAM / digest / 양자화 / context")
print("=" * 60)
print(dump(ps))

print()
print("=" * 60)
print("[4] 응답 전체 구조")
print("=" * 60)
print(dump(response))

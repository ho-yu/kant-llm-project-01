"""STEP 04 — 모델 하나에 질문 한 개를 보내 연결을 확인한다.

    uv run python 01_ollama_chat.py           아래 MODEL_LABEL 의 모델
    uv run python 01_ollama_chat.py F         라벨로 지정
    uv run python 01_ollama_chat.py --list    등록된 모델 목록

모델 태그는 `data/config/models.json` 에서 읽는다. 태그를 이 파일에 복사해 두면
설정 파일과 어긋날 수 있어서다 — 고칠 곳은 언제나 models.json 한 곳이다.

본 실험(10문항 × 2회)은 `10_run.py` 가 한다. 이 파일은 연결과 응답을 눈으로
한 번 확인하는 용도이며, 여기서 나온 응답은 실험 기록에 저장되지 않는다.
"""

import argparse

from ollama import Client

from evalkit import config

# ---------------------------------------------------------------- 여기만 바꿉니다

MODEL_LABEL = "F"  # A~F. models.json 의 model_label
QUESTION = "온라인 쇼핑몰 고객 문의에 답변할 때 중요한 점 3가지를 간단히 설명해 주세요."

# ----------------------------------------------------------------


def models() -> dict[str, dict]:
    return {m["model_label"]: m for m in config.enabled_models()}


parser = argparse.ArgumentParser(description="STEP 04 연결 확인")
parser.add_argument("label", nargs="?", default=MODEL_LABEL, help="모델 라벨 (A~F)")
parser.add_argument("--list", action="store_true", help="등록된 모델을 보여주고 끝낸다")
args = parser.parse_args()

catalog = models()

if args.list:
    for label, m in sorted(catalog.items()):
        print(f"{label}  {m.get('tier', ''):14s}  {m['model_tag']}")
    raise SystemExit(0)

label = args.label.upper()
if label not in catalog:
    raise SystemExit(f"라벨 {label} 을 models.json 에서 찾지 못했습니다. --list 로 확인하세요.")

model = catalog[label]
tag = model["model_tag"]

print(model.get("display_name") or f"Model {label}")
print(f"  {tag}")
print("Ollama에 질문을 보냈습니다. 답변을 기다려 주세요.")

# 내 PC에서 실행 중인 Ollama에 연결합니다.
client = Client(host="http://127.0.0.1:11434", timeout=180)
response = client.chat(
    model=tag,
    messages=[{"role": "user", "content": QUESTION}],
    stream=False,
    options={"temperature": 0, "num_predict": 256},
)

print("\n[Ollama 답변]")
print(response.message.content)

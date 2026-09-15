from ollama import Client

MODEL = "hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M"
QUESTION = "온라인 쇼핑몰 고객 문의에 답변할 때 중요한 점 3가지를 간단히 설명해 주세요."

# 내 PC에서 실행 중인 Ollama에 연결합니다.
client = Client(host="http://127.0.0.1:11434", timeout=180)
print("Ollama에 질문을 보냈습니다. 답변을 기다려 주세요.")
response = client.chat(
    model=MODEL,
    messages=[{"role": "user", "content": QUESTION}],
    stream=False,
    options={"temperature": 0, "num_predict": 256},
)

print("\n[Ollama 답변]")
print(response.message.content)
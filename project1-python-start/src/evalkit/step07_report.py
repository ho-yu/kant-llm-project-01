"""공통 5문항의 원본 실행 기록과 기존 채점표로 STEP 07을 생성한다.

    python -m evalkit.step07_report

원본 runs.jsonl, questions.json, 채점 입력면은 읽기만 한다.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean

from . import config, recorder, scoring
from .report import _inject


LABELS = ("C", "D", "F", "CLOUD")
NAMES = {"C": "Model C (금융)", "D": "Model D (코딩)",
         "F": "Model F (이커머스)", "CLOUD": "Cloud"}


def _avg(rows: list[dict], field: str) -> str:
    values = [r[field] for r in rows if r.get("status") == "success" and r.get(field) is not None]
    return f"{mean(values):.2f} (n={len(values)})" if values else "측정값 없음 (n=0)"


def _cloud_temp(cloud_opts: dict, local_opts: dict) -> str:
    """Cloud 요청의 temperature 를 기록에서 읽어 동일 여부까지 판정한다.

    실행 조건이 바뀌면 이 표도 따라가야 한다 — 문구를 고정해 두면
    기록과 어긋난 채 남는다.
    """
    if "temperature" not in cloud_opts:
        return "요청에 미지정; 실제 적용값 미확인 | 차이"
    ct, lt = cloud_opts["temperature"], local_opts.get("temperature")
    state = "동일" if ct == lt else "차이"
    return f"`{ct}` (요청에 전달됨) | {state}"


def build() -> str:
    qids = config.cloud_question_ids()
    if len(qids) != 5:
        raise ValueError(f"Cloud 공통 질문은 정확히 5개여야 함: {qids}")
    questions = config.question_map()
    scores = {s["run_id"]: s for s in scoring.parse()}
    local = [r for r in recorder.iter_records(config.LOCAL_RUNS_PATH)
             if r.get("phase") == "main" and r.get("question_id") in qids
             and r.get("model_label") in LABELS[:3]]
    cloud = [r for r in recorder.iter_records(config.CLOUD_RUNS_PATH)
             if r.get("phase") == "main" and r.get("question_id") in qids]
    by_model = {label: [r for r in (cloud if label == "CLOUD" else local)
                        if r.get("model_label") == label] for label in LABELS}
    for label, rows in by_model.items():
        expected = 1 if label == "CLOUD" else 2
        for qid in qids:
            found = [r for r in rows if r.get("question_id") == qid]
            if len(found) != expected or {r.get("repeat") for r in found} != set(range(1, expected + 1)):
                raise ValueError(f"{label}/{qid}: 기대 {expected}회, 실제 {len(found)}회")
            if any(r.get("prompt") != questions[qid]["prompt"] for r in found):
                raise ValueError(f"{label}/{qid}: 질문 원문 불일치")

    def score_values(rows: list[dict]) -> list[float]:
        return [scores[r["run_id"]]["average"] for r in rows
                if r.get("status") == "success" and r["run_id"] in scores
                and scores[r["run_id"]].get("average") is not None]

    settings = config.load_run_settings()
    options = settings["options"]
    cloud_cfg = config.load_models()["cloud_model"]
    env = config.load_environment()
    hw = env.get("hardware", {})
    cloud_opts = cloud[0].get("options") if cloud else {}
    lines = [
        "## STEP 07 — Local LLM vs Cloud API", "",
        "### 비교 범위", "",
        f"- Local: Model C 금융, Model D 코딩, Model F 이커머스. Cloud: `{cloud_cfg['model_id']}`.",
        f"- 공통 질문: {', '.join(qids)} (`questions.json`의 `cloud_compare=true`), 총 5개.",
        "- 질문당 Local 2회 모두 집계, Cloud 1회. 워밍업과 재시도는 제외.",
        "- 이 단계에서는 최종 Local 모델을 선정하지 않는다.", "",
        "### 비교 조건", "",
        "| 항목 | Local | Cloud | 상태 |", "|---|---|---|---|",
        "| 질문 | 동일한 원문 5개 | 동일한 원문 5개 | 동일 |",
        f"| Temperature | `{options.get('temperature')}` | {_cloud_temp(cloud_opts, options)} |",
        f"| Output limit | `num_predict={options.get('num_predict')}` | `max_output_tokens={cloud_opts.get('max_output_tokens')}` | 숫자는 같으나 토크나이저·한도 의미 차이 |",
        f"| Context | `num_ctx={options.get('num_ctx')}` | API에서 창 크기 미지정 | 차이 |",
        "| Tools | 사용 안 함 | `tools=[]`, `tool_choice=none` (실행 코드) | 도구 미사용 |",
        "| Reasoning | 별도 설정 없음 | `effort=none` (실행 코드) | 모델 계열 차이 |",
        f"| Generation settings | `seed={options.get('seed')}`, system prompt 없음 | seed 미지정, system prompt 없음 | 일부 차이 |",
        "| 반복 횟수 | 2회/문항 | 1회/문항 | 의도적 차이 |", "",
        "요청 설정은 로컬 원본의 `options`, Cloud 원본의 `options`, `run_cloud.py` 호출 코드에서 확인했다. "
        "Cloud의 tools·reasoning 요청값은 현재 JSONL에 독립 필드로 저장되지 않아 원본만으로 재검증할 수 없다. "
        "토크나이저, 로컬 단일 Windows/GPU 추론 환경, Cloud 서버·네트워크가 서로 다르다.", "",
        "### 공통 5문항", "",
        "| 질문 | Model C | Model D | Model F | Cloud |",
        "|---|---:|---:|---:|---:|",
    ]
    for qid in qids:
        cells = []
        for label in LABELS:
            vals = score_values([r for r in by_model[label] if r["question_id"] == qid])
            cells.append(f"{mean(vals):.2f} (n={len(vals)})" if vals else "미채점")
        lines.append(f"| {qid} | " + " | ".join(cells) + " |")

    lines += ["", "### Quality", "",
              "STEP 05의 A 답변 적합성, B 논리성/실용성, C 한국어 표현, 해당 문항의 D 지시사항 준수와 E 정보 부족·불확실성 대응을 그대로 사용했다. "
              "각 응답의 기존 기준 점수 평균을 구한 뒤 공통 5문항의 응답을 동일 가중 평균했다. 점수 근거는 로컬 `docs/eval-results.md`, Cloud `docs/cloud-compare.md`의 각 run_id 블록에 있다.", "",
              "| Model | 평균 (1~5) | Quality n (응답) | Success / Attempts |",
              "|---|---:|---:|---:|",
              ]
    for label, rows in by_model.items():
        vals = score_values(rows)
        average = f"{mean(vals):.2f}" if vals else "미채점"
        success = sum(r.get("status") == "success" for r in rows)
        lines.append(f"| {NAMES[label]} | {average} | {len(vals)} | {success} / {len(rows)} |")
    lines += ["", "Cloud Q10은 `api_status=incomplete`이고 출력 한도 768토큰에 도달했다. "
              "채점표의 기존 4.00점은 그 불완전한 응답에 대한 점수다. 정상 완료 4건만 따로 보면 평균이 달라지므로 임의로 제외하지 않았다.", "",
              "### Latency", "",
              "| Model | 평균 전체 응답 시간 (초) |", "|---|---:|"]
    for label, rows in by_model.items():
        lines.append(f"| {NAMES[label]} | {_avg(rows, 'elapsed_sec')} |")
    lines += ["", "현재 실험 환경에서 관측된 전체 응답 시간이다. Local은 로컬 호출, Cloud는 네트워크 왕복과 API 처리를 포함한다. "
              "따라서 이 수치만으로 모델 자체의 생성 속도를 판정할 수 없다.", "",
              "### Generation Performance", "",
              "| Model | Local tokens/s | 출력 토큰 평균 | 입력 토큰 평균 | 로딩 시간 평균 (초) | 종료 상태 |",
              "|---|---:|---:|---:|---:|---|",
              ]
    for label, rows in by_model.items():
        if label == "CLOUD":
            status = Counter(r.get("api_status") or "미기록" for r in rows)
            lines.append(f"| Cloud | 내부 생성 시간 없음 → 계산 불가 | {_avg(rows, 'output_tokens')} | {_avg(rows, 'input_tokens')} | 미제공 | "
                         + ", ".join(f"{k} {v}" for k, v in status.items()) + " |")
        else:
            status = Counter(r.get("done_reason") or "미기록" for r in rows)
            lines.append(f"| {NAMES[label]} | {_avg(rows, 'tokens_per_sec')} | {_avg(rows, 'eval_count')} | {_avg(rows, 'prompt_eval_count')} | {_avg(rows, 'load_duration_sec')} | "
                         + ", ".join(f"{k} {v}" for k, v in status.items()) + " |")
    lines += ["", "Local 생성속도와 Cloud의 네트워크 포함 elapsed는 동일 지표가 아니다. "
              "Cloud는 내부 생성 시간이 없어 tokens/s를 계산하지 않았다. 입력·출력 토큰은 서로 다른 토크나이저로 측정되어 수치만으로 답변 길이와 장황함을 판단할 수 없다.", "",
              "#### 종료 상태와 응답 길이", "",
              "| Model | 정상 종료 | 한도 도달/미완료 | 호출 실패 | 평균 응답 글자 수 |",
              "|---|---:|---:|---:|---:|",
              ]
    for label, rows in by_model.items():
        good = sum((r.get("api_status") == "completed" if label == "CLOUD" else r.get("done_reason") == "stop") for r in rows)
        limited = sum((r.get("api_status") == "incomplete" if label == "CLOUD" else r.get("done_reason") == "length") for r in rows)
        errors = sum(r.get("status") != "success" for r in rows)
        chars = [len(r.get("response_text") or "") for r in rows if r.get("status") == "success"]
        lines.append(f"| {NAMES[label]} | {good} | {limited} | {errors} | {mean(chars):.1f} (n={len(chars)}) |")
    lines += ["", "Cloud의 `incomplete` 1건은 API 응답이 돌아와 호출 성공 수에는 포함했지만 정상 종료로 세지 않았다. "
              "원본에 `incomplete_details.reason`이 저장되지 않아 원인을 확정할 수 없다. 출력 768토큰과 요청 한도 768토큰이 같다는 점은 한도 도달의 근거다.", "",
              "### Cost", "",
              f"Cloud 원본 API 사용량은 입력 {sum(r.get('input_tokens') or 0 for r in cloud)}토큰, 출력 {sum(r.get('output_tokens') or 0 for r in cloud)}토큰이다. "
              f"기록 당시 입력 ${cloud_cfg.get('price_input_per_1m_tokens')}/1M, 출력 ${cloud_cfg.get('price_output_per_1m_tokens')}/1M, 통화 {cloud_cfg.get('price_currency')}. "
              f"요청별 `estimated_cost` 합계는 {sum(r.get('estimated_cost') or 0 for r in cloud):.7f} {cloud_cfg.get('price_currency')} (5회), "
              f"평균 {mean(r['estimated_cost'] for r in cloud if r.get('estimated_cost') is not None):.7f} {cloud_cfg.get('price_currency')} (n={sum(r.get('estimated_cost') is not None for r in cloud)})다.",
              f"가격 출처: [{cloud_cfg.get('price_source_url')}]({cloud_cfg.get('price_source_url')}) (설정 파일 확인일 {cloud_cfg.get('price_checked_at')}, Standard 단가). "
              "추정 비용은 원본에 저장된 토큰 사용량 × 단가이며 실제 청구액은 기록되지 않았다. 실제 API 청구·사용량은 계정의 사용량 페이지에서 별도 확인이 필요하다.",
              "Local은 API 토큰 과금이 없다. GPU/PC 구입·유지, 전력, 모델 저장 공간, 관리와 운영 비용은 측정하지 않았으므로 금액으로 환산하지 않았다.", "",
              "### Security", "",
              "- STEP 1 요구사항: **데이터 보안 중요** — 고객 문의에 주문번호·연락처·배송지 같은 개인정보가 섞여 들어올 수 있다.",
              "- Local: 문의가 내부에 머문다. 모델과 데이터를 직접 통제하고 내부망 서빙으로 외부 전송을 없앨 수 있다. 접근 제어·패치·로그·로컬 보안은 운영자 책임이다.",
              "- Cloud: **문의 원문이 외부 API로 전송된다.** 개인정보가 포함될 수 있으므로 비식별화·최소화, 제공자의 데이터 처리·보관 정책 검토, 서비스 의존 관리가 선행돼야 한다.",
              "- 이 제약은 로컬 후보 간 판정에는 영향이 없다(C·D·F 의 데이터 통제 수준이 같다). **로컬을 우선하고 Cloud 사용 범위를 제한하는 근거**로 STEP 8 운영 권고에 반영한다.", "",
              "### Infrastructure / Operations", "",
              f"- Local: 이 실험은 Windows, {hw.get('gpu_name')}, RAM {hw.get('system_ram_gb')} GB, Ollama 환경에서 수행했다. "
              "GPU/PC·모델 다운로드·저장 공간·모델 관리·업데이트·장애 대응·서빙을 운영자가 맡는다.",
              "- Cloud: API 사용에는 자체 GPU가 필요하지 않고 서버 운영 부담이 낮다. 인터넷 연결, API 장애·변경, 사용량·예산 관리는 필요하다.", "",
              "### Customization", "",
              "- Local: 모델 선택, 양자화, 자체 서빙과 내부망 배치가 가능하다. 이번 실험은 Q4_K_M 모델을 Ollama로 실행했으며 Fine-tuning은 수행하지 않았다.",
              "- Cloud: 제공 모델과 API 기능 범위에 의존하고 설정 및 서버 내부 제어에 제한이 있다. 이번 실험은 별도 Fine-tuning을 수행하지 않았다.", "",
              "### Main Trade-offs", "",
              "- Quality: 공통 질문의 기존 채점에서 Cloud가 높았으나 Q10 미완료와 반복 수 차이를 함께 본다.",
              "- Latency: 이번 환경에서는 Local 전체 응답 시간이 짧았다. Cloud 수치에 네트워크가 포함되어 모델 자체 속도 비교는 불가하다.",
              "- Cost: Cloud의 기록 기반 추정 API 비용은 계산 가능하다. Local 총소유비용은 미측정이다.",
              "- Security: Local은 문의가 내부에 머물고 자체 보안 책임이 따른다. Cloud는 문의 원문의 외부 전송이 전제되어, 개인정보가 섞일 수 있는 고객 문의에는 그대로 쓰기 어렵다.",
              "- Operations: Local은 장비·모델·서빙을 관리한다. Cloud는 API·인터넷·사용량 관리에 의존한다.",
              "- Customization: Local은 양자화·자체 서빙 등 제어 범위가 넓다. Cloud는 제공 API 범위에서 설정한다.", "",
              "### Representative Success / Failure Cases", "",
              "- Local 성공: F의 Q01 두 회차는 평균 4.50점. 배송 확인 순서를 제시했다 (원본 점수·근거: `docs/eval-results.md`).",
              "- Local 실패: C의 Q04 두 회차 평균 1.75점. 확인되지 않은 환불 가능성을 단정한 응답이 있다.",
              "- Cloud 성공: Q06은 기존 채점 5.00점이며 요청한 FAQ 유형을 제시했다 (`docs/cloud-compare.md`).",
              "- Cloud 실패/제한: Q10은 4.00점으로 채점되었지만 `api_status=incomplete`, 출력 768토큰으로 응답이 끝나 정상 완료되지 않았다.", "",
              "### Limitations", "",
              "공통 질문은 5개뿐이고 Local은 질문당 2회, Cloud는 1회다. Local은 단일 Windows/GPU 환경에서 측정했고 Cloud elapsed에는 네트워크가 포함된다. "
              "토크나이저와 모델 계열, 도메인 Fine-tuning 이력이 다르므로 점수·토큰·시간 차이를 단일 원인으로 돌릴 수 없다. "
              "작은 평가셋이며 Cloud Q10 미완료 사유와 실제 청구액은 원본에 없다.", "",
              "### STEP 08 Handoff", "",
              "STEP 07에서는 최종 Local 모델을 선정하지 않는다. STEP 08에서 사전 확정한 필수 통과 조건과 모델 선호 우선순위를 적용하고, "
              "최종 Local 1개 선정·선택 및 탈락 이유·운영 권고를 기록한다.",
    ]
    return "\n".join(lines)


def write() -> str:
    return _inject(config.DOCS_DIR / "steps" / "step07.md", build())


if __name__ == "__main__":
    print(write())

"""기록된 회차를 사람이 읽을 수 있게 훑어본다.

    uv run python -m evalkit.peek              최근 5건 요약
    uv run python -m evalkit.peek --model B    Model B 진행 상황
    uv run python -m evalkit.peek --run B_Q01_r1   한 회차 전문
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from . import config, recorder

#: 한 줄 요약에 보여줄 지표
BRIEF = (
    ("elapsed_sec", "응답", "{:.2f}s"),
    ("load_duration_sec", "로딩", "{:.2f}s"),
    ("eval_count", "출력토큰", "{:.0f}"),
    ("tokens_per_sec", "생성속도", "{:.1f}t/s"),
    ("size_vram_mib", "VRAM", "{:.0f}MiB"),
)


def _brief(rec: dict[str, Any]) -> str:
    parts = []
    for key, label, fmt in BRIEF:
        v = rec.get(key)
        parts.append(f"{label}={fmt.format(v)}" if v is not None else f"{label}=null")
    return "  ".join(parts)


def show_recent(limit: int, model: str | None) -> None:
    records = [r for r in recorder.iter_records(config.LOCAL_RUNS_PATH)]
    if model:
        records = [r for r in records if r.get("model_label") == model]

    if not records:
        print("기록이 없습니다.")
        return

    for rec in records[-limit:]:
        mark = "OK " if rec.get("status") == config.STATUS_SUCCESS else "ERR"
        print(f"[{mark}] {rec['run_id']:<18} {_brief(rec)}")
        if rec.get("done_reason") == "length":
            print("        done_reason=length — 출력 한도에서 잘린 답변")
        if rec.get("status") == config.STATUS_ERROR:
            print(f"        {rec.get('error_type')}: {rec.get('error_message')}")
        # 같은 사유가 여러 지표에 붙는 경우가 많아 사유 기준으로 묶는다.
        grouped: dict[str, list[str]] = {}
        for field, reason in (rec.get("measurement_notes") or {}).items():
            grouped.setdefault(reason, []).append(field)
        for reason, fields in grouped.items():
            shown = ", ".join(fields[:4]) + (f" 외 {len(fields) - 4}개" if len(fields) > 4 else "")
            print(f"        ! {shown}: {reason}")


def show_progress() -> None:
    """모델별 진행 상황 — 계획 대비 몇 건을 기록했는가."""
    settings = config.load_run_settings()
    total = len(config.load_questions()["questions"]) * settings["repeats"]
    records = list(recorder.iter_records(config.LOCAL_RUNS_PATH))

    print(f"{'모델':<6} {'본실험':>10} {'성공':>6} {'실패':>6} {'워밍업':>7}")
    for m in config.enabled_models():
        label = m["model_label"]
        rows = [r for r in records if r.get("model_label") == label]
        main = [r for r in rows if r.get("phase") == config.PHASE_MAIN]
        ok = sum(1 for r in main if r.get("status") == config.STATUS_SUCCESS)
        warm = "있음" if any(r.get("phase") == config.PHASE_WARMUP for r in rows) else "없음"
        print(f"{label:<6} {f'{len(main)}/{total}':>10} {ok:>6} {len(main) - ok:>6} {warm:>7}")


def show_one(run_id: str) -> None:
    found = recorder_trace(run_id)
    if found is None:
        print(f"{run_id} 기록을 찾지 못했습니다.")
        return
    print(json.dumps(found, ensure_ascii=False, indent=2))


def recorder_trace(run_id: str) -> dict[str, Any] | None:
    for path in (config.LOCAL_RUNS_PATH, config.CLOUD_RUNS_PATH):
        for rec in recorder.iter_records(path):
            if rec.get("run_id") == run_id:
                return rec
    return None


def main() -> None:
    from . import use_utf8_stdout

    use_utf8_stdout()
    p = argparse.ArgumentParser(description="기록된 회차 훑어보기")
    p.add_argument("--model", help="특정 model_label 만")
    p.add_argument("--run", help="한 회차 전문 출력")
    p.add_argument("-n", type=int, default=5, help="최근 몇 건 (기본 5)")
    p.add_argument("--progress", action="store_true", help="모델별 진행 상황만")
    args = p.parse_args()

    if args.run:
        show_one(args.run)
        return

    show_progress()
    if not args.progress:
        print()
        show_recent(args.n, args.model)


if __name__ == "__main__":
    main()

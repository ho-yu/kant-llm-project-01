"""채점용 빈 레코드를 scores.jsonl 에 미리 깔아둔다.

runs.jsonl 을 읽어 회차마다 빈 채점 레코드를 만든다.
run_id / question_id / model_label / 기준 코드는 원본에서 그대로 가져오므로
손으로 적다가 틀릴 일이 없다. 사람은 점수와 근거만 채우면 된다.

점수는 절대 여기서 매기지 않는다. 전부 null 로 두고 나간다.

호출이 실패한 회차(status="error")는 채점 대상이 아니므로
not_scored_reason 을 채워 두고 점수는 null 로 남긴다.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Iterable

from . import config, recorder


def _existing_score_ids() -> set[str]:
    return {
        s["run_id"]
        for s in recorder.iter_records(config.SCORES_PATH)
        if s.get("run_id")
    }


def build_pending(
    phases: Iterable[str] = config.AGGREGATED_PHASES,
    include_warmup: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    """아직 채점 레코드가 없는 회차들의 빈 레코드를 만든다."""
    qmap = config.question_map()
    already = _existing_score_ids()
    scope = set(phases)
    if include_warmup:
        scope.add(config.PHASE_WARMUP)

    pending: list[dict[str, Any]] = []
    skipped: list[str] = []

    for source, path in (("local", config.LOCAL_RUNS_PATH), ("cloud", config.CLOUD_RUNS_PATH)):
        for run in recorder.iter_records(path):
            run_id = run.get("run_id")
            if not run_id:
                continue
            if run.get("phase") not in scope:
                continue
            if run_id in already:
                skipped.append(run_id)
                continue

            qid = run.get("question_id")
            question = qmap.get(qid or "")
            if question is None:
                skipped.append(run_id)
                continue

            rec = recorder.new_score_record(
                run_id=run_id,
                source_file=source,
                question_id=qid,
                model_label=run.get("model_label"),
                criteria_codes=question["criteria_codes"],
            )

            # 호출 실패는 채점 대상이 아니다. 점수는 null 로 두고 사유만 남긴다.
            if run.get("status") == config.STATUS_ERROR:
                rec["not_scored_reason"] = (
                    f"호출 실패 (status=error, {run.get('error_type')})"
                )

            pending.append(rec)

    return pending, skipped


def _summarize(pending: list[dict[str, Any]]) -> str:
    by_model: dict[str, int] = {}
    for r in pending:
        by_model[r["model_label"]] = by_model.get(r["model_label"], 0) + 1
    return ", ".join(f"{k}: {v}건" for k, v in sorted(by_model.items())) or "없음"


def run(dry_run: bool = False, include_warmup: bool = False) -> None:
    from . import use_utf8_stdout

    use_utf8_stdout()
    pending, skipped = build_pending(include_warmup=include_warmup)

    print(f"채점 레코드를 만들 회차: {len(pending)}건 ({_summarize(pending)})")
    if skipped:
        print(f"건너뜀: {len(skipped)}건 (이미 채점 레코드가 있거나 질문 ID 없음)")

    not_scored = [r for r in pending if r.get("not_scored_reason")]
    if not_scored:
        print(f"  이 중 {len(not_scored)}건은 호출 실패라 not_scored_reason 만 채워집니다")

    if not pending:
        print("\n새로 만들 레코드가 없습니다. runs.jsonl 이 비어 있는지 확인하세요.")
        return

    if dry_run:
        print("\n샘플:")
        print(json.dumps(pending[0], ensure_ascii=False, indent=2))
        print("\n(dry-run — 저장하지 않았습니다)")
        return

    log = recorder.RunLog(config.SCORES_PATH)
    for rec in pending:
        log.append(rec)

    print(f"\n{log.summary()}")
    print(f"파일: {config.SCORES_PATH}")
    print("\n각 줄의 scores / rationales 를 채우세요. average 는 비워두면")
    print("aggregator 가 기준별 평균을 따로 계산합니다.")


def main() -> None:
    p = argparse.ArgumentParser(description="채점용 빈 레코드 생성")
    p.add_argument("--dry-run", action="store_true", help="저장하지 않고 개수만 출력")
    p.add_argument("--include-warmup", action="store_true", help="워밍업도 채점 대상에 포함")
    a = p.parse_args()
    run(dry_run=a.dry_run, include_warmup=a.include_warmup)


if __name__ == "__main__":
    main()

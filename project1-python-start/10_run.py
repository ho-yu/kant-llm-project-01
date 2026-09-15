"""모델 하나를 실행하고 STEP 04 / STEP 06 형식으로 결과를 보여줍니다.

    uv run python 10_run.py

아래 MODEL 만 B -> C -> D -> E 순서로 바꿔 가며 실행합니다.
출력은 그대로 docs/steps/step04.md, step06.md 에 붙일 수 있는 형태입니다.

중단해도 됩니다. 다시 실행하면 이미 기록된 회차는 건너뛰고 이어집니다.
"""

from evalkit import collect_env, report, run_local

# ---------------------------------------------------------------- 여기만 바꿉니다

MODEL = "A"        # A 법률 / B 의료·바이오 / C 금융 / D 코딩 / E 수학 / F 이커머스

LIMIT = None          # 본 실험을 몇 건까지 할지. 처음엔 3, 확인되면 None 으로 바꿔 전체(20건)

# ----------------------------------------------------------------

print(report.BAR)
print(f"  {MODEL} 실행")
print(report.BAR)

# 실험 전에 반드시 정해져 있어야 하는 값 확인
problems = report.preflight()
if problems:
    print("\n실험을 시작할 수 없습니다. data/config/run_settings.json 을 먼저 채우세요.\n")
    for p in problems:
        print(f"  - {p}")
    raise SystemExit(1)

# 환경 정보는 매번 갱신해 둔다 (여러 번 실행해도 안전)
collect_env.run()

print("\n" + report.BAR)
print("  실행")
print(report.BAR)
run_local.run_all(only_model=MODEL, limit=LIMIT)

print("\n" + report.BAR)
print("  진행 상황")
print(report.BAR)
print(report.progress(MODEL))

print("\n" + report.BAR)
print("  STEP 04")
print(report.BAR + "\n")
print(report.step04(MODEL))

print("\n" + report.BAR)
print("  STEP 06")
print(report.BAR + "\n")
print(report.step06(MODEL))

# 같은 내용을 파일로도 남긴다. 매번 복사해 붙이지 않아도 된다.
print("\n" + report.BAR)
print("  파일로도 저장했습니다")
print(report.BAR)
for path in report.write_step_docs():
    print("  ", path)

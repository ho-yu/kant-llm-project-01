"""실행 환경 정보를 자동 수집해 data/env/environment.json 에 채운다.

자동으로 채우는 것
    OS / Python / Ollama / 패키지 버전, GPU·VRAM·CPU·시스템 RAM,
    모델별 digest / quantization_level / 다운로드 크기 (client.list())

사람이 채워야 하는 것 (여기서 건드리지 않는다)
    Model Card URL, License(선언/Base), 문서상 최대 Context,
    execution_type, colab_used

기존 파일을 병합한다. 사람이 적어둔 값은 덮어쓰지 않고,
수집에 실패한 항목은 0 이 아니라 null 로 두고 notes 에 사유를 남긴다.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from typing import Any

from . import config


# ---------------------------------------------------------------- 개별 수집기


def _run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def collect_ollama_version(notes: dict[str, str]) -> str | None:
    raw = _run(["ollama", "--version"])
    if raw is None:
        notes["runtime.ollama_version"] = "`ollama --version` 실행 실패"
        return None
    # "ollama version is 0.34.0" -> "0.34.0"
    return raw.split()[-1] if raw else None


def collect_packages(notes: dict[str, str]) -> dict[str, str | None]:
    from importlib.metadata import PackageNotFoundError, version

    out: dict[str, str | None] = {}
    for name in ("ollama", "openai"):
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
            notes[f"runtime.packages.{name}"] = "설치되어 있지 않음"
    return out


def collect_gpu(notes: dict[str, str]) -> dict[str, Any]:
    raw = _run([
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits",
    ])
    if raw is None:
        notes["hardware.gpu_name"] = "nvidia-smi 실행 실패 (GPU 없음 또는 미설치)"
        notes["hardware.vram_total_mib"] = "nvidia-smi 실행 실패"
        return {"gpu_name": None, "vram_total_mib": None}

    first = raw.splitlines()[0]
    parts = [p.strip() for p in first.split(",")]
    if len(parts) < 2:
        notes["hardware.gpu_name"] = f"nvidia-smi 출력 형식 예상과 다름: {first!r}"
        return {"gpu_name": None, "vram_total_mib": None}

    try:
        vram = int(parts[1])
    except ValueError:
        vram = None
        notes["hardware.vram_total_mib"] = f"VRAM 값을 숫자로 읽지 못함: {parts[1]!r}"
    return {"gpu_name": parts[0], "vram_total_mib": vram}


def collect_system_ram(notes: dict[str, str]) -> float | None:
    """시스템 RAM(GB). VRAM 과 별개 항목이다."""
    try:
        import psutil  # 선택 의존성

        return round(psutil.virtual_memory().total / 1_073_741_824, 1)
    except ImportError:
        pass

    if sys.platform == "win32":
        try:
            import ctypes

            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(MemoryStatusEx)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return round(stat.ullTotalPhys / 1_073_741_824, 1)
        except Exception as e:
            notes["hardware.system_ram_gb"] = f"측정 실패: {type(e).__name__}"
            return None

    notes["hardware.system_ram_gb"] = "측정 방법 없음 (psutil 미설치)"
    return None


def collect_model_info(notes: dict[str, str]) -> dict[str, dict[str, Any]]:
    """client.list() 에서 모델 태그별 digest / 양자화 / 다운로드 크기를 읽는다."""
    try:
        from ollama import Client

        settings = config.load_run_settings()
        client = Client(host=settings["host"], timeout=settings.get("timeout_sec"))
        listing = client.list()
    except Exception as e:
        notes["models"] = f"client.list() 실패: {type(e).__name__} — Ollama 실행 중인지 확인"
        return {}

    out: dict[str, dict[str, Any]] = {}
    for entry in getattr(listing, "models", []) or []:
        tag = getattr(entry, "model", None) or getattr(entry, "name", None)
        if not tag:
            continue
        details = getattr(entry, "details", None)
        out[tag] = {
            "digest": getattr(entry, "digest", None),
            "quantization_level": getattr(details, "quantization_level", None) if details else None,
            "parameter_size": getattr(details, "parameter_size", None) if details else None,
            "download_size_bytes": getattr(entry, "size", None),
        }
    return out


# ---------------------------------------------------------------- 병합


#: 자동 수집이 값을 채우는 경로. 이외의 필드는 건드리지 않는다.
AUTO_PATHS = (
    "platform.os",
    "platform.os_version",
    "runtime.llm_runtime",
    "runtime.ollama_version",
    "runtime.ollama_host",
    "runtime.python_version",
    "runtime.packages.ollama",
    "runtime.packages.openai",
    "hardware.gpu_name",
    "hardware.vram_total_mib",
    "hardware.cpu",
    "hardware.system_ram_gb",
)

#: 모델 항목 중 자동으로 채우는 키. 나머지(License, Model Card URL,
#: 문서상 최대 Context)는 사람이 직접 확인해야 하므로 손대지 않는다.
AUTO_MODEL_KEYS = ("digest", "quantization_level", "download_size_bytes")


def _set(
    target: dict[str, Any],
    path: str,
    value: Any,
    changes: list[str],
    resolved: list[str] | None = None,
) -> None:
    """점 경로에 값을 넣는다. 값이 None 이면 기존 값을 지우지 않는다.

    값을 채우면 그 경로의 이전 실패 사유는 더 이상 사실이 아니므로
    resolved 에 담아 두었다가 notes 에서 제거한다.
    """
    if value is None:
        return
    if resolved is not None:
        resolved.append(path)
    keys = path.split(".")
    node = target
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    before = node.get(keys[-1])
    if before == value:
        return
    node[keys[-1]] = value
    changes.append(f"{path}: {before!r} -> {value!r}")


def build(existing: dict[str, Any]) -> tuple[dict[str, Any], list[str], dict[str, str]]:
    notes: dict[str, str] = {}
    changes: list[str] = []
    resolved: list[str] = []  # 이번에 값을 채운 경로 — 옛 실패 사유를 지운다
    env = json.loads(json.dumps(existing))  # 깊은 복사

    settings = config.load_run_settings()

    _set(env, "platform.os", platform.system(), changes, resolved)
    _set(env, "platform.os_version", platform.version(), changes, resolved)
    _set(env, "runtime.llm_runtime", "Ollama", changes, resolved)
    _set(env, "runtime.ollama_version", collect_ollama_version(notes), changes, resolved)
    _set(env, "runtime.ollama_host", settings.get("host"), changes, resolved)
    _set(env, "runtime.python_version", platform.python_version(), changes, resolved)

    for name, ver in collect_packages(notes).items():
        _set(env, f"runtime.packages.{name}", ver, changes, resolved)

    gpu = collect_gpu(notes)
    _set(env, "hardware.gpu_name", gpu["gpu_name"], changes, resolved)
    _set(env, "hardware.vram_total_mib", gpu["vram_total_mib"], changes, resolved)
    _set(env, "hardware.cpu", platform.processor() or None, changes, resolved)
    _set(env, "hardware.system_ram_gb", collect_system_ram(notes), changes, resolved)

    # --- 모델별 정보 --------------------------------------------------
    listed = collect_model_info(notes)
    by_tag = {m["model_tag"]: m for m in config.enabled_models()}

    entries: list[dict[str, Any]] = []
    existing_entries = {
        m.get("model_tag"): m for m in env.get("models", []) if isinstance(m, dict)
    }
    template = next(
        (m for m in existing.get("models", []) if isinstance(m, dict)), {}
    )

    for label_info in config.enabled_models():
        tag = label_info["model_tag"]
        entry = existing_entries.get(tag)
        if entry is None:
            # 기존 템플릿의 키 구성을 유지한 빈 항목을 만든다.
            # "_" 로 시작하는 주석 키는 설명이므로 값을 그대로 둔다.
            entry = {
                k: (v if k.startswith("_") else None) for k, v in template.items()
            }
        entry["model_label"] = label_info["model_label"]
        entry["model_tag"] = tag

        info = listed.get(tag)
        if info is None:
            notes[f"models[{label_info['model_label']}]"] = (
                "client.list() 목록에 없음 — 아직 pull 하지 않았을 수 있음"
            )
        else:
            for key in AUTO_MODEL_KEYS:
                if info.get(key) is not None:
                    before = entry.get(key)
                    if before != info[key]:
                        entry[key] = info[key]
                        changes.append(f"models[{entry['model_label']}].{key}: {before!r} -> {info[key]!r}")
                    resolved.append(f"models[{entry['model_label']}].{key}")
            if str(info.get("quantization_level", "")).lower() == "unknown":
                notes[f"models[{label_info['model_label']}].quantization_level"] = (
                    "Ollama 가 'unknown' 으로 보고함 — 모델 태그 기준값을 함께 기재할 것"
                )

        entries.append(entry)

    env["models"] = entries
    env["recorded_at"] = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")

    # 기존 notes 와 병합 (사람이 적은 메모를 지우지 않는다).
    # 단, 이번에 값을 채운 경로의 옛 실패 사유는 더 이상 사실이 아니므로 버린다.
    # 값과 사유가 동시에 남으면 기록이 서로 모순된다.
    carried = {
        k: v
        for k, v in (env.get("notes") or {}).items()
        if not k.startswith("_") and k != "example_field_path" and k not in resolved and v is not None
    }
    carried.update(notes)
    env["notes"] = carried

    return env, changes, notes


def manual_todo(env: dict[str, Any]) -> list[str]:
    """사람이 채워야 하는데 아직 비어 있는 항목."""
    todo = []
    if not (env.get("platform") or {}).get("execution_type"):
        todo.append("platform.execution_type (예: Local PC)")
    for m in env.get("models", []):
        label = m.get("model_label")
        for key, desc in (
            ("model_card_url", "Model Card URL"),
            ("license_declared", "저장소 선언 License"),
            ("license_base_model", "Base model License"),
            ("doc_max_context", "문서상 최대 Context"),
        ):
            if not m.get(key):
                todo.append(f"models[{label}].{key} — {desc}")
    return todo


def run(dry_run: bool = False) -> None:
    """수집하고 결과를 출력한다. dry_run 이면 파일을 쓰지 않는다."""
    from . import use_utf8_stdout

    use_utf8_stdout()
    existing = config.load_environment()
    env, changes, notes = build(existing)

    print("=== 수집 결과 ===")
    if changes:
        for c in changes:
            print(f"  {c}")
    else:
        print("  변경 없음")

    if notes:
        print("\n=== 수집 실패 / 주의 (값은 null 로 둠) ===")
        for k, v in notes.items():
            print(f"  {k}: {v}")

    todo = manual_todo(env)
    if todo:
        print("\n=== 직접 채워야 하는 항목 ===")
        for t in todo:
            print(f"  {t}")

    if dry_run:
        print("\n(dry-run — 파일을 쓰지 않았습니다)")
        return

    config.ENVIRONMENT_PATH.write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nwritten: {config.ENVIRONMENT_PATH}")


def main() -> None:
    p = argparse.ArgumentParser(description="실행 환경 정보 자동 수집")
    p.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 결과만 출력")
    run(dry_run=p.parse_args().dry_run)


if __name__ == "__main__":
    main()

# PAIQM_Launcher/game_launcher.py
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

# Make package imports robust when executed as a plain script
PKG_DIR = Path(__file__).resolve().parent
if __package__ in (None, ""):
    # allow absolute package imports when run as "python game_launcher.py"
    sys.path.insert(0, str(PKG_DIR.parent))


def _call_backend_via_import(args: list[str]) -> bool:
    """
    Try to import the backend relatively and call its main(*args).
    Returns True if it ran, False if we should fall back to a subprocess.
    """
    try:
        from . import launcher_backend  # relative import, package-friendly
    except Exception:
        return False

    try:
        launcher_backend.main(*args)
        return True
    except SystemExit as e:
        # propagate non-zero exit codes
        code = e.code or 0
        if code != 0:
            sys.exit(code)
        return True
    except Exception as e:
        print(f"[ERROR] Backend exception: {e}")
        sys.exit(1)


def _call_backend_subprocess(args: list[str]) -> None:
    """
    Fallback: spawn a fresh Python process to run the backend.
    Prefer `-m package.module`; if package name is unknown, direct-file path.
    """
    module = f"{__package__}.launcher_backend" if __package__ else "PAIQM_Launcher.launcher_backend"

    # Ensure the parent of the package is on PYTHONPATH so `-m` works even when not installed
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR.parent) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [sys.executable, "-m", module, *args]
    print(">", " ".join(map(str, cmd)))
    try:
        subprocess.check_call(cmd, cwd=str(PKG_DIR), env=env)
    except subprocess.CalledProcessError as e:
        print("[ERROR] Step failed with non-zero exit.")
        sys.exit(e.returncode)
    except Exception as e:
        # As a last resort, try direct file execution
        backend_path = PKG_DIR / "launcher_backend.py"
        if backend_path.exists():
            cmd2 = [sys.executable, str(backend_path), *args]
            print(">", " ".join(map(str, cmd2)))
            subprocess.check_call(cmd2, cwd=str(PKG_DIR), env=env)
        else:
            print(f"[ERROR] Could not locate backend module or file: {e}")
            sys.exit(1)


def run_step(description: str, args: list[str]):
    print(f"\n=== {description} ===")
    # 1) Try relative import (fast, same interpreter)
    if _call_backend_via_import(args):
        return
    # 2) Fallback to subprocess (-m), robust across cwd/installation modes
    _call_backend_subprocess(args)


def game_verifier_main(game_name: str):
    # Optional sanity check (useful during development)
    if not (PKG_DIR / "launcher_backend.py").exists():
        print("Error: launcher_backend.py not found next to game_launcher.py.")
        sys.exit(1)

    run_step("1) Sync remote manifests", ["sync"])
    run_step("2) Install quantum-dice", ["install", game_name])
    # run_step("3) Run quantum-dice", ["run", game_name])


def game_launcher_main(game_name: str):
    # Optional sanity check (useful during development)
    if not (PKG_DIR / "launcher_backend.py").exists():
        print("Error: launcher_backend.py not found next to game_launcher.py.")
        sys.exit(1)

    # run_step("1) Sync remote manifests", ["sync"])
    # run_step("2) Install quantum-dice", ["install", game_name])
    run_step("3) Run quantum-dice", ["run", game_name])
    run_step("4) Check local status", ["status"])


# if __name__ == "__main__":
#     # Example manual run
#     game_launcher_main("quantum-dice")

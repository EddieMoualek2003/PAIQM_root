# PAIQM_Launcher/launcher_backend.py
from __future__ import annotations

import argparse, json, os, subprocess, sys, venv
from pathlib import Path

# -------------------------
# Bootstrap so this file works when:
# - imported as part of the package (relative imports)
# - run as a module:    python -m PAIQM_Launcher.launcher_backend ...
# - run as a script:    python PAIQM_Launcher/launcher_backend.py ...
# -------------------------
PKG_DIR = Path(__file__).resolve().parent
if __package__ in (None, ""):
    # Allow absolute package imports when executed as a plain script
    sys.path.insert(0, str(PKG_DIR.parent))

# -------------------------
# Paths & helpers
# -------------------------
HOME = Path.home()
PAIQM_ROOT = HOME / ".paiqm"
GAMES_ROOT = PAIQM_ROOT / "games"
for p in (GAMES_ROOT,):
    p.mkdir(parents=True, exist_ok=True)

def _find_registry() -> Path:
    """Resolve registry.json robustly:
       1) PAIQM_REGISTRY env var (if set)
       2) next to this file (package resource)
       3) current working directory
    """
    env = os.getenv("PAIQM_REGISTRY")
    if env:
        p = Path(env).expanduser().resolve()
        return p
    pkg_path = PKG_DIR / "registry.json"
    if pkg_path.exists():
        return pkg_path
    cwd_path = Path.cwd() / "registry.json"
    return cwd_path

REGISTRY = _find_registry()

def run_cmd(cmd, cwd: Path | None = None, env: dict | None = None):
    print(">", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, env=env)

def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

# Third-party (keep imports here so script bootstrap above runs first)
import requests, yaml  # noqa: E402

def fetch_manifest(game_entry: dict):
    url = game_entry["manifest_url"]
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    return yaml.safe_load(res.text)

def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

# -------------------------
# Commands
# -------------------------
def sync():
    reg = load_registry()
    for g in reg["games"]:
        m = fetch_manifest(g)
        print(f"{g['id']}: remote v{m['version']}")

def install(game_id: str):
    reg = load_registry()
    entry = next(g for g in reg["games"] if g["id"] == game_id)
    manifest = fetch_manifest(entry)

    base = GAMES_ROOT / game_id
    repo_dir = base / "repo"
    venv_dir = base / "venv"
    base.mkdir(parents=True, exist_ok=True)

    if not repo_dir.exists():
        run_cmd(["git", "clone", entry["repo"], str(repo_dir)])
    run_cmd(["git", "checkout", entry["ref"]], cwd=repo_dir)

    if not venv_dir.exists():
        venv.EnvBuilder(with_pip=True).create(str(venv_dir))

    pip = venv_python(venv_dir)

    run_cmd([str(pip), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    deps = manifest.get("requirements", {}).get("pip", [])
    if deps:
        try:
            run_cmd([str(pip), "-m", "pip", "install", "--no-cache-dir", *deps])
        except subprocess.CalledProcessError:
            print("[WARN] First install attempt failed. Retrying without cache...")
            run_cmd([str(pip), "-m", "pip", "install", "--no-cache-dir", *deps])

    (base / "installed.json").write_text(json.dumps({
        "id": manifest["id"],
        "version": manifest["version"]
    }, indent=2), encoding="utf-8")

    print(f"Installed {game_id} v{manifest['version']}")

def run(game_id: str):
    reg = load_registry()
    entry = next(g for g in reg["games"] if g["id"] == game_id)
    manifest = fetch_manifest(entry)

    base = GAMES_ROOT / game_id
    repo_dir = base / "repo"
    venv_dir = base / "venv"
    python = venv_python(venv_dir)

    module = manifest["runtime"]["entry"]["module"]
    args = manifest["runtime"]["entry"].get("args", [])

    run_cmd([str(python), "-m", module, *args], cwd=repo_dir)

def status():
    for g in GAMES_ROOT.iterdir():
        meta = g / "installed.json"
        if meta.exists():
            data = json.loads(meta.read_text(encoding="utf-8"))
            print(f"{data['id']}: INSTALLED v{data['version']}")
        else:
            print(f"{g.name}: not installed")

# -------------------------
# Public entry point (works for import, -m, and direct script)
# -------------------------
def main(*cli_args: str):
    if cli_args:
        # Called programmatically: main("install", "quantum-dice")
        args = _parse_args(list(cli_args))
    else:
        # Called from CLI
        args = _parse_args()

    if args.cmd == "sync":
        sync()
    elif args.cmd == "install":
        install(args.game_id)
    elif args.cmd == "run":
        run(args.game_id)
    elif args.cmd == "status":
        status()

def _parse_args(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(prog="PAIQM_Launcher")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("sync")
    pi = sp.add_parser("install"); pi.add_argument("game_id")
    pr = sp.add_parser("run");     pr.add_argument("game_id")
    sp.add_parser("status")
    return ap.parse_args(argv)

if __name__ == "__main__":
    # Works both as script and as module
    main(*sys.argv[1:])

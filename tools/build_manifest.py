from __future__ import annotations
from pathlib import Path
import subprocess, sys, tomllib, shutil

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "paiqm_root.yaml"
GAME_ID = "paiqm-launcher"
PKG = "PAIQM_Launcher"

def run(*cmd, cwd=ROOT):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

def read_pyproject(default_version: str | None = None):
    """
    Reads project metadata from pyproject.toml.
    If default_version is provided, it overrides the version in pyproject.toml.
    """
    pp = ROOT / "pyproject.toml"
    if not pp.exists():
        return GAME_ID, (default_version or "0.0.0"), []
    data = tomllib.loads(pp.read_text(encoding="utf-8"))
    proj = data.get("project", {})
    name = proj.get("name", GAME_ID)
    version = default_version or proj.get("version", "0.0.0")
    deps = proj.get("dependencies", [])
    return name, version, deps

def write_manifest(name: str, version: str, deps: list[str]):
    req_block = "".join(f"    - {d}\n" for d in deps) or "    - qiskit\n"
    text = f"""\
schema_version: 1
id: {GAME_ID}
name: "{name}"
version: "{version}"
description: "PAIQM Root Project"
author: "Eddie Moualek"
license: "MIT"

requirements:
  python: ">=3.11,<3.13"
  pip:
{req_block}runtime:
  type: "python"
  entry:
    module: "{PKG}"
    args: []
ui:
  icon: ""
  categories: ["education","infrastructure"]

compatibility:
  raspi_models: ["Pi 4","Pi 5"]
  min_ram_mb: 2048

hooks:
  post_clone: []
"""
    MANIFEST.write_text(text, encoding="utf-8")
    print(f"Wrote {MANIFEST}")

def build():
    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    run(sys.executable, "-m", "build")

def git_push():
    # Push manifest + build artifacts (dist + egg-info if present)
    run("git", "add", "paiqm_game.yaml", "pyproject.toml")
    run("git", "add", "paiqm_root.yaml")
    if (ROOT / "dist").exists():
        run("git", "add", "dist")
    for egg in ROOT.glob("*.egg-info"):
        run("git", "add", str(egg))
    run("git", "commit", "-m", "chore: update manifest and build", cwd=ROOT)
    run("git", "push")

def main():
    # allow passing version as command-line arg
    custom_version = sys.argv[1] if len(sys.argv) > 1 else None

    name, version, deps = read_pyproject(default_version=custom_version)
    write_manifest(name, version, deps)
    build()
    try:
        git_push()
    except subprocess.CalledProcessError:
        print("Nothing to commit (maybe manifest unchanged).")

if __name__ == "__main__":
    main()

from pathlib import Path
import subprocess
import sys

def run_step(description: str, args: list[str]):
    print(f"\n=== {description} ===")
    cmd = [sys.executable, "launcher_backend.py", *args]
    print(">", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Step failed: {description}")
        sys.exit(e.returncode)

def main():
    # Ensure we are in the same folder as launcher_backend.py
    here = Path(__file__).parent
    backend = here / "launcher_backend.py"
    if not backend.exists():
        print("Error: launcher_backend.py not found in this folder.")
        sys.exit(1)

    run_step("1) Sync remote manifests", ["sync"])
    run_step("2) Install quantum-dice", ["install", "quantum-dice"])
    run_step("3) Run quantum-dice", ["run", "quantum-dice"])
    run_step("4) Check local status", ["status"])

if __name__ == "__main__":
    main()

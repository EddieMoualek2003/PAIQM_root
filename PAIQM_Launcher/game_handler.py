################################################################################
# Company:              Independent.
# Engineer:             Eddie Moualek
#
# Create Date:          14.09.2025
# Design Name:          PAIQM_Launcher
# File Name:            game_handler.py
# Project Name:         PAIQM
# Target Devices:       Windows, Linux, MacOS
# Tool Versions:        Python 3.13
# Description:          Handles game download, update and execution.
#
# Dependencies:   
#
# Revision:
#     Rev 0.01 - File Created
#
# Additional Comments:
"""
    - Serves two purposes:
        - Handles game installation/updating, where the latest version is pulled from GitHub.
        - Runs the game.
"""
#
################################################################################

## Imports
import requests
import subprocess
import sys
import tempfile
from pathlib import Path

def install_latest_release(owner: str, repo: str):
    """
    Download and install the latest release from a GitHub repo using pip.
    :param owner: GitHub username or organization
    :param repo: Repository name
    """
    # Get latest release metadata
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    r = requests.get(url)
    r.raise_for_status()
    release = r.json()

    # Look for a wheel or source distribution in assets
    asset = None
    for a in release["assets"]:
        if a["name"].endswith((".whl", ".tar.gz", ".zip")):
            asset = a
            break
    if not asset:
        raise RuntimeError("No suitable asset (.whl, .tar.gz, .zip) found in latest release")

    # Download to temp file
    print(f"Downloading {asset['name']} from {asset['browser_download_url']}")
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / asset["name"]

    with requests.get(asset["browser_download_url"], stream=True) as resp:
        resp.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    # Install with pip
    print(f"Installing {file_path}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", str(file_path)])

def run_module(module_name: str):
    """
    Run a Python module as if with `python -m modulename`.
    """
    print(f"Running module: {module_name}")
    subprocess.check_call([sys.executable, "-m", module_name])


# def main(owner:str, game_root: str, game_name: str):
#     install_latest_release(owner, game_root)
#     run_module(game_name)

# if __name__ == "__main__":
#     install_latest_release("EddieMoualek2003", "PAIQM_root")

#     # Example: run the launcher module
#     run_module("PAIQM_Launcher")

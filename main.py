"""
Financial Assistant - Google Agent Development Kit (ADK 2.0) Entry Point.
"""

import os
import sys
import subprocess
from pathlib import Path
from src.config import HOST, PORT

PROJECT_ROOT = Path(__file__).resolve().parent
AGENT_DIR = PROJECT_ROOT / "src" / "agent"


def main():
    """Launch the official Google ADK 2.0 Web UI."""
    print(f"🚀 Starting Google ADK 2.0 Web UI for Financial Assistant at: {AGENT_DIR}")

    # Set PYTHONPATH so ADK dynamic loader resolves the 'src' package
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{PROJECT_ROOT}{os.pathsep}{current_pythonpath}"
        if current_pythonpath
        else str(PROJECT_ROOT)
    )

    cmd = [
        sys.executable,
        "-m",
        "google.adk.cli.cli",
        "web",
        str(AGENT_DIR),
        "--host",
        str(HOST),
        "--port",
        str(PORT),
    ]
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 ADK Web UI stopped.")


if __name__ == "__main__":
    main()

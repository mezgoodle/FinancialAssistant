"""
Financial Assistant - Google Agent Development Kit (ADK 2.0) Entry Point.
"""

import os
import sys
import subprocess
from pathlib import Path
from src.config import HOST, PORT

AGENT_DIR = Path(__file__).resolve().parent / "src" / "agent"


def main():
    """Launch the official Google ADK 2.0 Web UI."""
    print(f"🚀 Starting Google ADK 2.0 Web UI for Financial Assistant at: {AGENT_DIR}")
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
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 ADK Web UI stopped.")


if __name__ == "__main__":
    main()

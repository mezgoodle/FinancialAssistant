import sys
from pathlib import Path

# Ensure project root is always in sys.path for ADK dynamic loader
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.agent.agent import root_agent
from src.agent.assistant import FinancialAssistantAgent

__all__ = ["root_agent", "FinancialAssistantAgent"]

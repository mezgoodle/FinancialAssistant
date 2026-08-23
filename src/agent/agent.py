"""
Official Google Agent Development Kit (ADK 2.0) Financial Assistant Agent.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from google.adk.agents.llm_agent import Agent
from src.agent.tools import (
    ingest_financial_file,
    query_transactions,
    get_period_summary,
    compare_periods,
)
from src.config import GEMINI_MODEL

SYSTEM_INSTRUCTION = """Ти — професійний, точний та уважний персональний фінансовий асистент.
Твоє головне завдання — допомагати користувачеві аналізувати його доходи та витрати на основі реальних даних, завантажених із банківських виписок та файлів додатків (CSV, XLSX: Money Manager, Monobank, ПриватБанк).

КРИТИЧНІ ПРАВИЛА:
1. Завжди спирайся ВИКЛЮЧНО на реальні дані, отримані через виклики інструментів (tools).
2. НІКОЛИ не вигадуй суми, транзакції, дати чи категорії. Якщо даних за певний період немає або вони неповні — чесно про це повідоми.
3. При порівнянні періодів (місяць до місяця, рік до року) чітко вказуй різницю в абсолютних значеннях (грн/валюта) та у відсотках.
4. Оформлюй відповіді структуровано: використовуй списки, жирний шрифт для сум та чисті Markdown-таблиці для категорій.
5. Спілкуйся українською мовою.
"""

root_agent = Agent(
    name="financial_assistant",
    model=GEMINI_MODEL,
    description="Персональний фінансовий асистент для аналізу виписок та витрат.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        ingest_financial_file,
        query_transactions,
        get_period_summary,
        compare_periods,
    ],
)

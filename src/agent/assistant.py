from typing import Any, Callable, List, Optional
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.agent.tools import ALL_TOOLS

SYSTEM_INSTRUCTION = """Ти — професійний, точний та уважний персональний фінансовий асистент.
Твоє головне завдання — допомагати користувачеві аналізувати його доходи та витрати на основі реальних даних, завантажених із файлів (CSV, XLSX).

КРИТИЧНІ ПРАВИЛА:
1. Завжди спирайся ВИКЛЮЧНО на реальні дані, отримані через виклики інструментів (tools).
2. НІКОЛИ не вигадуй суми, транзакції, дати чи категорії. Якщо даних за певний період немає або вони неповні — чесно про це повідоми.
3. При порівнянні періодів (місяць до місяця, рік до року) чітко вказуй різницю в абсолютних значеннях (грн/валюта) та у відсотках.
4. Оформлюй відповіді структуровано: використовуй списки, жирний шрифт для сум та чисті Markdown-таблиці для категорій.
5. Спілкуйся українською мовою (або мовою користувача, якщо він запитує іншою).
"""


class FinancialAssistantAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        tools: Optional[List[Callable[..., Any]]] = None,
    ):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self.tools = tools if tools is not None else ALL_TOOLS
        
        self.client = genai.Client(api_key=self.api_key)
        self.chat = None
        self._init_chat_session()

    def _init_chat_session(self):
        config_params = {
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.2,  # Low temperature for analytical accuracy
        }
        if self.tools:
            config_params["tools"] = self.tools

        config = types.GenerateContentConfig(**config_params)
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=config,
        )

    def set_tools(self, tools: List[Callable[..., Any]]):
        """Update tools and refresh chat session."""
        self.tools = tools
        self._init_chat_session()

    def send_message(self, message: str) -> str:
        """Send message to the agent and receive response."""
        if not self.chat:
            self._init_chat_session()
        response = self.chat.send_message(message)
        return response.text

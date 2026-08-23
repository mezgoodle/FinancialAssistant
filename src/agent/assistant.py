import os
from typing import Any, Callable, List, Optional
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from src.config import GEMINI_API_KEY

if GEMINI_API_KEY and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY


class FinancialAssistantAgent:
    """
    Google Agent Development Kit (ADK 2.0) Financial Assistant runner.
    """

    def __init__(
        self,
        agent: Optional[Agent] = None,
        session_id: str = "default_session",
        user_id: str = "default_user",
    ):
        from src.agent.agent import root_agent
        self.agent = agent or root_agent
        self.session_id = session_id
        self.user_id = user_id
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="financial_assistant",
            session_service=self.session_service,
        )

    def send_message(self, message: str) -> str:
        """Send a message to the agent using the ADK 2.0 Runner."""
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )

        reply_texts = []
        for event in self.runner.run(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        reply_texts.append(part.text)
            elif hasattr(event, "text") and event.text:
                reply_texts.append(event.text)

        return "".join(reply_texts) or "Немає відповіді від асистента."

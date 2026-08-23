import pytest
from src.agent.tools import reset_repository


@pytest.fixture(autouse=True)
def clean_repository_state():
    reset_repository()
    yield
    reset_repository()

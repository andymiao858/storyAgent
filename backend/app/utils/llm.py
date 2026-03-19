"""LLM client wrapper using OpenAI-compatible API."""
from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.LLM_API_KEY,
        openai_api_base=settings.LLM_BASE_URL,
        temperature=temperature,
    )

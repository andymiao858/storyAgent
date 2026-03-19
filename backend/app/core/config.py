from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "AI Children Story System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://localhost/storyagent"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # LLM (OpenAI-compatible)
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_API_KEY: str = "your-api-key-here"
    LLM_MODEL: str = "qwen3.5-flash-2026-02-23"

    # Embedding
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"

    # RAG
    RAG_DATA_DIR: str = "rag_data"
    FAISS_INDEX_DIR: str = "faiss_index"
    RAG_TOP_K: int = 5

    # Safety
    MAX_STORY_SCENES: int = 8
    MAX_SCENE_LENGTH: int = 500

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

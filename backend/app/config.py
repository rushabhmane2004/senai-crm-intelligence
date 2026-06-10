import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/senai_crm"
    BACKEND_PORT: int = 8000
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""

    # Read from .env file if it exists, checking multiple fallback locations relative to config.py
    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(__file__), ".env"),
            os.path.join(os.path.dirname(__file__), "..", ".env"),
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

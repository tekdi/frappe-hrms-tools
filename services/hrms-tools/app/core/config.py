"""
Core configuration for CV Analysis Service
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "CV Analysis Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM Provider Configuration
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, anthropic, gemini, auto
    DEFAULT_PROMPT_VERSION: str = "v1"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 4000

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_TEMPERATURE: float = 0.3
    ANTHROPIC_MAX_TOKENS: int = 4000

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 4000

    # Database
    DATABASE_PATH: str = "database/audit_logs.db"

    # Document Processing
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx"]

    # Request Limits
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 2
    REQUEST_TIMEOUT_SECONDS: int = 120

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings

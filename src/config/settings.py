"""Configuration settings for the AI agent application."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class APISettings(BaseModel):
    """API server configuration settings."""

    host: str = Field(default=os.getenv("API_HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("API_PORT", "8000")))
    debug: bool = Field(default=os.getenv("API_DEBUG", "false").lower() == "true")


class GigachatSettings(BaseModel):
    """Gigachat API configuration settings."""

    api_key: str = Field(default=os.getenv("GIGACHAT_API_KEY", ""))
    credentials_path: Optional[str] = Field(default=os.getenv("GIGACHAT_CREDENTIALS_PATH", None))
    model: str = Field(default=os.getenv("GIGACHAT_MODEL", "GigaChat"))
    temperature: float = Field(default=float(os.getenv("GIGACHAT_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default=int(os.getenv("GIGACHAT_MAX_TOKENS", "2048")))


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    log_file: Optional[str] = Field(default=os.getenv("LOG_FILE", None))


class Settings(BaseModel):
    """Global application settings."""

    api: APISettings = Field(default_factory=APISettings)
    gigachat: GigachatSettings = Field(default_factory=GigachatSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    def dict_config(self) -> Dict[str, Any]:
        """Convert settings to a dictionary."""
        return self.model_dump()


# Create global settings instance
settings = Settings()

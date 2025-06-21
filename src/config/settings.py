"""Настройки конфигурации для приложения ИИ-агента."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Загрузка переменных окружения из файла .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")




class OllamaSettings(BaseModel):
    """Настройки конфигурации Ollama API."""

    base_url: str = Field(default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    model: str = Field(default=os.getenv("OLLAMA_MODEL", "llama2"))
    temperature: float = Field(default=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")))
    top_k: int = Field(default=int(os.getenv("OLLAMA_TOP_K", "10")))
    top_p: float = Field(default=float(os.getenv("OLLAMA_TOP_P", "0.9")))
    repeat_penalty: float = Field(default=float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1")))
    max_tokens: int = Field(default=int(os.getenv("OLLAMA_MAX_TOKENS", "2048")))


class LoggingSettings(BaseModel):
    """Настройки конфигурации логирования."""

    level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    log_file: Optional[str] = Field(default=os.getenv("LOG_FILE", None))


class DatabaseSettings(BaseModel):
    """Настройки конфигурации базы данных."""

    host: str = Field(default=os.getenv("DB_HOST", "localhost"))
    port: int = Field(default=int(os.getenv("DB_PORT", "5432")))
    name: str = Field(default=os.getenv("DB_NAME", "parameters_db"))
    user: str = Field(default=os.getenv("DB_USER", "postgres"))
    password: str = Field(default=os.getenv("DB_PASSWORD", "postgres_password"))
    min_connections: int = Field(default=int(os.getenv("MIN_CONNECTIONS", "1")))
    max_connections: int = Field(default=int(os.getenv("MAX_CONNECTIONS", "10")))

    def get_connection_string(self) -> str:
        """Получить строку подключения к базе данных."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class EmbeddingsSettings(BaseModel):
    """Настройки конфигурации эмбеддингов."""
    
    # Тип эмбеддингов по умолчанию: "huggingface" или "gigachat"
    default_type: str = Field(default=os.getenv("DEFAULT_EMBEDDINGS_TYPE", "huggingface"))
    

class GigaChatSettings(BaseModel):
    """Настройки конфигурации GigaChat API."""
    
    api_key: Optional[str] = Field(default=os.getenv("GIGACHAT_API_KEY", None))
    base_url: str = Field(default=os.getenv("GIGACHAT_BASE_URL", "https://gigachat.api.url"))
    model: str = Field(default=os.getenv("GIGACHAT_MODEL", "GigaChat"))
    temperature: float = Field(default=float(os.getenv("GIGACHAT_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default=int(os.getenv("GIGACHAT_MAX_TOKENS", "2048")))


class Settings(BaseModel):
    """Глобальные настройки приложения."""

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    embeddings: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)
    gigachat: GigaChatSettings = Field(default_factory=GigaChatSettings)

    def dict_config(self) -> Dict[str, Any]:
        """Преобразовать настройки в словарь."""
        return self.model_dump()


# Создание глобального экземпляра настроек
settings = Settings()

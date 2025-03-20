"""Настройки конфигурации для приложения ИИ-агента."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Загрузка переменных окружения из файла .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class APISettings(BaseModel):
    """Настройки конфигурации API-сервера."""

    host: str = Field(default=os.getenv("API_HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("API_PORT", "8000")))
    debug: bool = Field(default=os.getenv("API_DEBUG", "false").lower() == "true")


class GigachatSettings(BaseModel):
    """Настройки конфигурации API Gigachat."""

    api_key: str = Field(default=os.getenv("GIGACHAT_API_KEY", ""))
    credentials_path: Optional[str] = Field(default=os.getenv("GIGACHAT_CREDENTIALS_PATH", None))
    model: str = Field(default=os.getenv("GIGACHAT_MODEL", "GigaChat"))
    temperature: float = Field(default=float(os.getenv("GIGACHAT_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default=int(os.getenv("GIGACHAT_MAX_TOKENS", "2048")))


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


class KafkaSettings(BaseModel):
    """Настройки конфигурации Kafka."""

    bootstrap_servers: str = Field(default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    topic: str = Field(default=os.getenv("KAFKA_TOPIC", "sql-generator-requests"))
    group_id: str = Field(default=os.getenv("KAFKA_GROUP_ID", "sql-generator-group"))
    auto_offset_reset: str = Field(default=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"))
    enable_auto_commit: bool = Field(default=os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "true").lower() == "true")
    consumer_timeout_ms: int = Field(default=int(os.getenv("KAFKA_CONSUMER_TIMEOUT_MS", "1000")))


class Settings(BaseModel):
    """Глобальные настройки приложения."""

    api: APISettings = Field(default_factory=APISettings)
    gigachat: GigachatSettings = Field(default_factory=GigachatSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)

    def dict_config(self) -> Dict[str, Any]:
        """Преобразовать настройки в словарь."""
        return self.model_dump()


# Создание глобального экземпляра настроек
settings = Settings()

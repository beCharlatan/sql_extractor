"""Модели данных для приложения генератора SQL."""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
import hashlib
from typing import Optional


class TaskSubtype(str, Enum):
    """Перечисление возможных подтипов задач."""
    
    NEW_SALARY_AGREEMENT = "Новый зарплатный договор"
    EXTEND_SALARY_AGREEMENT = "Расширение зарплатного договора"


class GenerateSQLRequest(BaseModel):
    """Модель запроса для генерации SQL."""

    hash: Optional[str] = Field(
        None,
        description="Уникальный идентификатор запроса",
        pattern="^[a-fA-F0-9]{32}$",
    )
    gosb_id: str = Field(
        ...,
        description="ГОСБ Руководителя ЗП",
        min_length=1,
    )
    tb_id: str = Field(
        ...,
        description="Территориальный банк Руководителя ЗП",
        min_length=1,
    )
    pers_number: str = Field(
        ...,
        description="Табельный номер Руководителя ЗП",
        min_length=1,
    )
    filter: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="Строка фильтра для обработки",
        examples=["Найти товары в категории электроника с ценой менее 1000"],
    )
    constraint: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="Строка ограничений для обработки",
        examples=["Отсортировать по наивысшему рейтингу и ограничить до 10 результатов"],
    )
    
    @field_validator('filter')
    @classmethod
    def filter_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Текст фильтра не может быть пустым или содержать только пробелы')
        return v
    
    @field_validator('constraint')
    @classmethod
    def constraint_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Текст ограничений не может быть пустым или содержать только пробелы')
        return v
    
    def model_post_init(self, __context) -> None:
        """Генерация хеша, если он не предоставлен."""
        if not self.hash:
            # Создание MD5 хеша из полей фильтра и ограничений
            combined = f"{self.filter}{self.constraint}".encode('utf-8')
            self.hash = hashlib.md5(combined).hexdigest()


class SQLComponents(BaseModel):
    """Компоненты SQL запроса."""

    where_clause: str = Field(
        default="",
        description="Условие WHERE (без ключевого слова 'WHERE')",
    )
    group_by_clause: str = Field(
        default="",
        description="Условие GROUP BY (без ключевого слова 'GROUP BY')",
    )
    having_clause: str = Field(
        default="",
        description="Условие HAVING (без ключевого слова 'HAVING')",
    )
    order_by_clause: str = Field(
        default="",
        description="Условие ORDER BY (без ключевого слова 'ORDER BY')",
    )
    limit_clause: str = Field(
        default="",
        description="Условие LIMIT (без ключевого слова 'LIMIT')",
    )
    full_sql: str = Field(
        default="",
        description="Объединенные компоненты SQL",
    )

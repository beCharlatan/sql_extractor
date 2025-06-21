"""Модели данных для приложения генератора SQL."""

from enum import Enum


class TaskSubtype(str, Enum):
    """Перечисление возможных подтипов задач."""
    
    NEW_SALARY_AGREEMENT = "Новый зарплатный договор"
    EXTEND_SALARY_AGREEMENT = "Расширение зарплатного договора"

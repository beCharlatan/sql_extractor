"""Сервис для определения подтипа задачи для организаций."""

from typing import List, Dict, Any
from loguru import logger

from src.models import TaskSubtype
from src.utils.errors import handle_exception


class TaskSubtypeProcessor:
    """Сервис для определения подтипа задачи для организаций."""

    def __init__(self):
        """Инициализация сервиса определения подтипа задачи."""
        pass

    async def process_organizations(self, organizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработка списка организаций для определения подтипа задачи.
        
        Args:
            organizations: Список организаций для обработки.
            
        Returns:
            Список организаций с добавленным подтипом задачи.
        """
        try:
            enriched_organizations = []
            
            for org in organizations:
                # Определяем подтип задачи на основе наличия зарплатного договора
                task_subtype = (
                    TaskSubtype.NEW_SALARY_AGREEMENT 
                    if not org.get("is_salary_agreement", False)
                    else TaskSubtype.EXTEND_SALARY_AGREEMENT
                )
                
                # Создаем копию организации с добавленным подтипом задачи
                enriched_org = org.copy()
                enriched_org["task_subtype"] = task_subtype.value
                enriched_organizations.append(enriched_org)
                
                logger.debug(f"Processed organization {org.get('id')} with task subtype: {task_subtype.value}")
            
            logger.info(f"Successfully processed {len(organizations)} organizations")
            return enriched_organizations
            
        except Exception as e:
            error_msg = f"Failed to process organizations: {str(e)}"
            logger.error(error_msg)
            handle_exception(e)
            raise 
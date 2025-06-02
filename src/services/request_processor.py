"""Сервис для обработки запросов на генерацию SQL."""

from typing import Dict, Any, Optional, List
from loguru import logger

from src.agent.agent import GigachatAgent
from src.agent.sql_generator import SQLGenerator
from src.kafka.result_producer import ResultProducer
from src.models import GenerateSQLRequest
from src.db.db_schema_tool import DBSchemaReferenceTool
from src.services.organization_processor import OrganizationProcessor
from src.services.task_subtype_processor import TaskSubtypeProcessor
from src.utils.errors import (
    SQLGenerationError,
    handle_exception,
)


class RequestProcessor:
    """Сервис для обработки запросов на генерацию SQL."""

    def __init__(
        self,
        sql_generator: Optional[SQLGenerator] = None,
        result_producer: Optional[ResultProducer] = None,
        organization_processor: Optional[OrganizationProcessor] = None,
        task_subtype_processor: Optional[TaskSubtypeProcessor] = None,
    ):
        """Инициализация сервиса обработки запросов.
        
        Args:
            sql_generator: Опциональный экземпляр SQLGenerator. Если не указан, будет создан новый.
            result_producer: Опциональный экземпляр ResultProducer. Если не указан, будет создан новый.
            organization_processor: Опциональный экземпляр OrganizationProcessor. Если не указан, будет создан новый.
            task_subtype_processor: Опциональный экземпляр TaskSubtypeProcessor. Если не указан, будет создан новый.
        """
        self.sql_generator = sql_generator
        self.result_producer = result_producer
        self.organization_processor = organization_processor
        self.task_subtype_processor = task_subtype_processor

    async def _create_sql_generator(self) -> SQLGenerator:
        """Асинхронное создание нового экземпляра генератора SQL."""
        try:
            agent = GigachatAgent()
            db_schema_tool = await DBSchemaReferenceTool.create()
            return await SQLGenerator.create(agent=agent, db_schema_tool=db_schema_tool)
        except Exception as e:
            error_msg = f"Failed to initialize SQL generator: {str(e)}"
            logger.error(error_msg)
            raise SQLGenerationError(error_msg, details={"original_error": str(e)})

    async def _create_result_producer(self) -> ResultProducer:
        """Асинхронное создание нового экземпляра производителя результатов."""
        try:
            producer = ResultProducer()
            await producer.start()
            return producer
        except Exception as e:
            error_msg = f"Failed to initialize result producer: {str(e)}"
            logger.error(error_msg)
            raise SQLGenerationError(error_msg, details={"original_error": str(e)})

    async def _create_organization_processor(self) -> OrganizationProcessor:
        """Асинхронное создание нового экземпляра процессора организаций."""
        try:
            processor = OrganizationProcessor()
            return processor
        except Exception as e:
            error_msg = f"Failed to initialize organization processor: {str(e)}"
            logger.error(error_msg)
            raise SQLGenerationError(error_msg, details={"original_error": str(e)})

    async def _create_task_subtype_processor(self) -> TaskSubtypeProcessor:
        """Асинхронное создание нового экземпляра процессора подтипов задач."""
        try:
            processor = TaskSubtypeProcessor()
            return processor
        except Exception as e:
            error_msg = f"Failed to initialize task subtype processor: {str(e)}"
            logger.error(error_msg)
            raise SQLGenerationError(error_msg, details={"original_error": str(e)})

    async def start(self):
        """Запуск сервиса и инициализация компонентов."""
        if self.sql_generator is None:
            self.sql_generator = await self._create_sql_generator()
            
        if self.result_producer is None:
            self.result_producer = await self._create_result_producer()
            
        if self.organization_processor is None:
            self.organization_processor = await self._create_organization_processor()
            
        if self.task_subtype_processor is None:
            self.task_subtype_processor = await self._create_task_subtype_processor()

    async def stop(self):
        """Остановка сервиса и его компонентов."""
        if self.result_producer is not None:
            await self.result_producer.stop()
            logger.info("Stopped result producer")

    async def _process_organization_batches(
        self,
        organizations: List[Dict[str, Any]],
        sql_components: Dict[str, Any],
        request_hash: str
    ) -> None:
        """Обработка и отправка батчей организаций.
        
        Args:
            organizations: Список организаций для обработки
            sql_components: SQL компоненты для отправки
            request_hash: Хеш запроса
        """
        batch_size = 20
        organization_batches = [organizations[i:i + batch_size] 
                              for i in range(0, len(organizations), batch_size)]
        
        for i, batch in enumerate(organization_batches):
            is_last = (i == len(organization_batches) - 1)
            await self.result_producer.send_result(
                sql_components=sql_components,
                request_hash=request_hash,
                organizations=batch,
                is_last=is_last
            )
            logger.info(f"Published batch {i + 1}/{len(organization_batches)} with {len(batch)} organizations")

    async def process_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка запроса на генерацию SQL.
        
        Args:
            message: Сообщение с запросом.
            
        Returns:
            Результат обработки запроса.
        """
        try:
            # Проверка и валидация запроса
            request = GenerateSQLRequest(**message)
            request_hash = request.hash

            # Генерация SQL компонентов
            logger.info("Generating SQL components from request")
            logger.debug(f"Filter: {request.filter}")
            logger.debug(f"Constraint: {request.constraint}")
            
            generator_result = await self.sql_generator.generate_sql_components(
                filter_text=request.filter,
                constraint_text=request.constraint,
            )
            
            # Получение списка организаций
            sql_components = generator_result["sql_components"]
            organizations = await self.organization_processor.process_sql_components(
                sql_components, 
                gosb_id=request.gosb_id, 
                tb_id=request.tb_id, 
                pers_number=request.pers_number
            )
            
            # Определение подтипов задач для организаций
            enriched_organizations = await self.task_subtype_processor.process_organizations(organizations)
            
            # Обработка и отправка батчей организаций
            await self._process_organization_batches(
                organizations=enriched_organizations,
                sql_components=sql_components,
                request_hash=request_hash
            )
            
            result = {
                "sql_components": sql_components,
                "request_hash": request_hash,
                "organizations": enriched_organizations
            }
            
            logger.info("Successfully generated SQL components and processed organizations")
            logger.debug(f"SQL components: {sql_components}")
            logger.debug(f"Processed {len(enriched_organizations)} organizations")
            
            return result

        except Exception as e:
            handle_exception(e)
            return e
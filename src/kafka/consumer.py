"""Реализация Kafka-потребителя для обработки запросов на генерацию SQL."""

from typing import Any, Dict, Optional
from pydantic import ValidationError as PydanticValidationError
from loguru import logger

from src.agent.agent import GigachatAgent
from src.agent.sql_generator import SQLGenerator
from src.kafka.base_consumer import BaseKafkaConsumer
from src.models import GenerateSQLRequest
from src.db.db_schema_tool import DBSchemaReferenceTool
from src.db.report_client import ReportClient
from src.utils.errors import (
    DatabaseError,
    GigachatAPIError,
    InvalidSQLError,
    KafkaError,
    SQLGenerationError,
    ValidationError,
    handle_exception,
)


class KafkaConsumer(BaseKafkaConsumer):
    """Специализированный Kafka-потребитель для обработки запросов на генерацию SQL."""

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
        consumer_timeout_ms: int = 1000,
        sql_generator: Optional[SQLGenerator] = None,
        db_client: Optional[ReportClient] = None,
    ):
        """Инициализация специализированного Kafka-потребителя для генерации SQL.
        
        Аргументы:
            bootstrap_servers: Серверы Kafka. По умолчанию settings.kafka.bootstrap_servers.
            topic: Тема Kafka для потребления. По умолчанию settings.kafka.topic.
            group_id: ID группы потребителей. По умолчанию settings.kafka.group_id.
            auto_offset_reset: Стратегия сброса смещения. По умолчанию "earliest".
            enable_auto_commit: Включить автоматическую фиксацию. По умолчанию True.
            consumer_timeout_ms: Тайм-аут потребителя в миллисекундах. По умолчанию 1000.
            sql_generator: Опциональный экземпляр SQLGenerator. Если не указан, будет создан новый.
            db_client: Опциональный экземпляр ReportClient. Если не указан, будет создан новый.
        """
        # Вызов инициализатора базового класса для настройки Kafka
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            consumer_timeout_ms=consumer_timeout_ms
        )
        
        # Инициализация свойств, которые будут заполнены при старте
        self.sql_generator = sql_generator
        self.db_client = db_client
    
    async def _create_sql_generator(self) -> SQLGenerator:
        """Асинхронное создание нового экземпляра генератора SQL.
        
        Возвращает:
            Экземпляр SQLGenerator.
            
        Вызывает исключение:
            KafkaError: Если инициализация генератора SQL не удалась.
        """
        try:
            agent = GigachatAgent()
            db_schema_tool = await DBSchemaReferenceTool.create()
            return await SQLGenerator.create(agent=agent, db_schema_tool=db_schema_tool)
        except Exception as e:
            error_msg = f"Failed to initialize SQL generator: {str(e)}"
            logger.error(error_msg)
            raise KafkaError(error_msg, details={"original_error": str(e)})
    
    async def start(self, max_retries=5, retry_delay=5):
        """Расширенный запуск, включающий подключение к PostgreSQL и Kafka.
        
        Аргументы:
            max_retries: Максимальное количество попыток подключения. По умолчанию 5.
            retry_delay: Задержка между попытками в секундах. По умолчанию 5.
        
        Вызывает исключение:
            KafkaError: Если инициализация потребителя не удалась после всех попыток.
            DatabaseError: Если подключение к PostgreSQL не удалось.
        """
        # Инициализация зависимостей, если они не были предоставлены
        if self.sql_generator is None:
            self.sql_generator = await self._create_sql_generator()
            
        if self.db_client is None:
            try:
                logger.info("Initializing connection to PostgreSQL database...")
                self.db_client = await ReportClient.create()
            except Exception as e:
                error_msg = f"Failed to connect to PostgreSQL database: {str(e)}"
                logger.error(error_msg)
                raise DatabaseError(error_msg, details={"original_error": str(e)})
            
        # Вызов метода start базового класса для подключения к Kafka
        await super().start(max_retries=max_retries, retry_delay=retry_delay)
    
    async def stop(self):
        """Расширенная остановка, включающая отключение от PostgreSQL и Kafka."""
        # Вызов метода stop базового класса для остановки Kafka-потребителя
        await super().stop()
        
        # Отключение от PostgreSQL
        if self.db_client is not None:
            await self.db_client.close()
            logger.info("Disconnected from PostgreSQL database")
    

    async def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка одного сообщения из Kafka и сохранение результатов в PostgreSQL.
        
        Аргументы:
            message: Сообщение из Kafka.
            
        Возвращает:
            Результат обработки.
            
        Вызывает исключение:
            ValidationError: Если проверка сообщения не удалась.
            KafkaError: Если обработка сообщения не удалась.
            DatabaseError: Если сохранение результата в PostgreSQL не удалось.
        """
        try: 
            # Извлечение ID сообщения
            message_id = message.get("message_id")
            
            # Проверка всего сообщения с использованием модели Pydantic
            try:
                # Попытка разбора и проверки сообщения с использованием модели GenerateSQLRequest
                request = GenerateSQLRequest(**message)
            except PydanticValidationError as e:
                # Получение подробной информации об ошибке проверки
                error_details = {"original_error": str(e)}
                
                # Попытка предоставить более конкретные сведения об ошибке, если это возможно
                if hasattr(e, "errors") and isinstance(e.errors(), list):
                    field_errors = {}
                    for error in e.errors():
                        loc = '.'.join(str(l) for l in error.get('loc', []))
                        if loc:
                            field_errors[loc] = error.get('msg', 'Validation error')
                    if field_errors:
                        error_details["field_errors"] = field_errors
                
                logger.warning(f"Invalid message format: {str(e)}")
                logger.debug(f"Message details: {message}")
                
                # Сохранение ошибки проверки, если у нас есть message_id
                if message_id and self.db_client:
                    filter_text = message.get("filter", "")
                    constraint_text = message.get("constraint", "")
                    request_hash = None
                    
                    # Попытка сгенерировать хеш, если это возможно
                    if isinstance(filter_text, str) and isinstance(constraint_text, str):
                        try:
                            temp_request = GenerateSQLRequest(filter=filter_text, constraint=constraint_text)
                            request_hash = temp_request.hash
                        except:
                            pass
                    
                    await self.db_client.store_error(
                        filter_text=str(filter_text),
                        constraint_text=str(constraint_text),
                        error_message=f"Message validation failed: {str(e)}",
                        message_id=message_id,
                        request_hash=request_hash
                    )
                
                raise ValidationError(
                    "Message does not match expected format",
                    details=error_details
                )
            
            # Генерация SQL компонентов
            logger.info("Generating SQL components from Kafka message")
            logger.debug(f"Filter: {request.filter}")
            logger.debug(f"Constraint: {request.constraint}")
            
            generator_result = await self.sql_generator.generate_sql_components(
                filter_text=request.filter,
                constraint_text=request.constraint,
            )
            
            # Сохранение результата в PostgreSQL
            sql_components = generator_result["sql_components"]
            await self.db_client.store_result(
                filter_text=request.filter,
                constraint_text=request.constraint,
                sql_components=sql_components,
                message_id=message_id,
                request_hash=request.hash
            )
            logger.info(f"Stored SQL generation result in PostgreSQL with message_id: {message_id}")
            
            # Создание ответа
            result = {
                "sql_components": sql_components,
                "message_id": message_id,
                "request_hash": request.hash
            }
            
            logger.info("Successfully generated SQL components from Kafka message")
            logger.debug(f"SQL components: {sql_components}")
            
            return result
        
        except (ValidationError, DatabaseError, InvalidSQLError) as e:
            # Ошибки проверки и базы данных
            handle_exception(e)
            error_message = f"{type(e).__name__}: {str(e)}"
            
            # Генерация хеша запроса, если это возможно
            try:
                request = GenerateSQLRequest(
                    filter=message.get("filter", ""), 
                    constraint=message.get("constraint", "")
                )
                request_hash = request.hash
            except Exception:
                # Если проверка не удалась, используем None для хеша
                request_hash = None
                
            # Сохранение ошибки в PostgreSQL
            try:
                await self.db_client.store_error(
                    filter_text=message.get("filter", ""),
                    constraint_text=message.get("constraint", ""),
                    error_message=error_message,
                    message_id=message.get("message_id"),
                    request_hash=request_hash
                )
                logger.info(f"Stored validation/database error in PostgreSQL with message_id: {message.get('message_id')}")
            except Exception as db_error:
                logger.error(f"Failed to store error in PostgreSQL: {str(db_error)}")
            
            error_result = {
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "details": getattr(e, "details", {}),
                },
                "message_id": message.get("message_id"),
                "request_hash": request_hash if 'request_hash' in locals() else None,
            }
            return error_result
        except GigachatAPIError as e:
            # Ошибки Gigachat API
            handle_exception(e)
            error_message = f"GigachatAPIError: {str(e)}"
            
            # Генерация хеша запроса, если это возможно
            try:
                request = GenerateSQLRequest(
                    filter=message.get("filter", ""), 
                    constraint=message.get("constraint", "")
                )
                request_hash = request.hash
            except Exception:
                # Если проверка не удалась, используем None для хеша
                request_hash = None
                
            # Сохранение ошибки в PostgreSQL
            try:
                await self.db_client.store_error(
                    filter_text=message.get("filter", ""),
                    constraint_text=message.get("constraint", ""),
                    error_message=error_message,
                    message_id=message.get("message_id"),
                    request_hash=request_hash
                )
                logger.info(f"Stored Gigachat API error in PostgreSQL with message_id: {message.get('message_id')}")
            except Exception as db_error:
                logger.error(f"Failed to store error in PostgreSQL: {str(db_error)}")
            
            error_result = {
                "error": {
                    "type": "GigachatAPIError",
                    "message": str(e),
                    "details": getattr(e, "details", {}),
                },
                "message_id": message.get("message_id"),
                "request_hash": request_hash if 'request_hash' in locals() else None,
            }
            return error_result
        except SQLGenerationError as e:
            # Ошибки генерации SQL
            handle_exception(e)
            error_message = f"SQLGenerationError: {str(e)}"
            
            # Генерация хеша запроса, если это возможно
            try:
                request = GenerateSQLRequest(
                    filter=message.get("filter", ""), 
                    constraint=message.get("constraint", "")
                )
                request_hash = request.hash
            except Exception:
                # Если проверка не удалась, используем None для хеша
                request_hash = None
                
            # Сохранение ошибки в PostgreSQL
            try:
                await self.db_client.store_error(
                    filter_text=message.get("filter", ""),
                    constraint_text=message.get("constraint", ""),
                    error_message=error_message,
                    message_id=message.get("message_id"),
                    request_hash=request_hash
                )
                logger.info(f"Stored SQL generation error in PostgreSQL with message_id: {message.get('message_id')}")
            except Exception as db_error:
                logger.error(f"Failed to store error in PostgreSQL: {str(db_error)}")
            
            error_result = {
                "error": {
                    "type": "SQLGenerationError",
                    "message": str(e),
                    "details": getattr(e, "details", {}),
                },
                "message_id": message.get("message_id"),
                "request_hash": request_hash if 'request_hash' in locals() else None,
            }
            return error_result
        except Exception as e:
            # Другие непредвиденные ошибки
            handle_exception(e)
            logger.exception(f"Unexpected error processing Kafka message: {str(e)}")
            error_message = f"UnexpectedError: {str(e)}"
            
            # Генерация хеша запроса, если это возможно
            try:
                request = GenerateSQLRequest(
                    filter=message.get("filter", ""), 
                    constraint=message.get("constraint", "")
                )
                request_hash = request.hash
            except Exception:
                # Если проверка не удалась, используем None для хеша
                request_hash = None
                
            # Сохранение ошибки в PostgreSQL
            try:
                await self.db_client.store_error(
                    filter_text=message.get("filter", ""),
                    constraint_text=message.get("constraint", ""),
                    error_message=error_message,
                    message_id=message.get("message_id"),
                    request_hash=request_hash
                )
                logger.info(f"Stored unexpected error in PostgreSQL with message_id: {message.get('message_id')}")
            except Exception as db_error:
                logger.error(f"Failed to store error in PostgreSQL: {str(db_error)}")
            
            error_result = {
                "error": {
                    "type": "UnexpectedError",
                    "message": f"Unexpected error: {str(e)}",
                },
                "message_id": message.get("message_id"),
                "request_hash": request_hash if 'request_hash' in locals() else None,
            }
            return error_result

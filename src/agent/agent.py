"""Реализация ИИ-агента с использованием LangChain и различных моделей (локальных и облачных)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from loguru import logger
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel
from langchain_community.llms import Ollama
from langchain_gigachat import GigaChat
from langchain.callbacks.base import BaseCallbackHandler

from src.config.settings import settings, AgentType
from src.tools.okved_tool import get_okved_tool
from src.tools.okato_tool import get_okato_tool
from src.tools.oktmo_tool import get_oktmo_tool
from src.tools.db_schema_tool_wrapper import get_table_schema_tool, get_table_columns_tool


class AnswerStopHandler(BaseCallbackHandler):
    """Обработчик обратного вызова для остановки агента при обнаружении ключевого слова 'Ответ:'."""
    
    def __init__(self):
        super().__init__()
        self.stopped = False
        self.answer = None
        self.full_text = ""
        self.answer_text = ""
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Вызывается при получении нового токена от LLM."""
        self.full_text += token
        
        # Проверяем наличие ключевого слова "Ответ:"
        if "Ответ:" in self.full_text and not self.stopped:
            self.stopped = True
            logger.info("Обнаружено ключевое слово 'Ответ:', останавливаем выполнение агента")
            
            # Извлекаем текст после "Ответ:"
            parts = self.full_text.split("Ответ:", 1)
            if len(parts) > 1:
                self.answer_text = parts[1].strip()
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Вызывается при завершении генерации LLM."""
        # Если мы еще не обнаружили ключевое слово, проверяем еще раз
        if not self.stopped and "Ответ:" in self.full_text:
            self.stopped = True
            logger.info("Обнаружено ключевое слово 'Ответ:' при завершении генерации")
            
            # Извлекаем текст после "Ответ:"
            parts = self.full_text.split("Ответ:", 1)
            if len(parts) > 1:
                self.answer_text = parts[1].strip()


class BaseAgent(ABC):
    """Базовый класс для всех агентов на основе LangChain."""

    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """Инициализация базового агента.
        
        Аргументы:
            tools: Список инструментов для использования агентом.
        """
        self.tools = tools or []
        self.agent_executor = None
        self.llm = None

    @abstractmethod
    def _create_llm(self) -> BaseLanguageModel:
        """Создание модели языка для использования агентом.
        
        Возвращает:
            Модель языка для использования агентом.
        """
        pass

    @abstractmethod
    async def process_query(self, query: str) -> str:
        """Обработка запроса пользователя.
        
        Аргументы:
            query: Текст запроса.
            
        Возвращает:
            Результат обработки запроса.
        """
        pass

    def _create_agent_executor(self, llm: BaseLanguageModel) -> None:
        """Создание исполнителя агента с заданной моделью.
        
        Аргументы:
            llm: Модель языка для использования агентом.
        """
        # Создаем список названий инструментов
        tool_names = ", ".join([tool.name for tool in self.tools])
        
        # Создаем обработчик для остановки при обнаружении ключевого слова "Ответ:"
        answer_stop_handler = AnswerStopHandler()
        
        prompt = PromptTemplate(
        template="""Ты SQL-агент, который генерирует SQL-запросы на основе пользовательских запросов на естественном языке. Твоя задача - преобразовать запрос пользователя в корректный SQL-запрос, используя предоставленные инструменты для получения информации о структуре базы данных.

Доступные инструменты: {tool_names}

{tools}

Вот как ты должен работать:
1. Проанализируй запрос пользователя и определи, какие таблицы и поля нужны для запроса.
2. Используй инструменты get_table_schema и get_table_columns для получения информации о структуре таблиц.
3. На основе полученной информации сформируй SQL-запрос, который соответствует запросу пользователя.
4. Верни готовый SQL-запрос в формате, готовом к выполнению.

Используй СТРОГО следующий формат без отклонений:
Мысль: что я знаю и что нужно узнать
Действие: инструмент для использования
Входные данные: данные для инструмента
Наблюдение: результат использования инструмента
... (повторяй Мысль/Действие/Входные данные/Наблюдение сколько нужно раз)
Мысль: я знаю ответ
Ответ: окончательный ответ на вопрос

В своем окончательном ответе предоставь:
1. Готовый SQL-запрос, который можно выполнить
2. Краткое объяснение, как этот запрос соответствует требованиям пользователя

Важно: ВСЕГДА используй точно эти ключевые слова: "Мысль:", "Действие:", "Входные данные:", "Наблюдение:", "Ответ:" и следуй за ними без изменений.

Запрос пользователя: {input}
{agent_scratchpad}""",
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
        )

        agent = create_react_agent(
            llm=llm,
            tools=self.tools,
            prompt=prompt
        )

        # Создаем функцию для проверки наличия ключевого слова "Ответ:" в выводе агента
        def should_continue(output):
            if "Ответ:" in output:
                logger.info("Обнаружено ключевое слово 'Ответ:' в выводе агента, останавливаем выполнение")
                return False
            return True
            
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=10,  # Ограничиваем количество итераций
            return_intermediate_steps=False,  # Возвращаем только финальный результат
            callbacks=[answer_stop_handler],  # Добавляем обработчик для остановки при обнаружении "Ответ:"
            early_stopping_method="force",  # Принудительная остановка
            # Функция для проверки условия остановки
            should_continue=should_continue
        )

    @abstractmethod
    async def process_query(self, query: str) -> str:
        """Обработка запроса пользователя.
        
        Аргументы:
            query: Текст запроса.
            
        Возвращает:
            Результат обработки запроса.
        """
        pass


class GigaChatAgent(BaseAgent):
    """ИИ-агент на основе LangChain и облачной модели GigaChat."""

    def __init__(self, model: Optional[str] = None, tools: Optional[List[BaseTool]] = None):
        """Инициализация агента GigaChat.

        Аргументы:
            model: Название модели GigaChat. По умолчанию используется модель из настроек.
            tools: Список инструментов для агента.
        """
        self.model_name = model or settings.gigachat.model
        # Если инструменты не указаны, используем стандартные
        default_tools = [get_okved_tool(), get_okato_tool(), get_oktmo_tool(), get_table_schema_tool(), get_table_columns_tool()]
        super().__init__(tools or default_tools)
        self.llm = self._create_llm()
        self._create_agent_executor(self.llm)
        logger.info(f"Initialized GigaChatAgent with model {self.model_name} and {len(self.tools)} tools")

    def _create_llm(self) -> BaseLanguageModel:
        """Создание модели языка GigaChat для использования агентом.
        
        Возвращает:
            Модель языка GigaChat.
        """
        return GigaChat(
            api_key=settings.gigachat.api_key,
            base_url=settings.gigachat.base_url,
            model=self.model_name,
            temperature=settings.gigachat.temperature,
            max_tokens=settings.gigachat.max_tokens,
            verify_ssl_certs=False
        )
        
    async def process_query(self, query: str) -> str:
        """Обработка запроса пользователя.
        
        Аргументы:
            query: Текст запроса.
            
        Возвращает:
            Результат обработки запроса.
        """
        logger.info(f"Processing query: {query}...")
        try:
            # Создаем обработчик для остановки
            answer_stop_handler = AnswerStopHandler()
            
            # Выполняем запрос с обработчиком
            try:
                result = await self.agent_executor.ainvoke(
                    {"input": query},
                    callbacks=[answer_stop_handler]
                )
                
                # Проверяем, был ли агент остановлен по ключевому слову
                if answer_stop_handler.stopped:
                    logger.info("Агент был остановлен по ключевому слову 'Ответ:'")
                    # Если есть извлеченный ответ, используем его
                    if answer_stop_handler.answer_text:
                        return answer_stop_handler.answer_text
                
                # Если нет извлеченного ответа, используем результат агента
                return result["output"]
            except KeyboardInterrupt:
                # Обрабатываем прерывание пользователем
                logger.info("Выполнение агента прервано пользователем")
                # Если есть извлеченный ответ, возвращаем его
                if answer_stop_handler.answer_text:
                    return answer_stop_handler.answer_text
                # Иначе возвращаем частичный результат
                return f"Запрос был прерван. Частичный результат:\n{answer_stop_handler.full_text}"
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Если есть извлеченный ответ, возвращаем его даже при ошибке
            if 'answer_stop_handler' in locals() and answer_stop_handler.answer_text:
                return answer_stop_handler.answer_text
            raise


class OllamaAgent(BaseAgent):
    """ИИ-агент на основе LangChain и локальной модели Ollama."""

    def __init__(self, model: Optional[str] = None, tools: Optional[List[BaseTool]] = None):
        """Инициализация агента Ollama.

        Аргументы:
            model: Название модели Ollama. По умолчанию используется модель из настроек.
            tools: Список инструментов для агента.
        """
        self.model_name = model or settings.ollama.model
        # Если инструменты не указаны, используем стандартные
        default_tools = [get_okved_tool(), get_okato_tool(), get_oktmo_tool(), get_table_schema_tool(), get_table_columns_tool()]
        super().__init__(tools or default_tools)
        self.llm = self._create_llm()
        self._create_agent_executor(self.llm)
        logger.info(f"Initialized OllamaAgent with model {self.model_name} and {len(self.tools)} tools")

    def _create_llm(self) -> BaseLanguageModel:
        """Создание модели языка Ollama для использования агентом.
        
        Возвращает:
            Модель языка Ollama.
        """
        return Ollama(
            base_url=settings.ollama.base_url,
            model=self.model_name,
            temperature=settings.ollama.temperature,
            top_k=settings.ollama.top_k,
            top_p=settings.ollama.top_p,
            repeat_penalty=settings.ollama.repeat_penalty,
            num_ctx=settings.ollama.max_tokens
        )
        
    async def process_query(self, query: str) -> str:
        """Обработка запроса пользователя.
        
        Аргументы:
            query: Текст запроса.
            
        Возвращает:
            Результат обработки запроса.
        """
        logger.info(f"Processing query: {query}...")
        try:
            # Создаем обработчик для остановки
            answer_stop_handler = AnswerStopHandler()
            
            # Выполняем запрос с обработчиком
            try:
                result = await self.agent_executor.ainvoke(
                    {"input": query},
                    callbacks=[answer_stop_handler]
                )
                
                # Проверяем, был ли агент остановлен по ключевому слову
                if answer_stop_handler.stopped:
                    logger.info("Агент был остановлен по ключевому слову 'Ответ:'")
                    # Если есть извлеченный ответ, используем его
                    if answer_stop_handler.answer_text:
                        return answer_stop_handler.answer_text
                
                # Если нет извлеченного ответа, используем результат агента
                return result["output"]
            except KeyboardInterrupt:
                # Обрабатываем прерывание пользователем
                logger.info("Выполнение агента прервано пользователем")
                # Если есть извлеченный ответ, возвращаем его
                if answer_stop_handler.answer_text:
                    return answer_stop_handler.answer_text
                # Иначе возвращаем частичный результат
                return f"Запрос был прерван. Частичный результат:\n{answer_stop_handler.full_text}"
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Если есть извлеченный ответ, возвращаем его даже при ошибке
            if 'answer_stop_handler' in locals() and answer_stop_handler.answer_text:
                return answer_stop_handler.answer_text
            raise


def get_agent_class() -> Type[BaseAgent]:
    """Возвращает класс агента в зависимости от настроек.
    
    Возвращает:
        Класс агента для использования (OllamaAgent или GigaChatAgent).
    """
    agent_type = settings.default_agent_type
    if agent_type == AgentType.GIGACHAT:
        return GigaChatAgent
    else:  # По умолчанию используем Ollama
        return OllamaAgent


# Для обратной совместимости и создания экземпляра агента
Agent = get_agent_class()

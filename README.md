# Агент извлечения параметров с поддержкой выбора LLM-моделей

Проект представляет собой агента на базе LLM для извлечения параметров из текста и генерации SQL-запросов. Система поддерживает как локальные модели через Ollama, так и облачные модели через GigaChat (Сбер).

## 🌟 Возможности

- Переключение между локальными и облачными LLM моделями
- Создание RAG-систем для работы с кодами ОКВЭД, ОКАТО и другими классификаторами
- Генерация SQL-запросов на основе запросов на естественном языке
- Интеграция с базами данных для выполнения сгенерированных запросов
- Гибкая настройка параметров моделей

## 📋 Требования

- Python 3.9+
- PostgreSQL для хранения данных и индексов
- Доступ к API GigaChat (для облачной версии)
- Установленный Ollama (для локальной версии)

## 🔧 Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/your-username/extract-parameter-agent.git
cd extract-parameter-agent
```

2. Установите зависимости:

```bash
pip install -e .
```

3. Создайте файл настроек `.env` на основе примера:

```bash
cp .env.example .env
```

4. Отредактируйте файл `.env` и укажите необходимые параметры.

## ⚙️ Настройка

### Переключение между моделями

Система поддерживает два типа языковых моделей:

1. **Локальные модели** через Ollama
2. **Облачные модели** через GigaChat

Выбор модели осуществляется через переменную окружения `DEFAULT_AGENT_TYPE` в файле `.env`:

```
DEFAULT_AGENT_TYPE=ollama  # или gigachat
```

### Параметры моделей

#### Параметры Ollama

```
# Настройки Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=silmarillion/ngs-mistral-7b-instruct-v0.2-klingon-q4_0:latest
OLLAMA_TEMPERATURE=0.7
OLLAMA_TOP_K=10
OLLAMA_TOP_P=0.9
OLLAMA_REPEAT_PENALTY=1.1
OLLAMA_MAX_TOKENS=2048
```

#### Параметры GigaChat

```
# Настройки GigaChat
GIGACHAT_API_KEY=ваш_ключ_api
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
GIGACHAT_MODEL=GigaChat
GIGACHAT_TEMPERATURE=0.7
GIGACHAT_MAX_TOKENS=2048
```

### Настройки эмбеддингов

```
DEFAULT_EMBEDDINGS_TYPE=huggingface  # или gigachat
```

## 🚀 Использование

### Базовый пример

```python
from src.agent.agent import Agent
import asyncio

async def main():
    # Создание экземпляра агента (тип будет выбран на основе настроек в .env)
    agent = Agent()

    # Обработка запроса
    result = await agent.process_query("Найди продукты категории Электроника с ценой меньше 5000 рублей")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Инициализация RAG-систем

Перед первым использованием RAG-систем необходимо выполнить их инициализацию с загрузкой данных в векторные хранилища:

```python
from src.data.init_rag import initialize_all_rag_systems

# Инициализация всех RAG-систем с данными по умолчанию
initialize_all_rag_systems()

# Или с указанием путей к данным
initialize_all_rag_systems(
    okato_csv="path/to/okato.csv",
    okved_csv="path/to/okved.csv",
    oktmo_csv="path/to/oktmo.csv"
)
```

Функция `initialize_all_rag_systems` загружает данные из CSV-файлов и создает векторные индексы для последующего семантического поиска.

### Пример использования с RAG-системами

```python
from src.data.okved_rag import get_okved_rag
from src.config.settings import settings
from src.embeddings import EmbeddingsType
from loguru import logger

def test_okved_search():
    # Получаем экземпляр RAG для ОКВЭД
    embeddings_type = EmbeddingsType(settings.embeddings.default_type)
    okved_rag = get_okved_rag(collection_name="okved_collection", embeddings_type=embeddings_type)

    # Выполняем поиск
    query = "разработка программного обеспечения"
    results = okved_rag.search(query, k=3)

    # Выводим результаты
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. Код: {result['code']} - {result['name']} (релевантность: {result['relevance']}%)")

if __name__ == "__main__":
    test_okved_search()
```

### Пример генерации SQL-запроса

```python
from src.agent.sql_generator import SQLGenerator
import asyncio

async def generate_sql():
    # Создаем генератор SQL для таблицы products
    generator = SQLGenerator("products")

    # Генерируем SQL-запрос
    query = "Найди все продукты с ценой больше 1000 рублей, отсортированные по убыванию цены"
    sql = await generator.generate_sql(query)

    print(f"Сгенерированный SQL-запрос:")
    print(sql)

if __name__ == "__main__":
    asyncio.run(generate_sql())
```

### Использование CLI-утилиты

Проект включает командную утилиту для тестирования генерации SQL-запросов:

```bash
# Базовое использование
python -m src.cli "Найди все товары с ценой больше 1000 рублей"

# Сохранение результата в файл
python -m src.cli "Найди товары в категории Электроника" --output result.json

# Подробный вывод
python -m src.cli "Найди пользователей с возрастом больше 30 лет" --verbose
```

Опции командной строки:

- `query`: Текст запроса для генерации SQL (обязательный параметр)
- `--output`, `-o`: Файл для сохранения результата в формате JSON
- `--verbose`, `-v`: Подробный вывод логов

Результат работы утилиты включает сгенерированный SQL-запрос, а также дополнительные метаданные в формате JSON.

## 📊 Тестирование

Для запуска тестов выполните:

```bash
python -m pytest
```

## 📝 Логирование

Система ведет журнал работы, отмечая инициализацию агентов и обработку запросов:

```
2025-06-23 21:34:59 | INFO | Initialized OllamaAgent with model silmarillion/ngs-mistral-7b-instruct-v0.2-klingon-q4_0:latest and 5 tools
2025-06-23 21:34:59 | INFO | Initialized SQLGenerator for table products
2025-06-23 21:34:59 | INFO | Processing query: Найди продукты категории Электроника...
```

Настройки логирования можно изменить в файле `.env`:

```
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

## ⚠️ Решение проблем

1. **Ошибка "invalid option provided" option=tfs_z**:

   - Это внутреннее предупреждение Ollama, которое можно игнорировать
   - При необходимости обновите пакет `langchain-ollama` до последней версии

2. **Ошибка "truncating input prompt"**:

   - Запрос слишком большой для контекстного окна модели
   - Уменьшите размер запроса или увеличьте параметр `OLLAMA_MAX_TOKENS`

3. **Модель не найдена в Ollama**:
   - Убедитесь, что модель загружена:
     ```bash
     ollama pull silmarillion/ngs-mistral-7b-instruct-v0.2-klingon-q4_0:latest
     ```

## 🧩 Расширение функциональности

Для добавления поддержки новой языковой модели необходимо:

1. Создать новый класс, наследующийся от `BaseAgent`:

```python
class NewModelAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None, tools: Optional[List[BaseTool]] = None):
        # Инициализация агента
        self.model_name = model or settings.newmodel.model
        default_tools = [get_okved_tool(), get_okato_tool(), ...]
        super().__init__(tools or default_tools)
        self.llm = self._create_llm()
        self._create_agent_executor(self.llm)

    def _create_llm(self) -> BaseLanguageModel:
        # Создание экземпляра модели
        return NewModelLLM(
            api_key=settings.newmodel.api_key,
            # Другие параметры
        )

    async def process_query(self, query: str) -> str:
        # Реализация обработки запроса
        # ...
```

2. Добавить новый тип в `AgentType` в модуле `settings.py`:

```python
class AgentType(str, Enum):
    OLLAMA = "ollama"
    GIGACHAT = "gigachat"
    NEW_MODEL = "new_model"
```

3. Обновить функцию `get_agent_class` в `agent.py`:

```python
def get_agent_class() -> Type[BaseAgent]:
    agent_type = settings.default_agent_type
    if agent_type == AgentType.GIGACHAT:
        return GigaChatAgent
    elif agent_type == AgentType.NEW_MODEL:
        return NewModelAgent
    else:
        return OllamaAgent
```

## 📄 Лицензия

[MIT](LICENSE)

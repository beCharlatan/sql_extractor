# SQL Extractor с интеграцией PostgreSQL и Kafka

## Описание проекта

SQL Extractor - это высокопроизводительное приложение, которое преобразует запросы на естественном языке в SQL-компоненты с использованием модели Gigachat. Приложение интегрировано с Kafka для обработки сообщений и PostgreSQL для хранения результатов генерации SQL.

## Основные возможности

- Генерация SQL-запросов из текста на естественном языке
- Поддержка сложных SQL-компонентов (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT)
- Интеграция с Kafka для асинхронной обработки запросов
- Сохранение результатов и ошибок в PostgreSQL
- Контейнеризация с использованием Docker
- Полное логирование и обработка ошибок
- Интеграция с Allure TestOps для отчетов о тестировании

## Технические требования

- Python 3.13+
- PostgreSQL
- Kafka
- Docker и Docker Compose (для контейнеризации)
- Учетные данные API Gigachat

## Установка и настройка

### Локальная установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/beCharlatan/sql_extractor.git
   cd sql_extractor
   ```

2. Создайте виртуальное окружение (рекомендуется):

   ```bash
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` с учетными данными Gigachat, настройками PostgreSQL и Kafka:

   ```
   # Настройки Gigachat
   GIGACHAT_API_KEY=ваш_ключ_api
   GIGACHAT_CREDENTIALS_PATH=/путь/к/credentials.json  # Если применимо

   # Настройки PostgreSQL
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres

   # Настройки Kafka
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   KAFKA_TOPIC=sql_generation_requests
   KAFKA_GROUP_ID=sql_generator_group
   ```

### Установка с использованием Docker

1. Убедитесь, что Docker и Docker Compose установлены на вашей системе

2. Запустите приложение с помощью Docker Compose:

   ```bash
   docker-compose up -d
   ```

   Это запустит все необходимые сервисы: PostgreSQL, Kafka, Zookeeper и само приложение.

## Архитектура приложения

### Основные компоненты

- **Kafka Consumer**: Обрабатывает входящие сообщения из Kafka, извлекает параметры запроса и отправляет их в генератор SQL
- **SQL Generator**: Генерирует SQL-компоненты на основе текстовых запросов с использованием Gigachat
- **PostgreSQL Client**: Сохраняет результаты генерации SQL и информацию об ошибках в базе данных
- **DB Schema Reference Tool**: Предоставляет информацию о схеме базы данных для более точной генерации SQL

### Поток данных

1. Сообщение с запросом поступает в топик Kafka
2. Kafka Consumer получает сообщение и извлекает параметры запроса
3. SQL Generator генерирует SQL-компоненты на основе запроса
4. Результат сохраняется в PostgreSQL
5. В случае ошибки, информация об ошибке также сохраняется в PostgreSQL

## Использование

### Запуск приложения

```bash
python main.py
```

Это запустит Kafka Consumer, который будет прослушивать указанный топик и обрабатывать входящие сообщения.

### Отправка запросов через Kafka Producer

Для отправки запросов в Kafka можно использовать встроенный Producer:

```python
from src.kafka.producer import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    topic='sql_generation_requests'
)

# Отправка запроса
producer.send_message({
    'filter': 'Найти продукты в категории электроника с ценой меньше 1000',
    'constraint': 'Отсортировать по рейтингу по убыванию и ограничить 10 результатами'
})
```

### Формат запроса

Запрос должен содержать следующие поля:

- `filter`: Текст фильтра на естественном языке
- `constraint`: Текст ограничения на естественном языке
- `message_id` (опционально): Уникальный идентификатор сообщения

### Формат ответа

Ответ содержит следующие SQL-компоненты:

- `where_clause`: Условие WHERE
- `group_by_clause`: Группировка GROUP BY
- `having_clause`: Условие для сгруппированных данных HAVING
- `order_by_clause`: Сортировка ORDER BY
- `limit_clause`: Ограничение количества результатов LIMIT
- `full_sql`: Полный SQL-запрос, объединяющий все компоненты

## Структура базы данных

Приложение создает таблицу `organization_filters` в PostgreSQL со следующей структурой:

```sql
CREATE TABLE organization_filters (
    id SERIAL PRIMARY KEY,
    message_id TEXT,
    filter_text TEXT NOT NULL,
    constraint_text TEXT NOT NULL,
    where_clause TEXT,
    group_by_clause TEXT,
    having_clause TEXT,
    order_by_clause TEXT,
    limit_clause TEXT,
    full_sql TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT
);
```

## Тестирование

### Запуск тестов

Для запуска тестов используйте команду:

```bash
python run_tests.py
```

Эта команда запустит все тесты и сгенерирует отчет Allure.

### Просмотр отчетов Allure

После запуска тестов вы можете просмотреть отчеты Allure с помощью команды:

```bash
allure serve allure-results
```

## Обработка ошибок

Приложение обрабатывает следующие типы ошибок:

- **ValidationError**: Ошибки валидации входных данных
- **GigachatAPIError**: Ошибки при взаимодействии с API Gigachat
- **InvalidSQLError**: Ошибки при генерации SQL
- **DatabaseError**: Ошибки при взаимодействии с базой данных
- **KafkaError**: Ошибки при взаимодействии с Kafka

Все ошибки логируются и сохраняются в базе данных PostgreSQL для дальнейшего анализа.

## Мониторинг и логирование

Приложение использует библиотеку `loguru` для логирования. Логи содержат информацию о всех этапах обработки сообщений, включая получение сообщения из Kafka, генерацию SQL и сохранение результатов в PostgreSQL.

## Дополнительная информация

### Переменные окружения

Полный список поддерживаемых переменных окружения:

```
# Gigachat
GIGACHAT_API_KEY - Ключ API Gigachat
GIGACHAT_CREDENTIALS_PATH - Путь к файлу учетных данных Gigachat

# PostgreSQL
POSTGRES_HOST - Хост PostgreSQL
POSTGRES_PORT - Порт PostgreSQL
POSTGRES_DB - Имя базы данных PostgreSQL
POSTGRES_USER - Пользователь PostgreSQL
POSTGRES_PASSWORD - Пароль PostgreSQL

# Kafka
KAFKA_BOOTSTRAP_SERVERS - Серверы Kafka
KAFKA_TOPIC - Топик Kafka для запросов
KAFKA_GROUP_ID - ID группы потребителей Kafka
KAFKA_AUTO_OFFSET_RESET - Стратегия сброса смещения (earliest/latest)
KAFKA_ENABLE_AUTO_COMMIT - Автоматическая фиксация смещения (true/false)
KAFKA_CONSUMER_TIMEOUT_MS - Таймаут потребителя в миллисекундах
```

## Лицензия

Проект распространяется под лицензией MIT. См. файл LICENSE для получения дополнительной информации.

## Интеграция с Allure TestOps

В проекте настроена интеграция с Allure TestOps для генерации подробных отчетов о тестировании:

1. Добавлена зависимость allure-pytest для интеграции с фреймворком тестирования
2. Настроен скрипт run_tests.py для запуска тестов с генерацией отчетов Allure
3. Добавлены хуки в conftest.py для сбора информации о тестах
4. Тесты дополнены декораторами Allure для улучшения отчетности
5. Настроен CI/CD процесс с использованием Jenkinsfile для автоматической отправки отчетов
6. Создан файл конфигурации allurectl.yaml для настройки интеграции

Для просмотра отчетов после запуска тестов используйте:

```bash
allure serve allure-results
```

```bash
docker-compose up -d db
```

Эта команда запустит контейнер PostgreSQL с необходимой схемой и примерами данных.

### Запуск тестов без Allure

```bash
python -m pytest
```

### Allure Reporting

Проект настроен для генерации отчетов о тестировании с использованием Allure. Для работы с отчетами Allure:

1. Установите Allure CLI (если еще не установлено):

   ```bash
   # На macOS
   brew install allure

   # На Linux
   curl -o allure-2.24.1.tgz -OLs https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.24.1/allure-commandline-2.24.1.tgz
   tar -zxvf allure-2.24.1.tgz
   export PATH=$PATH:`pwd`/allure-2.24.1/bin
   ```

2. Запустите тесты с генерацией отчетов Allure, используя скрипт `run_tests.py`:

   ```bash
   # Запуск всех тестов с генерацией отчетов Allure
   python run_tests.py --clean --report

   # Запуск конкретного теста с генерацией отчетов
   python run_tests.py --tests tests/test_sql_generator.py --report

   # Запуск тестов и открытие отчета в браузере
   python run_tests.py --clean --serve

   # Подготовка отчета для загрузки в Allure TestOps
   python run_tests.py --clean --testops
   ```

3. Для интеграции с Allure TestOps в CI/CD используйте Jenkinsfile и allurectl:

   ```bash
   # Локальная отправка отчетов в Allure TestOps (требуются переменные окружения)
   export ALLURE_TESTOPS_ENDPOINT=https://your-testops-instance.com
   export ALLURE_TESTOPS_TOKEN=your-token
   export ALLURE_TESTOPS_PROJECT_ID=your-project-id

   allurectl upload --launch-name "SQL Extractor Tests" allure-results
   ```

### Code formatting

```bash
black .
isort .
```

### Linting

```bash
ruff check .
```

### Docker Commands

- Start all services: `docker-compose up -d`
- Start only the database: `docker-compose up -d db`
- Start only the API: `docker-compose up -d api`
- View logs: `docker-compose logs -f`
- Stop all services: `docker-compose down`

## Тестирование приложения с использованием Kafka

### Публикация сообщений в Kafka при запущенном Docker

Когда ваше приложение запущено в Docker, вы можете отправлять сообщения в Kafka для тестирования следующими способами:

#### 1. Использование инструмента kafkacat/kcat

Утилита kafkacat (также известная как kcat) - это удобный инструмент командной строки для работы с Kafka:

```bash
# Установка kafkacat
# На macOS
brew install kcat

# На Ubuntu/Debian
apt-get install kafkacat

# Отправка сообщения в Kafka
echo '{"filter": "Найти продукты в категории электроника с ценой меньше 1000", "constraint": "Отсортировать по рейтингу по убыванию и ограничить 10 результатами"}' | \
kcat -b localhost:9092 -t sql_generation_requests -P
```

#### 2. Использование Python-скрипта

Создайте файл `send_kafka_message.py`:

```python
from kafka import KafkaProducer
import json

def send_test_message():
    # Конфигурация продюсера
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    # Пример сообщения
    message = {
        'filter': 'Найти продукты в категории электроника с ценой меньше 1000',
        'constraint': 'Отсортировать по рейтингу по убыванию и ограничить 10 результатами',
        'message_id': 'test-message-001'  # Опционально
    }

    # Отправка сообщения
    producer.send('sql_generation_requests', message)
    producer.flush()
    print(f"Сообщение успешно отправлено: {message}")

if __name__ == "__main__":
    send_test_message()
```

Запустите скрипт:

```bash
python send_kafka_message.py
```

#### 3. Использование Docker для подключения к Kafka-контейнеру

Если вы хотите отправить сообщение непосредственно из другого контейнера Docker:

```bash
# Запуск временного контейнера с kafkacat для отправки сообщения
docker run --rm -it --network=host edenhill/kcat:1.7.1 \
  -b localhost:9092 -t sql_generation_requests -P \
  -l <(echo '{"filter": "Найти продукты в категории электроника с ценой меньше 1000", "constraint": "Отсортировать по рейтингу по убыванию и ограничить 10 результатами"}')
```

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:29092 uv run python send_kafka_message.py --filter 'Найти все заказы за последний месяц' --constraint 'Отсортировать по дате'
```

#### 4. Проверка успешной обработки сообщения

После отправки сообщения вы можете проверить, что оно было успешно обработано:

```bash
# Проверка логов приложения
docker-compose logs -f api

# Проверка записи в базе данных PostgreSQL
docker-compose exec db psql -U postgres -d postgres -c "SELECT * FROM organization_filters ORDER BY created_at DESC LIMIT 5;"
```

> **Примечание**: Убедитесь, что в вашем файле docker-compose.yml корректно настроены порты Kafka (обычно 9092) и они проброшены на хост-машину.

## License

MIT

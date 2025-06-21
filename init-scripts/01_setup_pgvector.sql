-- Инициализация расширения pgvector для поддержки векторных операций
CREATE EXTENSION IF NOT EXISTS vector;

-- Создание схемы для хранения векторных данных (опционально)
CREATE SCHEMA IF NOT EXISTS vector_store;

-- Вывод информации об установленном расширении
\dx vector

-- Сообщение о завершении установки
\echo 'Расширение pgvector успешно установлено'

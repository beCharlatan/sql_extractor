"""
Скрипт для инициализации RAG-систем с загрузкой данных из CSV-файлов в векторные хранилища.

Этот скрипт следует запускать отдельно при необходимости первоначальной загрузки
или обновления данных в векторных хранилищах. Основное приложение будет использовать
только поисковые функции без повторной загрузки данных.
"""

import os
import argparse
from loguru import logger

from src.data.okato_rag import initialize_okato_rag
from src.data.okved_rag import initialize_okved_rag
from src.data.oktmo_rag import initialize_oktmo_rag


def initialize_all_rag_systems(okato_csv: str = None, okved_csv: str = None, oktmo_csv: str = None):
    """
    Инициализирует все RAG-системы с загрузкой данных в векторные хранилища.
    
    Args:
        okato_csv: Путь к CSV-файлу с кодами ОКАТО. Если None, используется путь по умолчанию.
        okved_csv: Путь к CSV-файлу с кодами ОКВЭД. Если None, используется путь по умолчанию.
        oktmo_csv: Путь к CSV-файлу с кодами ОКТМО. Если None, используется путь по умолчанию.
    """
    logger.info("Начало инициализации RAG-систем с загрузкой данных")
    
    # Инициализация ОКАТО RAG
    logger.info("Инициализация ОКАТО RAG...")
    okato_rag = initialize_okato_rag(csv_path=okato_csv)
    logger.info(f"ОКАТО RAG успешно инициализирована, загружено {len(okato_rag.df)} документов")
    
    # Инициализация ОКВЭД RAG
    logger.info("Инициализация ОКВЭД RAG...")
    okved_rag = initialize_okved_rag(csv_path=okved_csv)
    logger.info(f"ОКВЭД RAG успешно инициализирована")
    
    # Инициализация ОКТМО RAG
    logger.info("Инициализация ОКТМО RAG...")
    oktmo_rag = initialize_oktmo_rag(csv_path=oktmo_csv)
    logger.info(f"ОКТМО RAG успешно инициализирована, загружено {len(oktmo_rag.data)} документов")
    
    logger.info("Все RAG-системы успешно инициализированы")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Инициализация RAG-систем с загрузкой данных")
    parser.add_argument("--okato", help="Путь к CSV-файлу с кодами ОКАТО", default=None)
    parser.add_argument("--okved", help="Путь к CSV-файлу с кодами ОКВЭД", default=None)
    parser.add_argument("--oktmo", help="Путь к CSV-файлу с кодами ОКТМО", default=None)
    
    args = parser.parse_args()
    
    initialize_all_rag_systems(args.okato, args.okved, args.oktmo)

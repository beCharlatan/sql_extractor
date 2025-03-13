#!/usr/bin/env python
"""
Скрипт для запуска тестов с генерацией отчетов Allure.

Этот скрипт запускает тесты pytest с генерацией отчетов Allure
и предоставляет опции для выбора тестов и управления отчетами.
"""

import argparse
import os
import subprocess
import sys


def main():
    """
Запуск тестов с генерацией отчетов Allure.
    """
    parser = argparse.ArgumentParser(description="Запуск тестов с генерацией отчетов Allure")
    parser.add_argument(
        "--tests", 
        default="tests", 
        help="Путь к тестам или конкретный тест (например, tests/test_agent.py)"
    )
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Очистить предыдущие результаты тестов"
    )
    parser.add_argument(
        "--report", 
        action="store_true", 
        help="Сгенерировать HTML-отчет после запуска тестов"
    )
    parser.add_argument(
        "--serve", 
        action="store_true", 
        help="Запустить веб-сервер для просмотра отчета"
    )
    parser.add_argument(
        "--testops", 
        action="store_true", 
        help="Подготовить отчет для загрузки в Allure TestOps"
    )
    
    args = parser.parse_args()
    
    # Создаем директории для отчетов, если они не существуют
    os.makedirs("allure-results", exist_ok=True)
    os.makedirs("allure-report", exist_ok=True)
    
    # Очищаем предыдущие результаты, если указан флаг --clean
    if args.clean:
        print("Очистка предыдущих результатов тестов...")
        subprocess.run(["rm", "-rf", "allure-results/*"], shell=True, check=False)
        subprocess.run(["rm", "-rf", "allure-report/*"], shell=True, check=False)
    
    # Формируем команду для запуска тестов
    pytest_cmd = [
        "python", "-m", "pytest", 
        args.tests, 
        "--alluredir=allure-results"
    ]
    
    # Если нужно подготовить отчет для TestOps, добавляем соответствующие опции
    if args.testops:
        pytest_cmd.extend([
            "--allure-features=SQL Generator,API,Database Integration",
            "--allure-epics=SQL Generation,API Integration,Database",
            "--allure-link-pattern=issue:https://github.com/beCharlatan/sql_extractor/issues/{}",
            "--allure-link-pattern=tms:https://testops.example.com/testcase/{}"
        ])
    
    # Запускаем тесты
    print(f"Запуск тестов: {' '.join(pytest_cmd)}")
    result = subprocess.run(pytest_cmd, check=False)
    
    # Если тесты завершились с ошибкой, выводим сообщение
    if result.returncode != 0:
        print(f"Тесты завершились с ошибкой (код {result.returncode})")
    
    # Генерируем HTML-отчет, если указан флаг --report или --serve
    if args.report or args.serve:
        print("Генерация HTML-отчета Allure...")
        subprocess.run(["allure", "generate", "allure-results", "-o", "allure-report", "--clean"], check=False)
    
    # Запускаем веб-сервер для просмотра отчета, если указан флаг --serve
    if args.serve:
        print("Запуск веб-сервера для просмотра отчета...")
        subprocess.run(["allure", "open", "allure-report"], check=False)
    
    # Если нужно подготовить отчет для TestOps, создаем ZIP-архив
    if args.testops:
        print("Подготовка отчета для загрузки в Allure TestOps...")
        subprocess.run(["zip", "-r", "allure-results.zip", "allure-results"], check=False)
        print("Отчет готов для загрузки в Allure TestOps: allure-results.zip")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

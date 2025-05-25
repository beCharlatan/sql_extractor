from datetime import datetime, timedelta
import asyncio
from functools import wraps
from typing import Dict, Optional, Callable, Any


class DBResponseCache:
    """Кеш с поддержкой составных ключей и автоматической инвалидацией"""
    
    def __init__(self):
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._midnight_task: Optional[asyncio.Task] = None

    def __del__(self):
        if self._midnight_task:
            self._midnight_task.cancel()

    async def _start_midnight_scheduler(self):
        """Фоновая задача для очистки кеша в полночь"""
        while True:
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            await asyncio.sleep((next_midnight - now).total_seconds())
            self._cache.clear()

    def _ensure_scheduler_started(self):
        """Запуск планировщика при первом обращении"""
        if not self._midnight_task or self._midnight_task.done():
            self._midnight_task = asyncio.create_task(self._start_midnight_scheduler())

    def cached(self, prefix: str):
        """Фабрика декораторов с параметром префикса"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> str:
                self._ensure_scheduler_started()
                
                # Извлекаем table_name из аргументов
                table_name = kwargs.get("table_name") or args[1]
                cache_key = f"{prefix}_{table_name}"

                # Проверяем кеш
                if entry := self._cache.get(cache_key):
                    value, expiration = entry
                    if datetime.now() < expiration:
                        return value

                # Используем блокировку для текущего ключа
                lock = self._locks.setdefault(cache_key, asyncio.Lock())
                async with lock:
                    # Двойная проверка после получения блокировки
                    if entry := self._cache.get(cache_key):
                        return entry[0]

                    # Вызываем оригинальную функцию
                    result = await func(*args, **kwargs)
                    
                    # Рассчитываем время экспирации
                    expires_at = datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ) + timedelta(days=1)
                    
                    # Обновляем кеш
                    self._cache[cache_key] = (result, expires_at)
                    return result

            return wrapper
        return decorator


# Пример использования
cache = DBResponseCache()
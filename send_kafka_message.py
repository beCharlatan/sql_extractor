#!/usr/bin/env python
"""Командная строковая утилита для отправки запросов генерации SQL в Kafka."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from src.kafka.producer import send_sql_generation_request
from src.utils.logging import setup_logging


async def main():
    parser = argparse.ArgumentParser(description="Send SQL generation requests to Kafka")
    parser.add_argument(
        "--filter", "-f",
        required=True,
        help="Filter text for SQL generation",
    )
    parser.add_argument(
        "--constraint", "-c",
        required=True,
        help="Constraint text for SQL generation",
    )
    parser.add_argument(
        "--request-hash", "-r",
        help="Optional request hash (UUID will be generated if not provided)",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        request_hash = await send_sql_generation_request(
            filter_text=args.filter,
            constraint_text=args.constraint,
            request_hash=args.request_hash,
        )
        
        logger.info(f"Successfully sent message with request_hash {request_hash}")
        print(f"Message sent with request_hash: {request_hash}")
        return 0
    except Exception as e:
        logger.exception(f"Error sending message: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

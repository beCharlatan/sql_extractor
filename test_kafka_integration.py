#!/usr/bin/env python

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from src.config.settings import settings
from src.kafka.producer import send_sql_generation_request
from src.utils.logging import setup_logging


async def test_kafka_producer():
    logger.info("Testing Kafka producer...")
    
    try:
        request_hash = await send_sql_generation_request(
            filter_text="products with price greater than 100",
            constraint_text="sort by price in descending order",
        )
        
        logger.info(f"Successfully sent message with request_hash {request_hash}")
        return True
    except Exception as e:
        logger.exception(f"Error sending message: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test Kafka integration")
    parser.add_argument(
        "--test", "-t",
        choices=["producer", "all"],
        default="all",
        help="Test to run: producer or all",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    logger.info(f"Starting Kafka integration test: {args.test}")
    logger.info(f"Kafka settings: bootstrap_servers={settings.kafka.bootstrap_servers}, topic={settings.kafka.topic}")
    
    success = True
    
    if args.test in ["producer", "all"]:
        producer_success = await test_kafka_producer()
        if not producer_success:
            success = False
    
    if success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

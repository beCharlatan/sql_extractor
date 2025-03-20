import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from src.kafka.main import main as kafka_main
from src.utils.logging import setup_logging


def main():
    setup_logging()
    
    logger.info("Starting Kafka consumer application")
    
    asyncio.run(kafka_main())


if __name__ == "__main__":
    main()

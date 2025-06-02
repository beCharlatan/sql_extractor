import asyncio
import sys
from pathlib import Path
import uvicorn
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.kafka.main import main as kafka_main
from src.utils.logging import setup_logging
from src.api.main import app


async def run_api():
    """Run FastAPI server"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    setup_logging()
    logger.info("Starting application")
    
    # Run Kafka consumer and API server concurrently
    await asyncio.gather(
        kafka_main(),
        run_api()
    )


if __name__ == "__main__":
    asyncio.run(main())

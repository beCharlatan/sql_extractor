import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.api.main import app as api_app
from src.config.settings import settings
from src.utils.logging import setup_logging


def main():
    """Main entry point for the application."""
    # Set up logging
    setup_logging()
    
    # Run the API server
    import uvicorn
    uvicorn.run(
        api_app,
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.logging.level.lower(),
    )


if __name__ == "__main__":
    main()

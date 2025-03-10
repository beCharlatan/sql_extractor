"""Main entry point for the API server."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.routes import client_router, health_router
from src.config.settings import settings
from src.utils.errors import APIError
from src.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup events
    logger.info("Starting API server...")
    yield
    # Shutdown events
    logger.info("Shutting down API server...")


# Create the FastAPI application
app = FastAPI(
    title="SQL Generator API",
    description="API for generating SQL from natural language and extracting structured parameters using Gigachat",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "client",
            "description": "Operations for generating SQL and extracting parameters",
        },
        {
            "name": "health",
            "description": "Health check endpoints",
        },
    ],
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "deepLinking": True,
        "displayRequestDuration": True,
        "syntaxHighlight.theme": "monokai",
    },
    contact={
        "name": "SQL Generator Team",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log request information and timing."""
    start_time = time.time()
    
    # Generate a unique request ID
    request_id = f"{time.time():.6f}"
    logger.info(f"Request started: {request.method} {request.url.path} (ID: {request_id})")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.2f}ms (ID: {request_id})"
        )
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"- Error: {str(e)} - Time: {process_time:.2f}ms (ID: {request_id})"
        )
        raise


# Exception handler for API errors
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle API errors and return appropriate responses.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        JSONResponse with appropriate status code and error details.
    """
    handle_exception(exc)  # Log the exception
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "details": exc.details,
        },
    )


# Include routers
app.include_router(client_router)
app.include_router(health_router)


# Add a root endpoint that redirects to the docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to the API documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn

    # Set up logging
    setup_logging()

    # Run the server
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.logging.level.lower(),
    )

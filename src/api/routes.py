"""API routes for the AI agent application."""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from src.agent.agent import GigachatAgent
from src.agent.sql_generator import SQLGenerator
from src.api.models import GenerateSQLRequest, GenerateSQLResponse, SQLComponents
from src.utils.errors import (
    APIError,
    DatabaseError,
    GigachatAPIError,
    InvalidSQLError,
    SQLGenerationError,
    ValidationError,
    handle_exception,
)

# Create the client router
client_router = APIRouter(prefix="/client", tags=["client"])


# Обработчик исключений перенесен в main.py, так как APIRouter не поддерживает exception_handler


# Dependency to get the Gigachat agent
def get_gigachat_agent():
    """Dependency to get a Gigachat agent instance."""
    try:
        return GigachatAgent()
    except Exception as e:
        handle_exception(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize Gigachat agent: {str(e)}",
        )


# Dependency to get the SQL generator
def get_sql_generator(agent: GigachatAgent = Depends(get_gigachat_agent)):
    """Dependency to get a SQL generator instance."""
    from src.db.db_schema_tool import DBSchemaReferenceTool
    db_schema_tool = DBSchemaReferenceTool()
    return SQLGenerator(agent=agent, db_schema_tool=db_schema_tool)


@client_router.post(
    "/generate-sql",
    response_model=GenerateSQLResponse,
    summary="Generate SQL from natural language",
    description="""
    Generate SQL query components from natural language inputs.
    
    This endpoint takes a filter text and constraint text as input and returns
    SQL components (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT clauses) that can be used to construct a complete SQL query.
    
    The generator now supports advanced SQL features including:
    - GROUP BY for data aggregation and grouping
    - HAVING for filtering grouped results
    - Statistical functions like AVG, COUNT, SUM, MIN, MAX
    - Percentile calculations (e.g., finding values above the median)
    """,
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "sql_components": {
                            "where_clause": "category = 'electronics' AND price < 1000",
                            "group_by_clause": "category",
                            "having_clause": "AVG(price) > 500",
                            "order_by_clause": "rating DESC",
                            "limit_clause": "10",
                            "full_sql": "WHERE category = 'electronics' AND price < 1000\nGROUP BY category\nHAVING AVG(price) > 500\nORDER BY rating DESC\nLIMIT 10"
                        },
                        "parameters": {
                            "category": "electronics",
                            "price_max": 1000,
                            "sort_by": "rating",
                            "sort_order": "desc",
                            "limit": 10
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid input parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Filter text cannot be empty or whitespace only",
                        "details": {
                            "field": "filter"
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation Error - Input validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "filter"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Error processing request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error processing request: Internal server error",
                        "details": {
                            "original_error": "Failed to process request"
                        }
                    }
                }
            }
        },
        502: {
            "description": "Bad Gateway - Error with Gigachat API",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Gigachat API error: Failed to connect to API",
                        "details": {
                            "original_error": "Connection timeout"
                        }
                    }
                }
            }
        }
    }
)
async def generate_sql(
    request: GenerateSQLRequest,
    sql_generator: SQLGenerator = Depends(get_sql_generator),
):
    try:
        logger.info("Generating SQL components and structured parameters")
        logger.debug(f"Filter: {request.filter}")
        logger.debug(f"Constraint: {request.constraint}")
        
        generator_result = sql_generator.generate_sql_components(
            filter_text=request.filter,
            constraint_text=request.constraint,
        )
        
        # Create the response with SQL components only
        result = GenerateSQLResponse(
            sql_components=SQLComponents(**generator_result["sql_components"]),
        )
        
        logger.info("Successfully generated SQL components")
        logger.debug(f"SQL components: {generator_result['sql_components']}")

        return result

    except (ValidationError, DatabaseError, InvalidSQLError) as e:
        # Эти ошибки связаны с валидацией входных данных или доступом к БД
        handle_exception(e)
        raise e.to_http_exception()
    except GigachatAPIError as e:
        # Ошибки API Gigachat
        handle_exception(e)
        raise e.to_http_exception()
    except SQLGenerationError as e:
        # Ошибки генерации SQL
        handle_exception(e)
        raise e.to_http_exception()
    except APIError as e:
        # Другие API ошибки
        handle_exception(e)
        raise e.to_http_exception()
    except Exception as e:
        # Неожиданные ошибки
        handle_exception(e)
        logger.exception(f"Unexpected error in generate_sql: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}",
        )


# Create the health check router
health_router = APIRouter(tags=["health"])


@health_router.get(
    "/health",
    summary="Health check",
    description="""
    Check if the API is healthy and running properly.
    
    This endpoint returns the current status of the service and can be used for:
    - Monitoring and alerting
    - Load balancer health checks
    - Deployment verification
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "sql-generator-api",
                        "version": "1.0.0",
                        "timestamp": "2025-03-07T20:13:07.123456"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "service": "sql-generator-api",
                        "error": "Database connection failed"
                    }
                }
            }
        }
    }
)
async def health_check():
    """Health check endpoint.

    Returns:
        Dict: Health status information.
    """
    from datetime import datetime
    
    # В реальном приложении здесь можно добавить проверки подключения к базе данных,
    # доступности внешних сервисов и т.д.
    
    return {
        "status": "ok", 
        "service": "extract-parameter-agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

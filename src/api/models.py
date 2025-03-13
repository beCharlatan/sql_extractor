"""API data models for request and response validation."""

from pydantic import BaseModel, Field, field_validator


class GenerateSQLRequest(BaseModel):
    """Request model for SQL generation endpoint."""

    filter: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="Filter string to process",
        examples=["Find products in the electronics category with price less than 1000"],
    )
    constraint: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="Constraint string to process",
        examples=["Sort by highest rating and limit to 10 results"],
    )
    
    @field_validator('filter')
    @classmethod
    def filter_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Filter text cannot be empty or whitespace only')
        return v
    
    @field_validator('constraint')
    @classmethod
    def constraint_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Constraint text cannot be empty or whitespace only')
        return v


class SQLComponents(BaseModel):
    """SQL query components."""

    where_clause: str = Field(
        default="",
        description="WHERE clause (without the 'WHERE' keyword)",
    )
    group_by_clause: str = Field(
        default="",
        description="GROUP BY clause (without the 'GROUP BY' keyword)",
    )
    having_clause: str = Field(
        default="",
        description="HAVING clause (without the 'HAVING' keyword)",
    )
    order_by_clause: str = Field(
        default="",
        description="ORDER BY clause (without the 'ORDER BY' keyword)",
    )
    limit_clause: str = Field(
        default="",
        description="LIMIT clause (without the 'LIMIT' keyword)",
    )
    full_sql: str = Field(
        default="",
        description="The combined SQL components",
    )


class GenerateSQLResponse(BaseModel):
    """Response model for SQL generation endpoint."""

    sql_components: SQLComponents = Field(
        ...,
        description="Generated SQL query components",
    )

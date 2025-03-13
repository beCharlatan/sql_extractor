# AI Agent Application with Gigachat

A production-ready AI agent application built with Python, using Gigachat as the underlying language model and PostgreSQL for database operations.

## Features

- Robust API for interacting with Gigachat
- Parameter extraction capabilities
- SQL query generation from natural language inputs with support for advanced features (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT)
- PostgreSQL database integration for schema reference
- Table DDL-based context for accurate SQL generation
- Comprehensive logging and error handling
- Containerized deployment with Docker
- Extensive test coverage

## Requirements

- Python 3.13+
- PostgreSQL database
- Docker and Docker Compose (for containerized deployment)
- Gigachat API credentials

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/extract-parameter-agent.git
   cd extract-parameter-agent
   ```

2. Set up a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Create a `.env` file with your Gigachat API credentials and PostgreSQL connection settings:

   ```
   GIGACHAT_API_KEY=your_api_key_here
   GIGACHAT_CREDENTIALS_PATH=/path/to/credentials.json  # If applicable

   # PostgreSQL connection settings
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   ```

## Usage

### Command Line Interface (CLI)

The tool provides a command-line interface for generating SQL from natural language inputs:

```bash
extract-parameters --filter "Find products in the electronics category with price less than 1000" \
  --constraint "Sort by highest rating and limit to 10 results" \
  --table-ddl "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, category VARCHAR(50), price DECIMAL(10, 2), rating DECIMAL(3, 2), stock INT DEFAULT 0);"
```

Required arguments:

- `--filter` or `-f`: Filter text to process
- `--constraint` or `-c`: Constraint text to process
- `--table-ddl` or `-t`: Path to a file containing the table DDL or the DDL string itself

Optional arguments:

- `--output` or `-o`: Output format (`json` or `pretty`, default: `pretty`)
- `--verbose` or `-v`: Enable verbose logging

### Starting the API server

#### Running locally

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`.

#### Running with Docker

```bash
docker-compose up -d
```

This will start both the PostgreSQL database and the API service. The API will be available at `http://localhost:8000`.

### Using the agent programmatically

```python
from src.agent.sql_generator import SQLGenerator
from src.db.db_schema_tool import DBSchemaReferenceTool

# Initialize with a specific table name
db_tool = DBSchemaReferenceTool()
generator = SQLGenerator(db_schema_tool=db_tool)

# Generate SQL components
result = generator.generate_sql_components(
    filter_text="Find products in the electronics category with price less than 1000",
    constraint_text="Sort by highest rating and limit to 10 results"
)

print("SQL Components:", result["sql_components"])
```

## API Endpoints

- `POST /client/generate-sql` - Generate SQL query components and extract from filter and constraint inputs
- `GET /health` - Check API health status

### Using the SQL Generation Feature

The API generates SQL query components (WHERE, GROUP BY, HAVING, ORDER BY, and LIMIT clauses) and based on natural language filter and constraint inputs. It uses the PostgreSQL database schema as context to interpret these inputs as table attributes.

The SQL generator supports advanced features including:

- Grouping data with GROUP BY
- Filtering grouped data with HAVING
- Statistical calculations (AVG, COUNT, SUM, MIN, MAX)
- Percentile calculations (e.g., finding values above the median)
- Complex aggregation queries

#### Example Request

```json
{
  "filter": "Find products in the electronics category with price less than 1000",
  "constraint": "Sort by highest rating and limit to 10 results"
}
```

#### Example Response

```json
{
  "sql_components": {
    "where_clause": "category = 'electronics' AND price < 1000",
    "group_by_clause": "category",
    "having_clause": "AVG(price) > 500",
    "order_by_clause": "rating DESC",
    "limit_clause": "10",
    "full_sql": "WHERE category = 'electronics' AND price < 1000
GROUP BY category
HAVING AVG(price) > 500
ORDER BY rating DESC
LIMIT 10"
  }
}
```

## Command-Line Interface

The application includes a command-line interface for generating SQL query components from filter and constraint text.

### Basic Parameter Extraction

```bash
python -m src.cli --filter "Find products in the electronics category" --constraint "Price should be less than 1000"
```

### SQL Generation

```bash
python -m src.cli --filter "Find products in the electronics category" --constraint "Price should be less than 1000, sort by highest rating, and limit to 10 results" --generate-sql --table-ddl "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, category VARCHAR(50), price DECIMAL(10, 2), rating DECIMAL(3, 2), stock INT DEFAULT 0);"
```

You can also provide a file containing the table DDL:

```bash
python -m src.cli --filter "Find products in the electronics category" --constraint "Price should be less than 1000" --generate-sql --table-ddl path/to/table_ddl.sql
```

### Output Formats

The CLI supports both pretty-printed and JSON output formats:

```bash
python -m src.cli --filter "..." --constraint "..." --output json
```

For more options, run `python -m src.cli --help`.

## Development

### Setting up the database

The application uses PostgreSQL for database operations. You can set up the database using Docker:

```bash
docker-compose up -d db
```

This will start a PostgreSQL container with the necessary schema and sample data.

### Running tests

```bash
python -m pytest
```

### Code formatting

```bash
black .
isort .
```

### Linting

```bash
ruff check .
```

### Docker Commands

- Start all services: `docker-compose up -d`
- Start only the database: `docker-compose up -d db`
- Start only the API: `docker-compose up -d api`
- View logs: `docker-compose logs -f`
- Stop all services: `docker-compose down`

## License

MIT

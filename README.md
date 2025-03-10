# AI Agent Application with Gigachat

A production-ready AI agent application built with Python, using Gigachat as the underlying language model.

## Features

- Robust API for interacting with Gigachat
- Parameter extraction capabilities
- SQL query generation from natural language inputs
- Table DDL-based context for accurate SQL generation
- Comprehensive logging and error handling
- Containerized deployment support
- Extensive test coverage

## Requirements

- Python 3.13+
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

4. Create a `.env` file with your Gigachat API credentials:
   ```
   GIGACHAT_API_KEY=your_api_key_here
   GIGACHAT_CREDENTIALS_PATH=/path/to/credentials.json  # If applicable
   ```

## Usage

### Command Line Interface (CLI)

The tool provides a command-line interface for generating SQL and extracting parameters from natural language inputs:

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

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`.

### Using the agent programmatically

```python
from src.agent.sql_generator import SQLGenerator

generator = SQLGenerator()
result = generator.generate_sql_components(
    filter_text="Find products in the electronics category with price less than 1000",
    constraint_text="Sort by highest rating and limit to 10 results",
    table_ddl="CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, category VARCHAR(50), price DECIMAL(10, 2), rating DECIMAL(3, 2), stock INT DEFAULT 0);",
)

print("Parameters:", result["parameters"])
print("SQL Components:", result["sql_components"])
```

## API Endpoints

- `POST /client/generate-sql` - Generate SQL query components and extract structured parameters from filter and constraint inputs
- `GET /health` - Check API health status

### Using the SQL Generation Feature

The API generates SQL query components (WHERE, ORDER BY, and LIMIT clauses) and extracts structured parameters based on natural language filter and constraint inputs. It uses the provided table DDL as context to interpret these inputs as table attributes.

#### Example Request

```json
{
  "filter": "Find products in the electronics category with price less than 1000",
  "constraint": "Sort by highest rating and limit to 10 results",
  "table_ddl": "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, category VARCHAR(50), price DECIMAL(10, 2), rating DECIMAL(3, 2), stock INT DEFAULT 0);"
}
```

#### Example Response

```json
{
  "parameters": {
    "category": "electronics",
    "price_max": 1000,
    "sort_by": "rating",
    "sort_order": "DESC",
    "limit": 10
  },
  "sql_components": {
    "where_clause": "category = 'electronics' AND price < 1000",
    "order_by_clause": "rating DESC",
    "limit_clause": "10",
    "full_sql": "WHERE category = 'electronics' AND price < 1000
ORDER BY rating DESC
LIMIT 10"
  }
}
```

## Command-Line Interface

The application includes a command-line interface for extracting parameters from filter and constraint text, and optionally generating SQL query components.

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

## License

MIT

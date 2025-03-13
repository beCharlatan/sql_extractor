#!/usr/bin/env python
"""
Script to generate Swagger/OpenAPI JSON file from FastAPI application.
"""

import json
import os
from pathlib import Path

# Import the FastAPI app
from src.api.main import app
from src.utils.logging import setup_logging


def generate_swagger_json(output_path="swagger.json"):
    """
    Generate Swagger/OpenAPI JSON file from FastAPI application.
    
    Args:
        output_path: Path to save the Swagger JSON file
    """
    # Setup logging
    setup_logging()
    
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"Swagger JSON file generated at: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    # Default output path
    default_output = Path("docs/swagger.json")
    
    # Generate the Swagger JSON
    generate_swagger_json(str(default_output))
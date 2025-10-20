#!/usr/bin/env python3
"""
Export OpenAPI schema from md2cf REST API.

This script exports the OpenAPI schema without starting a server.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from md2cf.rest_api import app


def export_openapi_schema(output_file: str = "openapi.json") -> None:
    """
    Export OpenAPI schema to a JSON file.

    Args:
        output_file: Path to the output file
    """
    # Get OpenAPI schema
    schema = app.openapi()

    # Write to file
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI schema exported to: {output_path}")
    print(f"📊 Schema version: {schema['info']['version']}")
    print(f"📝 Endpoints: {len(schema['paths'])}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
    export_openapi_schema(output)

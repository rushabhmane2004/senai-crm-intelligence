"""
Export FastAPI OpenAPI schema to docs/openapi.json.

Usage (from project root):
    python scripts/export_openapi.py

Output:
    docs/openapi.json
"""
import os
import sys
import json

# Resolve absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")

# Add backend to sys.path and chdir so relative imports work
sys.path.insert(0, backend_path)
os.chdir(backend_path)

try:
    from app.main import app
except ImportError as e:
    print(f"[FAIL] Failed to import FastAPI app: {e}")
    sys.exit(1)

# Generate OpenAPI schema (no server startup required)
openapi_schema = app.openapi()

# Ensure output directory exists
docs_dir = os.path.join(workspace_root, "docs")
os.makedirs(docs_dir, exist_ok=True)
output_path = os.path.join(docs_dir, "openapi.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2)

# Summary output
paths = openapi_schema.get("paths", {})
components = openapi_schema.get("components", {}).get("schemas", {})

print(f"[SUCCESS] OpenAPI schema exported to: {output_path}")
print(f"  Paths exported   : {len(paths)}")
print(f"  Schema components: {len(components)}")
print(f"  API title        : {openapi_schema.get('info', {}).get('title', 'N/A')}")
print(f"  API version      : {openapi_schema.get('info', {}).get('version', 'N/A')}")

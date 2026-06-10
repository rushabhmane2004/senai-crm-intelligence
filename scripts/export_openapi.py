import os
import sys
import json

# Resolve absolute paths to backend folder to avoid import errors
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")
sys.path.insert(0, backend_path)

try:
    from app.main import app
except ImportError as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

# Retrieve Swagger schema from FastAPI instance
openapi_schema = app.openapi()

# Enforce output directory existence
docs_dir = os.path.join(workspace_root, "docs")
os.makedirs(docs_dir, exist_ok=True)
output_path = os.path.join(docs_dir, "openapi.json")

with open(output_path, "w") as f:
    json.dump(openapi_schema, f, indent=2)

print(f"Successfully exported OpenAPI schema to {output_path}")

# OpenAPI / Swagger Export Instructions

The Agentic CRM Intelligence Platform provides self-documenting interactive API endpoints based on the OpenAPI standard.

## 1. Live Interactive API Docs (Swagger UI)

When the backend FastAPI application is running locally on port `8000`, the interactive Swagger UI and alternative Redoc documentation are accessible at:
* **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

You can use the live Swagger documentation to test incoming payloads, run queries, and trigger test emails.

## 2. Exporting the Static OpenAPI Schema

To generate or update the static `openapi.json` file inside the `docs/` folder:

1. **Activate the backend virtual environment** (if not already active):
   * **Windows**:
     ```bash
     backend\venv\Scripts\activate
     ```
   * **macOS/Linux**:
     ```bash
     source backend/venv/bin/activate
     ```

2. **Execute the export script** from the root workspace directory:
   ```bash
   python scripts/export_openapi.py
   ```

3. **Verify results**:
   * The script will output the schema to `docs/openapi.json`.
   * The file is standard JSON containing all router schema representations, endpoints, and error envelopes.

"""
Test Script: Documentation Exports Validation
===============================================
Validates:
  1. docs/database_schema.md exists and contains a Mermaid ER diagram block.
  2. docs/api_reference.md exists and mentions all major endpoint groups.
  3. Running scripts/export_openapi.py succeeds.
  4. docs/openapi.json exists and is valid JSON.
  5. OpenAPI JSON contains the required endpoint paths.
"""
import os
import sys
import json
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
docs_dir = os.path.join(workspace_root, "docs")

REQUIRED_PATHS = [
    "/api/ingest",
    "/api/status/{message_id}",
    "/rag/search",
    "/analytics/sentiment-trend",
    "/agent/dry-run/{message_id}",
    "/intelligence/reputation",
]

API_REFERENCE_GROUPS = [
    "/api/ingest",
    "/api/status",
    "/api/actions",
    "/analytics/sentiment-trend",
    "/analytics/category-breakdown",
    "/analytics/risk-summary",
    "/rag/search",
    "/agent/dry-run",
    "/intelligence/reputation",
]

all_passed = True


def check(condition: bool, name: str, detail: str = ""):
    global all_passed
    if condition:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}" + (f": {detail}" if detail else ""))
        all_passed = False


def main():
    print("==================================================")
    print("Starting Documentation Exports Validation")
    print("==================================================")

    # ──────────────────────────────────────────────────────────
    # Test 1: docs/database_schema.md
    # ──────────────────────────────────────────────────────────
    print("\n[Test 1] docs/database_schema.md")
    schema_path = os.path.join(docs_dir, "database_schema.md")
    check(os.path.exists(schema_path), "File exists")

    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_content = f.read()
        check("```mermaid" in schema_content, "Contains Mermaid ER diagram block")
        check("erDiagram" in schema_content, "ER diagram uses erDiagram keyword")
        check("WEB_INTELLIGENCE_CACHE" in schema_content or "web_intelligence_cache" in schema_content,
              "Documents web_intelligence_cache table")
        check("EMAILS" in schema_content or "emails" in schema_content, "Documents emails table")
        check("ACTIONS" in schema_content or "actions" in schema_content, "Documents actions table")
        check("AUDIT_LOG" in schema_content or "audit_log" in schema_content, "Documents audit_log table")

    # ──────────────────────────────────────────────────────────
    # Test 2: docs/api_reference.md
    # ──────────────────────────────────────────────────────────
    print("\n[Test 2] docs/api_reference.md")
    api_ref_path = os.path.join(docs_dir, "api_reference.md")
    check(os.path.exists(api_ref_path), "File exists")

    if os.path.exists(api_ref_path):
        with open(api_ref_path, "r", encoding="utf-8") as f:
            api_content = f.read()
        for group in API_REFERENCE_GROUPS:
            check(group in api_content, f"Mentions {group}")

    # ──────────────────────────────────────────────────────────
    # Test 3: Run export_openapi.py
    # ──────────────────────────────────────────────────────────
    print("\n[Test 3] Running scripts/export_openapi.py")
    export_script = os.path.join(workspace_root, "scripts", "export_openapi.py")
    check(os.path.exists(export_script), "export_openapi.py exists")

    if os.path.exists(export_script):
        result = subprocess.run(
            [sys.executable, export_script],
            capture_output=True,
            text=True,
            cwd=workspace_root,
        )
        check(result.returncode == 0, "export_openapi.py exits with code 0",
              result.stderr[:300] if result.returncode != 0 else "")
        if result.stdout:
            print(f"    Output: {result.stdout.strip()}")

    # ──────────────────────────────────────────────────────────
    # Test 4: docs/openapi.json validity
    # ──────────────────────────────────────────────────────────
    print("\n[Test 4] docs/openapi.json")
    openapi_path = os.path.join(docs_dir, "openapi.json")
    check(os.path.exists(openapi_path), "File exists")

    if os.path.exists(openapi_path):
        try:
            with open(openapi_path, "r", encoding="utf-8") as f:
                openapi_data = json.load(f)
            check(True, "Valid JSON")
        except json.JSONDecodeError as e:
            check(False, "Valid JSON", str(e))
            openapi_data = {}

        if openapi_data:
            paths = openapi_data.get("paths", {})
            check(len(paths) > 0, f"Has at least 1 path (found {len(paths)})")

            # ──────────────────────────────────────────────────
            # Test 5: Required paths present
            # ──────────────────────────────────────────────────
            print("\n[Test 5] Required endpoint paths in openapi.json")
            for required_path in REQUIRED_PATHS:
                check(required_path in paths, f"Path present: {required_path}",
                      f"Available: {list(paths.keys())[:10]}")

    # ──────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────
    print("\n==================================================")
    print("Documentation Exports Validation Summary")
    print("==================================================")
    if all_passed:
        print("[SUCCESS] All documentation export checks passed!")
        sys.exit(0)
    else:
        print("[FAIL] One or more documentation checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

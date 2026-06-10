"""
Demo Database Reset Script
===========================
Clears all runtime/demo data from the database while preserving:
  - knowledge_chunks  (RAG seeding registry)
  - web_intelligence_cache  (reputation cache)
  - ChromaDB vector store files
  - KB markdown files

Tables cleared (in FK-safe order):
  1. actions
  2. audit_log
  3. emails
  4. threads
  5. contacts

Usage (from project root):
    python scripts/reset_demo_data.py
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")

sys.path.insert(0, backend_path)
os.chdir(backend_path)

try:
    from app.database import SessionLocal
    from app.models.action import Action
    from app.models.audit_log import AuditLog
    from app.models.email import Email
    from app.models.thread import Thread
    from app.models.contact import Contact
except ImportError as e:
    print(f"[FAIL] Failed to import app models: {e}")
    sys.exit(1)

RESET_ORDER = [
    ("actions",   Action),
    ("audit_log", AuditLog),
    ("emails",    Email),
    ("threads",   Thread),
    ("contacts",  Contact),
]

def main():
    print("==================================================")
    print("Demo Database Reset")
    print("Preserves: knowledge_chunks, web_intelligence_cache")
    print("==================================================")

    db = SessionLocal()
    try:
        total_deleted = 0
        for table_name, Model in RESET_ORDER:
            count = db.query(Model).count()
            db.query(Model).delete(synchronize_session=False)
            db.commit()
            print(f"  Cleared [{table_name}]: {count} records deleted")
            total_deleted += count

        print(f"\n[SUCCESS] Demo tables cleared. Total records removed: {total_deleted}")
        sys.exit(0)

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Reset failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

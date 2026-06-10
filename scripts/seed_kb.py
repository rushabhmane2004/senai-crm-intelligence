import sys
from pathlib import Path

# Add backend directory to path to resolve imports correctly
project_root = Path(__file__).resolve().parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from app.database import engine, Base, SessionLocal
# Import models to register them on Base.metadata
from app.models import contact, thread, email, action, audit_log, knowledge_chunk
from app.services.rag_service import rag_service

def main():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    print("Seeding Knowledge Base from /kb...")
    db = SessionLocal()
    try:
        res = rag_service.seed_knowledge_base(db)
        print(f"Chunks created: {res.get('chunks_created', 0)}")
        print(f"Chunks skipped: {res.get('chunks_skipped', 0)}")
        print(f"Collection count: {res.get('collection_count', 0)}")
    except Exception as e:
        print(f"Error seeding KB: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

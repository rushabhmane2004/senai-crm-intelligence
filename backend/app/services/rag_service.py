import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session

def semantic_chunk_text(text: str, max_words: int = 400, overlap_words: int = 80) -> List[str]:
    """
    Chunks text by grouping words to target 300-500 tokens (~400 words) with a specified overlap.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += (max_words - overlap_words)
    return chunks

def generate_chunk_hash(source_doc: str, chunk_text: str) -> str:
    """
    Generates a stable SHA-256 hash for deduplication.
    """
    content = f"{source_doc}:{chunk_text}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

class RAGService:
    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self._model = None

    def _init_lazy(self):
        """
        Lazily initializes ChromaDB and the sentence-transformers model to optimize startup time.
        """
        if self._chroma_client is not None:
            return

        import chromadb
        from sentence_transformers import SentenceTransformer

        # Resolve persistent Chroma store directory relative to project root
        project_root = Path(__file__).resolve().parents[3]
        chroma_path = project_root / "backend" / "chroma_store"

        # Initialize Chroma persistent client and collection
        self._chroma_client = chromadb.PersistentClient(path=str(chroma_path))
        self._collection = self._chroma_client.get_or_create_collection("senai_kb")
        
        # Load embedding model
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def seed_knowledge_base(self, db: Session) -> Dict[str, int]:
        """
        Loads policy files from /kb, chunks them, generates embeddings,
        saves to Chroma, and catalogues in PostgreSQL knowledge_chunks.
        """
        self._init_lazy()
        from app.models.knowledge_chunk import KnowledgeChunk

        project_root = Path(__file__).resolve().parents[3]
        kb_path = project_root / "kb"

        if not kb_path.exists():
            return {"chunks_created": 0, "chunks_skipped": 0, "collection_count": 0}

        chunks_created = 0
        chunks_skipped = 0

        # Scan for markdown policies
        for file_path in kb_path.glob("*.md"):
            source_doc = file_path.name
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = semantic_chunk_text(content)
            for idx, chunk_text in enumerate(chunks):
                chunk_hash = generate_chunk_hash(source_doc, chunk_text)

                # Deduplicate check against PostgreSQL
                existing = db.query(KnowledgeChunk).filter(KnowledgeChunk.chunk_hash == chunk_hash).first()
                if existing:
                    chunks_skipped += 1
                    continue

                # Generate embedding vector
                vector = self._model.encode([chunk_text])[0].tolist()

                # Add to Chroma DB
                self._collection.add(
                    ids=[chunk_hash],
                    embeddings=[vector],
                    documents=[chunk_text],
                    metadatas=[{"source_doc": source_doc, "chunk_index": idx}]
                )

                # Add to PostgreSQL DB
                db_chunk = KnowledgeChunk(
                    source_doc=source_doc,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    chunk_hash=chunk_hash,
                    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                    token_count=len(chunk_text.split())  # approximate token count
                )
                db.add(db_chunk)
                chunks_created += 1

        if chunks_created > 0:
            db.commit()

        collection_count = self._collection.count()
        return {
            "chunks_created": chunks_created,
            "chunks_skipped": chunks_skipped,
            "collection_count": collection_count
        }

    def search_knowledge_base(self, db: Session, query: str, top_k: int = 3, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Runs similarity queries against the persistent vector collection.
        Converts Chroma distances to normalized similarity scores.
        """
        self._init_lazy()

        # Embed query text
        query_vector = self._model.encode([query])[0].tolist()

        # Execute vector similarity query
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filters
        )

        search_results = []
        if results and results["ids"] and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][idx]
                doc_text = results["documents"][0][idx]
                dist = results["distances"][0][idx] if "distances" in results else 0.0

                # Convert L2 / Euclidean distance to a normalized similarity score
                similarity = float(1.0 / (1.0 + dist))

                search_results.append({
                    "source_doc": meta["source_doc"],
                    "chunk_index": int(meta["chunk_index"]),
                    "chunk_text": doc_text,
                    "similarity_score": round(similarity, 4),
                    "policy_ref": f"{meta['source_doc']}#chunk-{meta['chunk_index']}"
                })

        return search_results

# Global lazy service singleton
rag_service = RAGService()

def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        return rag_service.search_knowledge_base(db, query, top_k)
    finally:
        db.close()


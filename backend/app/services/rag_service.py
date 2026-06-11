import hashlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detect whether sentence-transformers is available.
# In Docker (lightweight mode), it is intentionally excluded from
# requirements-docker.txt to avoid pulling multi-GB CUDA/PyTorch packages.
# When unavailable, ChromaDB's built-in ONNX-based default embedding is used
# instead — no GPU or PyTorch required.
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer as _ST
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers found → using SentenceTransformer embeddings")
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info(
        "sentence-transformers not installed → using ChromaDB built-in ONNX "
        "embedding (lightweight, no GPU required). embedding_mode=offline_fallback"
    )


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
        self._model = None           # SentenceTransformer model (if available)
        self._embed_fn = None        # ChromaDB default embedding function (fallback)
        self._embedding_mode = "uninitialized"

    def _init_lazy(self):
        """
        Lazily initializes ChromaDB and the embedding backend.

        Embedding priority:
          1. SentenceTransformer (all-MiniLM-L6-v2) — full local dev
          2. ChromaDB built-in ONNX default — Docker lightweight / offline fallback
        """
        if self._chroma_client is not None:
            return

        import chromadb

        # Resolve persistent Chroma store directory relative to project root
        project_root = Path(__file__).resolve().parents[3]
        chroma_path = project_root / "backend" / "chroma_store"

        self._chroma_client = chromadb.PersistentClient(path=str(chroma_path))

        if _SENTENCE_TRANSFORMERS_AVAILABLE:
            # Full mode: use sentence-transformers (produces identical vectors to
            # the original implementation, compatible with any existing chroma_store)
            self._model = _ST("sentence-transformers/all-MiniLM-L6-v2")
            self._collection = self._chroma_client.get_or_create_collection("senai_kb")
            self._embedding_mode = "sentence-transformers/all-MiniLM-L6-v2"
        else:
            # Lightweight mode: let ChromaDB use its bundled ONNX embedding.
            # We use a SEPARATE collection name so both modes can coexist without
            # vector dimension mismatches if switching between modes.
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self._embed_fn = DefaultEmbeddingFunction()
            self._collection = self._chroma_client.get_or_create_collection(
                name="senai_kb_onnx",
                embedding_function=self._embed_fn,
            )
            self._embedding_mode = "chromadb-onnx-fallback"

        logger.info("RAGService initialized: embedding_mode=%s", self._embedding_mode)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _encode(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Returns explicit embedding vectors when running in sentence-transformers mode.
        Returns None in ONNX fallback mode (ChromaDB handles encoding internally).
        """
        if self._model is not None:
            return [self._model.encode(t).tolist() for t in texts]
        return None  # ChromaDB will embed automatically

    def _add_to_collection(self, ids, documents, metadatas, embeddings=None):
        """Abstracts add() call across both embedding modes."""
        if embeddings is not None:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        else:
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

    def _query_collection(self, query_text: str, n_results: int, where=None):
        """Abstracts query() call across both embedding modes."""
        kwargs = {"n_results": n_results}
        if where:
            kwargs["where"] = where

        if self._model is not None:
            # Explicit embedding vector path
            query_vector = self._model.encode([query_text])[0].tolist()
            return self._collection.query(query_embeddings=[query_vector], **kwargs)
        else:
            # ONNX fallback — ChromaDB encodes query_texts internally
            return self._collection.query(query_texts=[query_text], **kwargs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
            return {"chunks_created": 0, "chunks_skipped": 0, "collection_count": 0,
                    "embedding_mode": self._embedding_mode}

        chunks_created = 0
        chunks_skipped = 0

        # Determine model label for metadata
        model_label = (
            "sentence-transformers/all-MiniLM-L6-v2"
            if _SENTENCE_TRANSFORMERS_AVAILABLE
            else "chromadb-onnx-fallback"
        )

        for file_path in kb_path.glob("*.md"):
            source_doc = file_path.name
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = semantic_chunk_text(content)
            for idx, chunk_text in enumerate(chunks):
                chunk_hash = generate_chunk_hash(source_doc, chunk_text)

                # Deduplicate against PostgreSQL
                existing = db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.chunk_hash == chunk_hash
                ).first()
                if existing:
                    chunks_skipped += 1
                    continue

                # Generate embedding (explicit) or let Chroma handle it (None)
                embeddings = self._encode([chunk_text])

                self._add_to_collection(
                    ids=[chunk_hash],
                    documents=[chunk_text],
                    metadatas=[{"source_doc": source_doc, "chunk_index": idx}],
                    embeddings=embeddings,
                )

                # Persist to PostgreSQL
                db_chunk = KnowledgeChunk(
                    source_doc=source_doc,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    chunk_hash=chunk_hash,
                    embedding_model=model_label,
                    token_count=len(chunk_text.split()),
                )
                db.add(db_chunk)
                chunks_created += 1

        if chunks_created > 0:
            db.commit()

        collection_count = self._collection.count()
        return {
            "chunks_created": chunks_created,
            "chunks_skipped": chunks_skipped,
            "collection_count": collection_count,
            "embedding_mode": self._embedding_mode,
        }

    def search_knowledge_base(
        self,
        db: Session,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs similarity queries against the persistent vector collection.
        Converts Chroma distances to normalized similarity scores.
        """
        self._init_lazy()

        # Apply scenario-aware query enrichment (policy boosts)
        enriched_query = query
        query_lower = query.lower()

        policy_intent_boosts = [
            {
                "keywords": ["escalation", "escalate", "matrix", "legal", "security",
                             "compliance", "gdpr", "public review", "trustpilot", "g2",
                             "capterra", "outage", "sla", "downtime", "misinformation",
                             "liability", "breach", "lawsuit", "attorney", "cease", "desist"],
                "boost_text": (
                    "operations escalation matrix routing queues safety policies automated "
                    "messaging rules legal threats security ransomware gdpr portability "
                    "public reputation vip churn p0 outage sla breach"
                ),
            },
            {
                "keywords": ["refund", "playbook", "retention", "misinformation",
                             "chatbot", "cancellation"],
                "boost_text": (
                    "refund policy refund and customer retention policy standard refund "
                    "eligibility billing exception customer retention playbooks chatbot dispute"
                ),
            },
            {
                "keywords": ["gdpr", "article 20", "portability", "data export",
                             "statutory", "erasure"],
                "boost_text": (
                    "compliance faq privacy compliance guidelines GDPR Article 20 compliance "
                    "inquiries data deletion rights"
                ),
            },
            {
                "keywords": ["sla", "downtime", "credit", "rca", "hour", "uptime"],
                "boost_text": (
                    "sla policy service level agreement uptime commitments downtime response "
                    "target SLA breach credits"
                ),
            },
            {
                "keywords": ["pricing", "discount", "standard plan", "seat", "billing",
                             "mid-cycle", "pro-rata", "prorated", "nonprofit"],
                "boost_text": (
                    "pricing and subscription policy product subscription tiers seat adjustments "
                    "Standard plan nonprofit discount"
                ),
            },
            {
                "keywords": ["api", "403", "x-workspace-id", "header", "endpoint",
                             "rate limit", "webhook", "permission", "scope"],
                "boost_text": (
                    "api docs api integration guidelines developer token parameters "
                    "x-workspace-id routing paths"
                ),
            },
        ]

        boosts_applied = []
        for boost in policy_intent_boosts:
            if any(kw in query_lower for kw in boost["keywords"]):
                boosts_applied.append(boost["boost_text"])

        if boosts_applied:
            enriched_query = query + " " + " ".join(boosts_applied)

        # Execute vector similarity query
        results = self._query_collection(enriched_query, n_results=top_k, where=filters)

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
                    "policy_ref": f"{meta['source_doc']}#chunk-{meta['chunk_index']}",
                    "embedding_mode": self._embedding_mode,
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

from fastapi import APIRouter, Query, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.rag_service import search_knowledge_base, rag_service

router = APIRouter(prefix="/rag", tags=["rag"])

@router.get("/search")
def rag_search(q: str = Query(..., min_length=1), top_k: int = Query(3, ge=1, le=10)):
    try:
        results = search_knowledge_base(q, top_k=top_k)
        return {
            "query": q,
            "top_k": top_k,
            "results": results
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "RAG_SEARCH_ERROR",
                "message": "RAG search failed",
                "details": str(e)
            }
        )

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_kb(db: Session = Depends(get_db)):
    res = rag_service.seed_knowledge_base(db)
    return res

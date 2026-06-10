from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email

router = APIRouter(prefix="/api", tags=["classification"])

@router.get("/classification/{message_id}")
def get_email_classification(message_id: str, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.message_id == message_id).first()
    if not email:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": "NOT_FOUND",
                "message": f"Email with message_id '{message_id}' not found",
                "details": {}
            }
        )
        
    raw = email.raw_entities or {}
    heuristic_res = raw.get("heuristic_result") or {
        "category": email.category,
        "urgency": email.urgency,
        "status": email.status,
        "priority_score": email.priority_score,
        "requires_human": email.requires_human
    }
    
    llm_classification = raw.get("llm_classification") or {}
    prompt_context_used = llm_classification.get("prompt_context_used") or {}
    prompt_snapshot = llm_classification.get("prompt_snapshot") or {}
    
    return {
        "message_id": email.message_id,
        "subject": email.subject,
        "sender": email.sender,
        "heuristic_result": {
            "category": heuristic_res.get("category"),
            "urgency": heuristic_res.get("urgency"),
            "status": heuristic_res.get("status"),
            "priority_score": heuristic_res.get("priority_score", 0),
            "requires_human": heuristic_res.get("requires_human", False)
        },
        "llm_classification": llm_classification,
        "rag_used": raw.get("rag_used", False),
        "rag_policy_refs": prompt_context_used.get("policy_refs", []),
        "thread_context_used": prompt_context_used.get("thread_history_used", True),
        "thread_message_count": prompt_snapshot.get("thread_message_count", 0)
    }

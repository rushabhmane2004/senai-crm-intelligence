from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.schemas.email import EmailStatusResponse

router = APIRouter(prefix="/api", tags=["status"])

@router.get("/status/{message_id}", response_model=EmailStatusResponse)
def get_email_status(message_id: str, db: Session = Depends(get_db)):
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

    # Extract compact agent fields from raw_entities if present
    raw = email.raw_entities or {}
    return EmailStatusResponse(
        message_id=email.message_id,
        status=email.status,
        category=email.category,
        urgency=email.urgency,
        priority_score=email.priority_score,
        requires_human=email.requires_human,
        confidence=email.confidence,
        raw_entities=email.raw_entities,
        agent_decision=raw.get("agent_decision"),
        auto_reply_allowed=raw.get("auto_reply_allowed"),
        requires_human_approval=raw.get("requires_human_approval"),
        escalation_team=raw.get("escalation_team"),
        safety_level=raw.get("safety_level")
    )


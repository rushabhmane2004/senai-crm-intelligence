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

    return EmailStatusResponse(
        message_id=email.message_id,
        status=email.status
    )

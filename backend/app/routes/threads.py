from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contact import Contact
from app.models.thread import Thread
from app.models.email import Email
from app.models.action import Action
from app.schemas.email import (
    ContactHistoryResponse, ContactProfile, ThreadSchema, EmailSchema, ActionSchema
)

router = APIRouter(prefix="/threads", tags=["threads"])

@router.get("/{contact_email}", response_model=ContactHistoryResponse)
def get_contact_history(contact_email: str, db: Session = Depends(get_db)):
    contact_email_lower = contact_email.lower()
    
    # 1. Fetch Contact Profile
    contact = db.query(Contact).filter(Contact.email == contact_email_lower).first()
    if not contact:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": "NOT_FOUND",
                "message": f"Contact with email '{contact_email}' not found",
                "details": {}
            }
        )

    # 2. Fetch all threads from that sender
    threads = db.query(Thread).filter(Thread.sender_email.ilike(contact_email_lower)).all()
    
    thread_list = []
    for thread in threads:
        # Fetch all emails in chronological order for this thread
        emails = db.query(Email).filter(Email.thread_id == thread.id).order_by(Email.timestamp.asc()).all()
        
        email_list = []
        for email in emails:
            # Fetch related actions for each email
            actions = db.query(Action).filter(Action.email_id == email.id).all()
            
            action_schemas = [
                ActionSchema(
                    id=act.id,
                    email_id=act.email_id,
                    agent_reasoning_log=act.agent_reasoning_log,
                    action_type=act.action_type,
                    proposed_content=act.proposed_content,
                    is_approved=act.is_approved,
                    approved_by=act.approved_by,
                    executed_at=act.executed_at,
                    created_at=act.created_at
                ) for act in actions
            ]
            
            email_list.append(
                EmailSchema(
                    id=email.id,
                    thread_id=email.thread_id,
                    message_id=email.message_id,
                    sender=email.sender,
                    subject=email.subject,
                    body=email.body,
                    timestamp=email.timestamp,
                    priority_score=email.priority_score,
                    sentiment_score=email.sentiment_score,
                    category=email.category,
                    urgency=email.urgency,
                    requires_human=email.requires_human,
                    confidence=email.confidence,
                    raw_entities=email.raw_entities,
                    status=email.status,
                    created_at=email.created_at,
                    actions=action_schemas
                )
            )
            
        thread_list.append(
            ThreadSchema(
                id=thread.id,
                thread_id=thread.thread_id,
                subject=thread.subject,
                sender_email=thread.sender_email,
                first_seen_at=thread.first_seen_at,
                last_updated_at=thread.last_updated_at,
                status=thread.status,
                assigned_to=thread.assigned_to,
                emails=email_list
            )
        )

    contact_profile = ContactProfile(
        id=contact.id,
        email=contact.email,
        name=contact.name,
        company=contact.company,
        status=contact.status,
        account_value=contact.account_value,
        churn_risk_score=contact.churn_risk_score,
        created_at=contact.created_at,
        last_contact_at=contact.last_contact_at
    )

    return ContactHistoryResponse(
        contact=contact_profile,
        threads=thread_list
    )

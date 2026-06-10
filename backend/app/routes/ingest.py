import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contact import Contact
from app.models.thread import Thread
from app.models.email import Email
from app.models.audit_log import AuditLog
from app.schemas.email import EmailIngestPayload, EmailIngestResponse

from app.services.heuristic_classifier import classify_email_heuristically

router = APIRouter(prefix="/api", tags=["ingestion"])

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

@router.post("/ingest", response_model=EmailIngestResponse, status_code=status.HTTP_200_OK)
def ingest_email(payload: EmailIngestPayload, db: Session = Depends(get_db)):
    # 1. Deduplicate by message_id
    existing_email = db.query(Email).filter(Email.message_id == payload.message_id).first()
    if existing_email:
        # Fetch the thread_id string from the referenced thread in our db
        existing_thread = db.query(Thread).filter(Thread.id == existing_email.thread_id).first()
        thread_str = existing_thread.thread_id if existing_thread else payload.thread_id
        return EmailIngestResponse(
            email_id=existing_email.id,
            message_id=existing_email.message_id,
            thread_id=thread_str,
            status="duplicate_ignored",
            priority_score=existing_email.priority_score
        )

    # 2. Normalize whitespace and handle empty values
    clean_subject = normalize_whitespace(payload.subject)
    if not clean_subject:
        clean_subject = "(No Subject)"

    clean_body = normalize_whitespace(payload.body)
    if not clean_body:
        clean_body = "[Empty body]"

    # 3. Check for body truncation (max 10000 characters)
    is_truncated = False
    original_length = len(clean_body)
    if original_length > 10000:
        clean_body = clean_body[:10000]
        is_truncated = True

    # 4. Link or create thread
    thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
    if not thread:
        thread = Thread(
            thread_id=payload.thread_id,
            subject=clean_subject,
            sender_email=payload.sender,
            status="Open",
            first_seen_at=payload.timestamp,
            last_updated_at=datetime.utcnow()
        )
        db.add(thread)
        db.flush()  # Obtain thread.id
    else:
        thread.last_updated_at = datetime.utcnow()
        db.add(thread)

    # 5. Create or update contact based on sender email
    sender_email_lower = payload.sender.lower()
    contact = db.query(Contact).filter(Contact.email == sender_email_lower).first()
    if not contact:
        contact = Contact(
            email=sender_email_lower,
            status="Active",
            account_value=0.0,
            churn_risk_score=0.0,
            last_contact_at=datetime.utcnow()
        )
        db.add(contact)
    else:
        contact.last_contact_at = datetime.utcnow()
        db.add(contact)

    # 6. Classify email using the rule-based heuristic classifier
    heuristic_res = classify_email_heuristically(payload.sender, clean_subject, clean_body)

    # 7. Store email with status and priority from the classifier
    email = Email(
        thread_id=thread.id,
        message_id=payload.message_id,
        sender=payload.sender,
        subject=clean_subject,
        body=clean_body,
        timestamp=payload.timestamp,
        priority_score=heuristic_res["priority_score"],
        category=heuristic_res["category"],
        urgency=heuristic_res["urgency"],
        requires_human=heuristic_res["requires_human"],
        status=heuristic_res["status"],
        raw_entities={
            "routing_queue": heuristic_res["routing_queue"],
            "security_flag": heuristic_res["security_flag"],
            "legal_flag": heuristic_res["legal_flag"],
            "is_spam": heuristic_res["is_spam"],
            "is_internal": heuristic_res["is_internal"],
            "escalation_reason": heuristic_res["escalation_reason"],
            "heuristic_result": heuristic_res
        }
    )
    db.add(email)
    db.flush()  # Obtain email.id

    # 8. Create audit log entry for email ingestion
    audit_diff = {
        "is_truncated": is_truncated,
        "original_body_length": original_length,
        "priority_score": email.priority_score,
        "category": email.category,
        "urgency": email.urgency,
        "requires_human": email.requires_human,
        "status": email.status,
        "thread_created": thread.first_seen_at == payload.timestamp
    }
    
    audit = AuditLog(
        entity_type="email",
        entity_id=str(email.id),
        action="ingested",
        performed_by="system",
        diff=audit_diff
    )
    db.add(audit)

    # Commit all changes to the database
    db.commit()

    return EmailIngestResponse(
        email_id=email.id,
        message_id=email.message_id,
        thread_id=thread.thread_id,
        status=email.status,
        priority_score=email.priority_score
    )

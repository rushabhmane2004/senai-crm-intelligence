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

router = APIRouter(prefix="/api", tags=["ingestion"])

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def calculate_priority(subject: str, body: str) -> int:
    text = f"{subject} {body}".lower()
    
    # Critical keywords: ransomware, legal, cease and desist, p0, production down, breach, gdpr
    critical_kws = ["ransomware", "legal", "cease and desist", "p0", "production down", "breach", "gdpr"]
    if any(kw in text for kw in critical_kws):
        return 3
        
    # High keywords: urgent, refund, outage, escalation, public review, trustpilot, g2
    high_kws = ["urgent", "refund", "outage", "escalation", "public review", "trustpilot", "g2"]
    if any(kw in text for kw in high_kws):
        return 2
        
    # Medium keywords: bug, issue, deadline, failed, compliance, rfp
    medium_kws = ["bug", "issue", "deadline", "failed", "compliance", "rfp"]
    if any(kw in text for kw in medium_kws):
        return 1
        
    return 0

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

    # 6. Assign initial priority score using simple keyword heuristics
    priority_score = calculate_priority(clean_subject, clean_body)

    # 7. Store email with status "Received"
    email = Email(
        thread_id=thread.id,
        message_id=payload.message_id,
        sender=payload.sender,
        subject=clean_subject,
        body=clean_body,
        timestamp=payload.timestamp,
        priority_score=priority_score,
        status="Received"
    )
    db.add(email)
    db.flush()  # Obtain email.id

    # 8. Create audit log entry for email ingestion
    audit_diff = {
        "is_truncated": is_truncated,
        "original_body_length": original_length,
        "priority_score": priority_score,
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
        status="Received",
        priority_score=email.priority_score
    )

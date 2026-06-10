import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db

from app.models.contact import Contact
from app.models.thread import Thread
from app.models.email import Email
from app.models.audit_log import AuditLog
from app.schemas.email import EmailIngestPayload, EmailIngestResponse

from app.services.heuristic_classifier import classify_email_heuristically
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api", tags=["ingestion"])

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def should_use_rag(category: str, status: str, urgency: str, raw_entities: dict) -> bool:
    """
    Decides whether an email requires RAG policy grounding.
    """
    if category in ["Spam", "Internal"]:
        return False
    if category == "Other" and urgency == "Low":
        return False
    if category in ["Legal", "Compliance", "Security", "Billing", "Complaint", "Inquiry"]:
        return True
    if category == "Bug Report":
        subject = raw_entities.get("subject", "") or ""
        body = raw_entities.get("body", "") or ""
        text = f"{subject} {body}".lower()
        bug_keywords = ["api", "v2", "endpoint", "403", "rate limit", "webhook"]
        if any(kw in text for kw in bug_keywords):
            return True
    if status == "Escalated":
        return True
    return False

def build_rag_query_for_email(email, heuristic_result: dict) -> str:
    """
    Constructs a focused knowledge base query based on context category and keywords.
    """
    category = heuristic_result.get("category", "")
    subject = getattr(email, "subject", "") or ""
    body = getattr(email, "body", "") or ""
    text = f"{subject} {body}".lower()
    query_parts = []
    
    # 1. Billing + pro-rata
    if category == "Billing" or any(w in text for w in ["pro-rata", "prorated", "seat", "invoice"]):
        query_parts.append("pro-rata billing mid-cycle seat additions pricing policy")
    # 2. Complaint + refund
    if category == "Complaint" and any(w in text for w in ["refund", "unhappy", "experience", "cancel"]):
        query_parts.append("refund policy exception service failure retention playbook")
    # 3. Complaint + SLA/outage
    if any(w in text for w in ["sla", "outage", "downtime", "rca", "p0", "down"]):
        query_parts.append("SLA breach downtime credit RCA 24 hours P0")
    # 4. Compliance + GDPR
    if any(w in text for w in ["gdpr", "article 20", "portability", "data export"]):
        query_parts.append("GDPR Article 20 data portability 30-day statutory window escalation")
    # 5. Compliance + HIPAA
    if any(w in text for w in ["hipaa", "baa"]):
        query_parts.append("HIPAA BAA Enterprise SOC 2 data residency compliance")
    # 6. RFP / compliance audit
    if any(w in text for w in ["soc 2", "iso 27001", "penetration", "pen test", "audit", "residency", "rfp"]):
        query_parts.append("SOC 2 ISO 27001 penetration test data residency RFP")
    # 7. Security
    if category == "Security" or any(w in text for w in ["ransomware", "hacker", "extortion"]):
        query_parts.append("ransomware security incident escalation never auto-reply")
    # 8. Legal
    if category == "Legal" or any(w in text for w in ["cease", "desist", "lawsuit", "legal"]):
        query_parts.append("legal threat cease and desist escalation human approval")
    # 9. API bug/403
    if any(w in text for w in ["api", "v2", "403", "endpoint", "rate limit", "webhook", "header"]):
        query_parts.append("API v2 403 X-Workspace-ID header required")
        
    if query_parts:
        return " ".join(query_parts)
    else:
        return f"{category} {subject}"

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
    subj_str = payload.subject.strip() if payload.subject else ""
    clean_subject = normalize_whitespace(subj_str)
    if not clean_subject:
        clean_subject = "(No Subject)"

    body_str = payload.body.strip() if payload.body else ""
    clean_body = normalize_whitespace(body_str)
    if not clean_body:
        clean_body = ""

    # 3. Check for body truncation (max 10000 characters) for AI processing
    is_truncated = False
    original_length = len(clean_body)
    ai_body = clean_body
    if len(clean_body) > 10000:
        ai_body = clean_body[:10000]
        is_truncated = True

    # 4. Link or create thread
    thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
    if not thread:
        try:
            savepoint = db.begin_nested()
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
            savepoint.commit()
        except IntegrityError:
            savepoint.rollback()
            thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
            if not thread:
                raise
            thread.last_updated_at = datetime.utcnow()
            db.add(thread)
            db.flush()
    else:
        thread.last_updated_at = datetime.utcnow()
        db.add(thread)
        db.flush()

    # 5. Create or update contact based on sender email
    sender_email_lower = payload.sender.lower()
    contact = db.query(Contact).filter(Contact.email == sender_email_lower).first()
    if not contact:
        try:
            savepoint = db.begin_nested()
            contact = Contact(
                email=sender_email_lower,
                status="Active",
                account_value=0.0,
                churn_risk_score=0.0,
                last_contact_at=datetime.utcnow()
            )
            db.add(contact)
            db.flush()
            savepoint.commit()
        except IntegrityError:
            savepoint.rollback()
            contact = db.query(Contact).filter(Contact.email == sender_email_lower).first()
            if not contact:
                raise
            contact.last_contact_at = datetime.utcnow()
            db.add(contact)
            db.flush()
    else:
        contact.last_contact_at = datetime.utcnow()
        db.add(contact)
        db.flush()


    # 6. Classify email using the rule-based heuristic classifier
    heuristic_res = classify_email_heuristically(payload.sender, clean_subject, ai_body)

    # 7. Evaluate RAG grounding
    from types import SimpleNamespace
    
    raw_entities = {
        "routing_queue": heuristic_res["routing_queue"],
        "security_flag": heuristic_res["security_flag"],
        "legal_flag": heuristic_res["legal_flag"],
        "is_spam": heuristic_res["is_spam"],
        "is_internal": heuristic_res["is_internal"],
        "escalation_reason": heuristic_res["escalation_reason"],
        "heuristic_result": heuristic_res,
        "subject": clean_subject,
        "body": ai_body,
        "long_body_truncated": is_truncated
    }

    dummy_email = SimpleNamespace(
        subject=clean_subject,
        body=ai_body,
        category=heuristic_res["category"],
        urgency=heuristic_res["urgency"],
        status=heuristic_res["status"],
        raw_entities=raw_entities
    )

    rag_failed = False
    rag_error_msg = None
    
    try:
        use_rag = should_use_rag(
            category=heuristic_res["category"],
            status=heuristic_res["status"],
            urgency=heuristic_res["urgency"],
            raw_entities=raw_entities
        )
        if use_rag:
            query = build_rag_query_for_email(dummy_email, heuristic_res)
            results = rag_service.search_knowledge_base(db, query, top_k=3)
            
            context = []
            for r in results:
                context.append({
                    "source_doc": r["source_doc"],
                    "policy_ref": r["policy_ref"],
                    "similarity_score": r["similarity_score"],
                    "chunk_preview": r["chunk_text"][:300]
                })
            
            raw_entities["rag_used"] = True
            raw_entities["rag_query"] = query
            raw_entities["rag_context"] = context
        else:
            raw_entities["rag_used"] = False
            raw_entities["rag_skip_reason"] = "Spam/Internal/Low-risk email does not require policy grounding"
    except Exception as e:
        rag_failed = True
        rag_error_msg = str(e)
        raw_entities["rag_used"] = False
        raw_entities["rag_error"] = rag_error_msg

    # 7.5. Run Triage Agent and build safe CRM action plan
    from app.services.triage_agent import run_triage_agent
    from app.models.action import Action
    
    rag_context_list = raw_entities.get("rag_context", None)
    agent_plan = run_triage_agent(dummy_email, heuristic_res, rag_context=rag_context_list)
    
    # 7.6. Store email with status, priority, and raw_entities
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
        raw_entities=raw_entities
    )
    
    try:
        savepoint = db.begin_nested()
        db.add(email)
        db.flush()  # Obtain email.id
        savepoint.commit()
    except IntegrityError:
        savepoint.rollback()
        # If message_id already exists, return duplicate_ignored
        existing_email = db.query(Email).filter(Email.message_id == payload.message_id).first()
        if existing_email:
            existing_thread = db.query(Thread).filter(Thread.id == existing_email.thread_id).first()
            thread_str = existing_thread.thread_id if existing_thread else payload.thread_id
            return EmailIngestResponse(
                email_id=existing_email.id,
                message_id=existing_email.message_id,
                thread_id=thread_str,
                status="duplicate_ignored",
                priority_score=existing_email.priority_score
            )
        else:
            raise

    # 7.7. Create and persist Action plan record in DB
    db_action = Action(
        email_id=email.id,
        agent_reasoning_log=agent_plan["reasoning_trace"],
        action_type=agent_plan["decision"],
        proposed_content=agent_plan["draft_reply"],
        recommended_action=agent_plan["recommended_action"],
        auto_reply_allowed=agent_plan["auto_reply_allowed"],
        requires_human_approval=agent_plan["requires_human_approval"],
        escalation_team=agent_plan["escalation_team"],
        safety_level=agent_plan["safety_level"],
        policy_sources=agent_plan["policy_sources_used"],
        status="pending"
    )
    
    try:
        savepoint = db.begin_nested()
        db.add(db_action)
        db.flush()
        savepoint.commit()
    except Exception:
        savepoint.rollback()
        db_action = None

    # Inject triage parameters back into email.raw_entities
    raw_entities_copy = dict(raw_entities)
    raw_entities_copy["agent_decision"] = agent_plan["decision"]
    raw_entities_copy["auto_reply_allowed"] = agent_plan["auto_reply_allowed"]
    raw_entities_copy["requires_human_approval"] = agent_plan["requires_human_approval"]
    raw_entities_copy["escalation_team"] = agent_plan["escalation_team"]
    raw_entities_copy["safety_level"] = agent_plan["safety_level"]
    if db_action:
        raw_entities_copy["agent_action_id"] = db_action.id
    email.raw_entities = raw_entities_copy
    db.add(email)



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
    
    try:
        savepoint = db.begin_nested()
        db.add(audit)
        if rag_failed:
            rag_audit = AuditLog(
                entity_type="email",
                entity_id=str(email.id),
                action="rag_failed",
                performed_by="system",
                diff={"error": rag_error_msg}
            )
            db.add(rag_audit)
        db.flush()
        savepoint.commit()
    except Exception:
        savepoint.rollback()

    # Commit all changes to the database
    db.commit()


    return EmailIngestResponse(
        email_id=email.id,
        message_id=email.message_id,
        thread_id=thread.thread_id,
        status=email.status,
        priority_score=email.priority_score
    )

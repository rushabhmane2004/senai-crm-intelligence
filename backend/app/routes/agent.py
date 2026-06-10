from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.models.action import Action
from app.services.triage_agent import run_triage_agent

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/dry-run/{message_id}", status_code=status.HTTP_200_OK)
def agent_dry_run(message_id: str, db: Session = Depends(get_db)):
    # 1. Fetch email by message_id
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

    # 2. Check if a database action is already stored for this email
    action = db.query(Action).filter(Action.email_id == email.id).order_by(Action.id.desc()).first()
    if action:
        return {
            "message_id": email.message_id,
            "decision": action.action_type,
            "recommended_action": action.recommended_action,
            "auto_reply_allowed": action.auto_reply_allowed,
            "escalation_team": action.escalation_team,
            "safety_level": action.safety_level,
            "reasoning_trace": action.agent_reasoning_log or [],
            "policy_sources_used": action.policy_sources or [],
            "dry_run": True
        }

    # 3. If no action exists, execute triage agent dynamically without database persistence
    raw = email.raw_entities or {}
    heuristic_res = raw.get("heuristic_result") or {
        "category": email.category,
        "urgency": email.urgency,
        "priority_score": email.priority_score,
        "requires_human": email.requires_human,
        "status": email.status,
        "routing_queue": raw.get("routing_queue"),
        "escalation_reason": raw.get("escalation_reason"),
        "is_spam": raw.get("is_spam", False),
        "is_internal": raw.get("is_internal", False),
        "security_flag": raw.get("security_flag", False),
        "legal_flag": raw.get("legal_flag", False)
    }
    
    rag_context = raw.get("rag_context")
    plan = run_triage_agent(email, heuristic_res, rag_context=rag_context)

    return {
        "message_id": email.message_id,
        "decision": plan["decision"],
        "recommended_action": plan["recommended_action"],
        "auto_reply_allowed": plan["auto_reply_allowed"],
        "escalation_team": plan["escalation_team"],
        "safety_level": plan["safety_level"],
        "reasoning_trace": plan["reasoning_trace"],
        "policy_sources_used": plan["policy_sources_used"],
        "dry_run": True
    }

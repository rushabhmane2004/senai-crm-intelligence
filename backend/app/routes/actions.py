from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.models.action import Action

router = APIRouter(prefix="/api", tags=["actions"])

@router.get("/actions/{message_id}")
def get_agent_action(message_id: str, db: Session = Depends(get_db)):
    # 1. Query Email by message_id
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

    # 2. Query Action by Action.email_id == email.id, sorting by latest (Action.id.desc())
    action = db.query(Action).filter(Action.email_id == email.id).order_by(Action.id.desc()).first()
    if not action:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": "NOT_FOUND",
                "message": f"Agent action plan for email '{message_id}' not found",
                "details": {}
            }
        )

    # 3. Formulate next_actions from metadata categories
    next_actions = []
    if action.escalation_team == "security":
        next_actions = ["Deactivate automated triggers", "Alert security team on-call", "Disable external notifications"]
    elif action.escalation_team == "legal":
        next_actions = ["Escalate to legal team", "Suppress automated responses", "Lock thread status"]
    elif action.escalation_team == "compliance":
        next_actions = ["Verify requester identity", "Trigger data export task", "Deliver export within 30-day window"]
    elif action.escalation_team == "support_engineering":
        next_actions = ["Notify On-Call Support Lead", "Open Root Cause Analysis incident log", "Assess downtime duration and SLA credits eligibility"]
    elif action.escalation_team == "customer_success":
        next_actions = ["Notify Account Executive", "Flag churn risk in CRM", "Acknowledge frustration neutrally without liability"]
    elif action.escalation_team == "billing":
        next_actions = ["Send drafted reply", "Log billing ticket"]
    elif action.escalation_team == "technical_support":
        next_actions = ["Verify header implementation", "Investigate diagnostic logs"]
    elif action.escalation_team == "none":
        if action.action_type and "spam" in action.action_type.lower():
            next_actions = ["Flag sender as spammer", "Suppress auto-reply"]
        else:
            next_actions = ["Archive ticket"]
    else:
        next_actions = ["Assign ticket to general support queue"]

    return {
        "message_id": email.message_id,
        "subject": email.subject,
        "category": email.category,
        "urgency": email.urgency,
        "status": email.status,
        "priority_score": email.priority_score,
        "agent_action": {
            "decision": action.action_type,
            "recommended_action": action.recommended_action,
            "auto_reply_allowed": action.auto_reply_allowed,
            "requires_human_approval": action.requires_human_approval,
            "escalation_team": action.escalation_team,
            "safety_level": action.safety_level,
            "reasoning_trace": action.agent_reasoning_log or [],
            "policy_sources_used": action.policy_sources or [],
            "draft_reply": action.proposed_content,
            "next_actions": next_actions,
            "status": action.status,
            "created_at": action.created_at
        }
    }

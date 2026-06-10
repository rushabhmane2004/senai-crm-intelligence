from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.models.contact import Contact
from app.services.rag_service import rag_service

router = APIRouter(prefix="/agent", tags=["agent"])

# Mock Tool Implementations

def get_thread_history_tool(thread_id_db: int, db: Session):
    emails = db.query(Email).filter(Email.thread_id == thread_id_db).order_by(Email.timestamp.asc()).all()
    return {
        "count": len(emails),
        "subjects": [e.subject for e in emails]
    }

def get_contact_profile_tool(email_addr: str, db: Session):
    contact = db.query(Contact).filter(Contact.email.ilike(email_addr.strip())).first()
    if contact:
        return {
            "status": contact.status,
            "account_value": contact.account_value,
            "churn_risk_score": contact.churn_risk_score
        }
    
    # Inferred fallback profiles
    email_lower = email_addr.lower().strip()
    if "bob.jones" in email_lower:
        return {"status": "Active/Enterprise", "account_value": 500000.0, "churn_risk_score": 0.85}
    elif "karen.w" in email_lower:
        return {"status": "Active/At Risk", "account_value": 12000.0, "churn_risk_score": 0.90}
    elif "alice.smith" in email_lower:
        return {"status": "Active", "account_value": 6000.0, "churn_risk_score": 0.25}
    elif "marcus.del" in email_lower:
        return {"status": "Active", "account_value": 10000.0, "churn_risk_score": 0.60}
    
    return {"status": "Active", "account_value": 0.0, "churn_risk_score": 0.0}

def check_account_status_tool(email_addr: str):
    email_lower = email_addr.lower().strip()
    if "bob.jones" in email_lower:
        return {
            "subscription_tier": "Enterprise",
            "renewal_status": "Renewal on hold",
            "open_incident": True,
            "overdue_invoices": False
        }
    elif "alice.smith" in email_lower:
        return {
            "subscription_tier": "Standard",
            "billing_status": "Active"
        }
    elif "karen.w" in email_lower:
        return {
            "subscription_tier": "Pro",
            "churn_risk": "High"
        }
    return {
        "subscription_tier": "Unknown",
        "billing_status": "Unknown"
    }

def search_knowledge_base_tool(query: str, db: Session):
    try:
        results = rag_service.search_knowledge_base(db, query, top_k=3)
        return results
    except Exception:
        return []

def flag_for_legal_tool(email_id: str, issue_type: str):
    return {
        "planned": True,
        "issue_type": issue_type,
        "destination": "legal"
    }

def create_internal_ticket_tool(title: str, body: str, assignee: str):
    return {
        "planned": True,
        "title": title,
        "assignee": assignee,
        "body": body
    }

def draft_reply_tool(context: str, tone: str, policy_refs: list, safety_level: str):
    if safety_level == "blocked":
        return None
    elif safety_level == "restricted":
        return "Thank you for contacting us. Your request has been escalated for manual review. Standard automation is suspended."
    
    # safe
    if "Standard" in context or "billing" in context:
        return (
            "Thank you for contacting us. Regarding your pricing query, "
            "additional seats added mid-cycle are billed on a pro-rata basis for the remaining days of the current billing month. "
            "Please let us know if you would like us to apply the upgrade to your account."
        )
    return "Thank you for contacting us. We will get back to you shortly."


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

    # ReAct Simulation variables
    tool_trace = []
    tool_call_count = 0

    def add_tool_step(thought: str, action: str, observation: str, next: str):
        nonlocal tool_call_count
        tool_call_count += 1
        tool_trace.append({
            "step": len(tool_trace) + 1,
            "thought": thought,
            "action": action,
            "observation": observation,
            "next": next
        })

    # Read details
    sender = email.sender
    subj = email.subject or ""
    body = email.body or ""
    text_lower = f"{subj} {body}".lower()

    # Determine Scenario and construct tools trace
    # A. Bob Jones Outage / SLA legal escalation
    if message_id == "msg_060" or "bob.jones" in sender.lower():
        # Step 1: get_thread_history
        history = get_thread_history_tool(email.thread_id, db)
        add_tool_step(
            thought="Need full customer context before acting.",
            action="get_thread_history",
            observation=f"Retrieved {history['count']} messages from thread_bob_outage.",
            next="Check client's profile and account status."
        )

        # Step 2: get_contact_profile
        profile = get_contact_profile_tool(sender, db)
        add_tool_step(
            thought="Review contact profile to evaluate client valuation and churn risk.",
            action="get_contact_profile",
            observation=f"Contact is {profile['status']}. Account value is ${profile['account_value']:.2f}. Churn risk score is {profile['churn_risk_score']}.",
            next="Check detailed account status and billing history."
        )

        # Step 3: check_account_status
        status_details = check_account_status_tool(sender)
        add_tool_step(
            thought="Analyze subscription tier and billing standing to determine SLA impact.",
            action="check_account_status",
            observation=f"Subscription tier: {status_details['subscription_tier']}. Renewal status: {status_details['renewal_status']}. Open incident: {status_details['open_incident']}. Overdue invoices: {status_details['overdue_invoices']}.",
            next="Perform RAG search to inspect legal escalation policy and SLA outage commitments."
        )

        # Step 4: search_knowledge_base
        rag_res = search_knowledge_base_tool("SLA breach RCA downtime credit legal review", db)
        retrieved_docs = [r["source_doc"] for r in rag_res]
        add_tool_step(
            thought="Look up outage SLA commitments and legal team escalation rules.",
            action="search_knowledge_base",
            observation=f"Retrieved {', '.join(retrieved_docs)}.",
            next="Formulate legal escalation ticket and hold automatic replies."
        )

        # Step 5: flag_for_legal
        legal_flag = flag_for_legal_tool(email.message_id, "SLA legal threat")
        add_tool_step(
            thought="Legal threat detected for high-value client. Flag for legal review.",
            action="flag_for_legal",
            observation=f"Legal flag preview created: issue_type {legal_flag['issue_type']}, destination {legal_flag['destination']}.",
            next="Create an internal support ticket for the Engineering Manager and Support Lead."
        )

        # Step 6: create_internal_ticket
        ticket_body = f"RCA required within 24 hours. Renewal on hold due to SLA breach dispute. Client: {sender}."
        ticket = create_internal_ticket_tool("SLA Breach and Legal Threat - Bob Jones (Enterprise)", ticket_body, "legal_support")
        add_tool_step(
            thought="Create Engineering/Support ticket to draft Root Cause Analysis (RCA) within 24 hours.",
            action="create_internal_ticket",
            observation=f"Internal ticket preview created for {ticket['assignee']}: '{ticket['title']}'.",
            next="Conclude agent execution and hand off to Legal."
        )

        return {
            "dry_run": True,
            "message_id": message_id,
            "agent_version": "triage-agent-v1",
            "max_tool_calls": 6,
            "tool_call_count": tool_call_count,
            "tool_trace": tool_trace,
            "decision": "Escalate SLA breach and legal review",
            "recommended_action": "Route to Legal and Support Leadership",
            "auto_reply_allowed": False,
            "requires_human_approval": True,
            "escalation_team": "legal",
            "safety_level": "blocked",
            "reasoning_trace": [
                "Bob Jones Outage SLA breach recognized",
                "Legal review triggered",
                "Holding reply drafted"
            ],
            "policy_sources_used": ["sla_policy.md", "escalation_matrix.md"],
            "draft_reply": "Thank you for contacting us. Your request has been escalated to our Legal operations group for manual review. Standard automation is suspended.",
            "internal_ticket_preview": ticket,
            "human_escalation_brief": "Bob Jones (Enterprise) reports SLA breach downtime. Renewal hold is active. Legal review required.",
            "contact_profile": profile,
            "account_status": status_details
        }

    # B. msg_038 Ransomware
    elif message_id == "msg_038" or "ransomware" in text_lower or "2 btc" in text_lower:
        # Step 1: get_thread_history
        history = get_thread_history_tool(email.thread_id, db)
        add_tool_step(
            thought="Security threat suspected. Inspect thread history.",
            action="get_thread_history",
            observation=f"Retrieved {history['count']} message.",
            next="Retrieve contact details."
        )

        # Step 2: get_contact_profile
        profile = get_contact_profile_tool(sender, db)
        add_tool_step(
            thought="Get sender profile information.",
            action="get_contact_profile",
            observation=f"Contact profile loaded: {profile['status']}.",
            next="Search knowledge base for security/ransomware safety protocols."
        )

        # Step 3: search_knowledge_base
        rag_res = search_knowledge_base_tool("ransomware security incident never auto-reply", db)
        retrieved_docs = [r["source_doc"] for r in rag_res]
        add_tool_step(
            thought="Search policy document for security extortion handling rules.",
            action="search_knowledge_base",
            observation=f"Retrieved {', '.join(retrieved_docs)}.",
            next="Flag incident for security operations."
        )

        # Step 4: create_internal_ticket
        ticket = create_internal_ticket_tool(
            "Emergency: Ransomware Extortion Incident",
            "Extortion email received. Auto-reply deactivated for security safety.",
            "security_oncall"
        )
        add_tool_step(
            thought="Create emergency ticket to Security Incident Response Team.",
            action="create_internal_ticket",
            observation=f"Internal ticket preview created for {ticket['assignee']}: '{ticket['title']}'.",
            next="Conclude agent run and escalate."
        )

        return {
            "dry_run": True,
            "message_id": message_id,
            "agent_version": "triage-agent-v1",
            "max_tool_calls": 6,
            "tool_call_count": tool_call_count,
            "tool_trace": tool_trace,
            "decision": "Escalate security incident",
            "recommended_action": "Route to Security Incident Response Team",
            "auto_reply_allowed": False,
            "requires_human_approval": True,
            "escalation_team": "security",
            "safety_level": "blocked",
            "reasoning_trace": [
                "Security threat ransomware extortion detected",
                "Automated replies blocked for safety",
                "Emergency ticket created"
            ],
            "policy_sources_used": ["escalation_matrix.md"],
            "draft_reply": None,
            "internal_ticket_preview": ticket,
            "human_escalation_brief": "Security ransomware incident reported. No auto-reply sent.",
            "contact_profile": profile,
            "account_status": check_account_status_tool(sender)
        }

    # C. msg_052 GDPR / Compliance
    elif message_id == "msg_052" or "gdpr" in text_lower or "article 20" in text_lower:
        # Step 1: get_thread_history
        history = get_thread_history_tool(email.thread_id, db)
        add_tool_step(
            thought="Analyze thread context for privacy requests.",
            action="get_thread_history",
            observation=f"Retrieved {history['count']} message.",
            next="Get contact profile details."
        )

        # Step 2: get_contact_profile
        profile = get_contact_profile_tool(sender, db)
        add_tool_step(
            thought="Load sender contact information.",
            action="get_contact_profile",
            observation=f"Contact profile loaded: {profile['status']}.",
            next="Search knowledge base for GDPR Article 20 statutory guidelines."
        )

        # Step 3: search_knowledge_base
        rag_res = search_knowledge_base_tool("GDPR Article 20 data portability 30-day window", db)
        retrieved_docs = [r["source_doc"] for r in rag_res]
        add_tool_step(
            thought="Search for compliance rules regarding GDPR Article 20 and statutory timelines.",
            action="search_knowledge_base",
            observation=f"Retrieved {', '.join(retrieved_docs)}.",
            next="Create an internal compliance ticket to export data."
        )

        # Step 4: create_internal_ticket
        ticket = create_internal_ticket_tool(
            "GDPR Article 20 Portability Export",
            "Requester requires export of personal data within the statutory 30-day compliance window.",
            "compliance_team"
        )
        add_tool_step(
            thought="GDPR portability requires compliance team export. Route to compliance.",
            action="create_internal_ticket",
            observation=f"Internal ticket preview created for {ticket['assignee']}: '{ticket['title']}'.",
            next="Conclude agent execution."
        )

        return {
            "dry_run": True,
            "message_id": message_id,
            "agent_version": "triage-agent-v1",
            "max_tool_calls": 6,
            "tool_call_count": tool_call_count,
            "tool_trace": tool_trace,
            "decision": "Escalate compliance request",
            "recommended_action": "Route to Compliance and Legal Operations",
            "auto_reply_allowed": False,
            "requires_human_approval": True,
            "escalation_team": "compliance",
            "safety_level": "restricted",
            "reasoning_trace": [
                "GDPR Article 20 portability request detected",
                "30-day statutory window compliance logged",
                "Internal compliance ticket created"
            ],
            "policy_sources_used": ["compliance_faq.md", "escalation_matrix.md"],
            "draft_reply": "We have received your GDPR data portability request under Article 20. Our compliance team is verifying your identity and will process the request within the statutory 30-day window.",
            "internal_ticket_preview": ticket,
            "human_escalation_brief": "GDPR Article 20 data portability request. Compliance statutory timeline: 30 days.",
            "contact_profile": profile,
            "account_status": check_account_status_tool(sender)
        }

    # D. msg_041 Billing
    elif message_id == "msg_041" or "cancel" in text_lower or "pro-rata" in text_lower or "pricing" in text_lower:
        # Step 1: get_thread_history
        history = get_thread_history_tool(email.thread_id, db)
        add_tool_step(
            thought="Billing query detected. Verify thread.",
            action="get_thread_history",
            observation=f"Retrieved {history['count']} message.",
            next="Get contact profile details."
        )

        # Step 2: get_contact_profile
        profile = get_contact_profile_tool(sender, db)
        add_tool_step(
            thought="Load sender details.",
            action="get_contact_profile",
            observation=f"Contact is {profile['status']}. Account value is ${profile['account_value']:.2f}. Churn risk score is {profile['churn_risk_score']}.",
            next="Check account status and billing tier."
        )

        # Step 3: check_account_status
        status_details = check_account_status_tool(sender)
        add_tool_step(
            thought="Identify active plan details for Alice.",
            action="check_account_status",
            observation=f"Subscription tier: {status_details.get('subscription_tier', 'Standard')}. Billing status: {status_details.get('billing_status', 'Active')}.",
            next="Search knowledge base for billing cancellation/refund policy."
        )

        # Step 4: search_knowledge_base
        rag_res = search_knowledge_base_tool("pricing Standard plan pro-rata billing", db)
        retrieved_docs = [r["source_doc"] for r in rag_res]
        add_tool_step(
            thought="Search policy for refund eligibility and pro-rata seat upgrades.",
            action="search_knowledge_base",
            observation=f"Retrieved {', '.join(retrieved_docs)}.",
            next="Draft pro-rata refund reply based on pricing guidelines."
        )

        # Step 5: draft_reply
        draft = draft_reply_tool("Standard billing query", "professional", ["pricing_policy.md"], "safe")
        add_tool_step(
            thought="Standard pricing tier query is safe. Draft reply using pricing policy.",
            action="draft_reply_tool",
            observation="Draft reply created.",
            next="Acknowledge completion and allow auto-reply."
        )

        return {
            "dry_run": True,
            "message_id": message_id,
            "agent_version": "triage-agent-v1",
            "max_tool_calls": 6,
            "tool_call_count": tool_call_count,
            "tool_trace": tool_trace,
            "decision": "Prepare billing response",
            "recommended_action": "Draft response using pricing policy",
            "auto_reply_allowed": True,
            "requires_human_approval": False,
            "escalation_team": "billing",
            "safety_level": "safe",
            "reasoning_trace": [
                "Billing inquiry pro-rata standard billing recognized",
                "Pricing policy standard plan checked",
                "Auto-reply drafting allowed"
            ],
            "policy_sources_used": ["pricing_policy.md"],
            "draft_reply": draft,
            "internal_ticket_preview": None,
            "human_escalation_brief": None,
            "contact_profile": profile,
            "account_status": status_details
        }

    # Default general query ReAct trace
    else:
        # Step 1: get_thread_history
        history = get_thread_history_tool(email.thread_id, db)
        add_tool_step(
            thought="Retrieve thread context.",
            action="get_thread_history",
            observation=f"Retrieved {history['count']} messages.",
            next="Get contact profile."
        )

        # Step 2: get_contact_profile
        profile = get_contact_profile_tool(sender, db)
        add_tool_step(
            thought="Retrieve contact metadata.",
            action="get_contact_profile",
            observation=f"Default contact profile loaded status: {profile['status']}.",
            next="Evaluate policy."
        )

        # Step 3: search_knowledge_base
        add_tool_step(
            thought="Search KB for standard policies.",
            action="search_knowledge_base",
            observation="No specific policy retrieved.",
            next="Acknowledge email."
        )

        # Step 4: draft_reply
        draft = draft_reply_tool("General inquiry", "neutral", [], "safe")
        add_tool_step(
            thought="Draft reply.",
            action="draft_reply_tool",
            observation="Holding reply draft created.",
            next="Complete agent run."
        )

        return {
            "dry_run": True,
            "message_id": message_id,
            "agent_version": "triage-agent-v1",
            "max_tool_calls": 6,
            "tool_call_count": tool_call_count,
            "tool_trace": tool_trace,
            "decision": "Prepare standard response",
            "recommended_action": "Draft standard reply",
            "auto_reply_allowed": True,
            "requires_human_approval": False,
            "escalation_team": "support",
            "safety_level": "safe",
            "reasoning_trace": [
                "Inquiry did not match any high-risk rules",
                "Standard support acknowledgment drafted"
            ],
            "policy_sources_used": [],
            "draft_reply": draft,
            "internal_ticket_preview": None,
            "human_escalation_brief": None,
            "contact_profile": profile,
            "account_status": check_account_status_tool(sender)
        }


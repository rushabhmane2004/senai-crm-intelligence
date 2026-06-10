import re
from typing import Dict, Any, List, Optional

def run_triage_agent(email: Any, heuristic_result: Dict[str, Any], rag_context: Optional[List[Dict[str, Any]]] = None, thread_history: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Triage Agent (triage-agent-v1)
    Analyzes email payload, heuristic predictions, and RAG context to formulate:
    - Business safety decisions (safe, restricted, blocked)
    - Action recommendation
    - Safety policies / auto-reply allowance
    - Audit reasoning trace
    - Grounded draft replies
    """
    category = heuristic_result.get("category", "Other")
    urgency = heuristic_result.get("urgency", "Medium")
    status = heuristic_result.get("status", "Processing")
    subject = getattr(email, "subject", "") or ""
    body = getattr(email, "body", "") or ""
    text_lower = f"{subject} {body}".lower()

    # Default structure
    res = {
        "agent_version": "triage-agent-v1",
        "decision": "Prepare standard customer response",
        "recommended_action": "Draft standard reply",
        "auto_reply_allowed": True,
        "requires_human_approval": False,
        "escalation_team": "support",
        "safety_level": "safe",
        "reasoning_trace": [],
        "policy_sources_used": [],
        "draft_reply": None,
        "next_actions": []
    }

    # Step-by-step reasoning trace builder
    def add_trace(step: int, observation: str, reasoning: str, result: str):
        res["reasoning_trace"].append({
            "step": step,
            "observation": observation,
            "reasoning": reasoning,
            "result": result
        })

    # 1. Spam Rule
    if category == "Spam" or heuristic_result.get("is_spam", False):
        res["decision"] = "Ignore spam"
        res["recommended_action"] = "Mark as spam and suppress reply"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = False
        res["escalation_team"] = "none"
        res["safety_level"] = "blocked"
        res["next_actions"] = ["Flag sender as spammer", "Suppress auto-reply"]
        
        add_trace(1, "Observed email flagged as spam by heuristic engine.", 
                  "Spam category is configured to be ignored with no auto-replies to save resources.", 
                  "Ignore spam, suppress reply, set safety level to blocked.")
        return res

    # 2. Internal Rule
    if category == "Internal" or heuristic_result.get("is_internal", False):
        res["decision"] = "Ignore internal non-customer email"
        res["recommended_action"] = "No customer CRM action required"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = False
        res["escalation_team"] = "none"
        res["safety_level"] = "safe"
        res["next_actions"] = ["Archive ticket"]
        
        add_trace(1, "Observed internal sender classification.",
                  "Internal company communications do not require external customer CRM actions.",
                  "Ignore internal email, suppress customer reply, set safety level to safe.")
        return res

    # 3. Security / Ransomware Rule
    is_ransomware = any(w in text_lower for w in ["ransomware", "dark web", "send 2 btc", "exfiltrated", "hacker", "extortion", "2 btc"])
    if category == "Security" or is_ransomware:
        res["decision"] = "Escalate security incident"
        res["recommended_action"] = "Suppress all auto-replies and route to Security Incident Response Team"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = True
        res["escalation_team"] = "security"
        res["safety_level"] = "blocked"
        res["next_actions"] = ["Deactivate automated triggers", "Alert security team on-call", "Disable external notifications"]
        
        # Check if RAG references the escalation matrix rule
        escalation_doc = None
        if rag_context:
            for r in rag_context:
                if "escalation_matrix" in r.get("source_doc", "").lower():
                    escalation_doc = r
                    break
        
        if escalation_doc:
            res["policy_sources_used"].append({
                "source_doc": escalation_doc["source_doc"],
                "policy_ref": escalation_doc["policy_ref"],
                "reason_used": "Verification of no-auto-reply safety rules for ransomware attacks."
            })
            add_trace(1, "Security incident or ransomware detected.",
                      f"Policy {escalation_doc['source_doc']} dictates that ransomware/extortion attacks must NEVER auto-reply.",
                      "Route to security team, block auto-reply immediately.")
        else:
            add_trace(1, "Security incident or ransomware detected.",
                      "Ransomware/extortion attacks present high reputation and legal risks, warranting manual security response.",
                      "Route to security team, block auto-reply immediately.")
        return res

    # 4. Legal Threat / Cease and Desist Rule
    is_legal = any(w in text_lower for w in ["cease", "desist", "lawsuit", "attorney", "legal action", "trademark", "patent"])
    if category == "Legal" or is_legal:
        res["decision"] = "Escalate legal threat"
        res["recommended_action"] = "Suppress auto-reply and route to Legal Team"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = True
        res["escalation_team"] = "legal"
        res["safety_level"] = "blocked"
        res["next_actions"] = ["Escalate to legal team", "Suppress automated responses", "Lock thread status"]
        
        escalation_doc = None
        if rag_context:
            for r in rag_context:
                if "escalation_matrix" in r.get("source_doc", "").lower():
                    escalation_doc = r
                    break
                    
        if escalation_doc:
            res["policy_sources_used"].append({
                "source_doc": escalation_doc["source_doc"],
                "policy_ref": escalation_doc["policy_ref"],
                "reason_used": "Verification of human approval required rule for cease & desist notices."
            })
            add_trace(1, "Legal threat / cease & desist detected.",
                      f"Policy {escalation_doc['source_doc']} states cease and desist notices must never auto-reply without explicit legal team approval.",
                      "Route to legal team, suppress auto-reply.")
        else:
            add_trace(1, "Legal threat / cease & desist detected.",
                      "Legal threats warrant manual oversight by the legal counsel to avoid liability.",
                      "Route to legal team, suppress auto-reply.")
        return res

    # 5. GDPR / Article 20 Rule
    is_gdpr = any(w in text_lower for w in ["gdpr", "article 20", "data portability", "personal data export", "statutory window"])
    if is_gdpr:
        res["decision"] = "Escalate privacy compliance request"
        res["recommended_action"] = "Route to Compliance and Legal Operations with 30-day response SLA"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = True
        res["escalation_team"] = "compliance"
        res["safety_level"] = "restricted"
        res["next_actions"] = ["Verify requester identity", "Trigger data export task", "Deliver export within 30-day window"]
        
        faq_doc = None
        if rag_context:
            for r in rag_context:
                if "compliance_faq" in r.get("source_doc", "").lower() or "escalation_matrix" in r.get("source_doc", "").lower():
                    faq_doc = r
                    break
        
        if faq_doc:
            res["policy_sources_used"].append({
                "source_doc": faq_doc["source_doc"],
                "policy_ref": faq_doc["policy_ref"],
                "reason_used": "Compliance check of statutory timeline and routing rules for GDPR portability requests."
            })
            add_trace(1, "GDPR Article 20 data portability request detected.",
                      f"Verified statutory window of 30 days from policy {faq_doc['source_doc']}.",
                      "Route to compliance team, restrict automated replies.")
        else:
            add_trace(1, "GDPR Article 20 data portability request detected.",
                      "Requires validation of statutory response window and legal operations routing.",
                      "Route to compliance team, restrict automated replies.")
        return res

    # 6. SLA Outage / P0 / RCA Rule
    is_outage = any(w in text_lower for w in ["outage", "downtime", "rca", "sla breach", "p0", "down"])
    if is_outage:
        res["decision"] = "Escalate SLA breach risk"
        res["recommended_action"] = "Route to Support Lead and Engineering Manager; prepare RCA and SLA credit review"
        res["auto_reply_allowed"] = False  # By default false to prevent premature promises of credits/refunding
        res["requires_human_approval"] = True
        res["escalation_team"] = "support_engineering"
        res["safety_level"] = "restricted"
        res["next_actions"] = ["Notify On-Call Support Lead", "Open Root Cause Analysis incident log", "Assess downtime duration and SLA credits eligibility"]
        
        sla_doc = None
        if rag_context:
            for r in rag_context:
                if "sla_policy" in r.get("source_doc", "").lower():
                    sla_doc = r
                    break
                    
        if sla_doc:
            res["policy_sources_used"].append({
                "source_doc": sla_doc["source_doc"],
                "policy_ref": sla_doc["policy_ref"],
                "reason_used": "SLA policy check for downtime credit eligibility and RCA delivery timelines."
            })
            add_trace(1, "P0 Outage or SLA breach risk detected.",
                      f"SLA policy {sla_doc['source_doc']} requires written RCA within 24 hours of incident resolution.",
                      "Route to Support Lead & Eng Manager, restrict auto-replies to prevent unauthorized credit commitments.")
        else:
            add_trace(1, "P0 Outage or SLA breach risk detected.",
                      "Significant outage requires immediate response coordination and escalation.",
                      "Route to Support Lead & Eng Manager, restrict auto-replies.")
        return res

    # 7. Public Review / Churn Threat Rule
    is_review_threat = any(w in text_lower for w in ["g2", "capterra", "trustpilot", "twitter", "negative review", "public review", "reputation", "cancel", "refund"])
    if is_review_threat or status == "Escalated":
        res["decision"] = "Escalate reputation and retention risk"
        res["recommended_action"] = "Route to Customer Success Lead and Account Executive"
        res["auto_reply_allowed"] = False
        res["requires_human_approval"] = True
        res["escalation_team"] = "customer_success"
        res["safety_level"] = "restricted"
        res["next_actions"] = ["Notify Account Executive", "Flag churn risk in CRM", "Acknowledge frustration neutrally without liability"]
        
        refund_doc = None
        if rag_context:
            for r in rag_context:
                if "refund_policy" in r.get("source_doc", "").lower() or "escalation_matrix" in r.get("source_doc", "").lower():
                    refund_doc = r
                    break
                    
        if refund_doc:
            res["policy_sources_used"].append({
                "source_doc": refund_doc["source_doc"],
                "policy_ref": refund_doc["policy_ref"],
                "reason_used": "Referencing the refund policy and public review threat retention playbooks."
            })
            add_trace(1, "Public review or cancellation threat detected.",
                      f"Refund policy {refund_doc['source_doc']} triggers standard retention playbooks and forbids automatic refund commitments.",
                      "Route to CS Lead & Account Executive, restrict automated messages.")
        else:
            add_trace(1, "Public review or cancellation threat detected.",
                      "Threat of churn or public review requires personalized retention handling.",
                      "Route to CS Lead & Account Executive, restrict automated messages.")
        return res

    # 8. Pricing / Billing Inquiry Rule
    if category == "Billing" or any(w in text_lower for w in ["pricing", "discount", "bill", "invoice", "pro-rata", "seat"]):
        res["decision"] = "Prepare policy-grounded billing response"
        res["recommended_action"] = "Draft response using pricing/billing policy"
        res["auto_reply_allowed"] = True
        res["requires_human_approval"] = False
        res["escalation_team"] = "billing"
        res["safety_level"] = "safe"
        res["next_actions"] = ["Send drafted reply", "Log billing ticket"]
        
        pricing_doc = None
        if rag_context:
            for r in rag_context:
                if "pricing_policy" in r.get("source_doc", "").lower():
                    pricing_doc = r
                    break
                    
        if pricing_doc:
            res["policy_sources_used"].append({
                "source_doc": pricing_doc["source_doc"],
                "policy_ref": pricing_doc["policy_ref"],
                "reason_used": "Look up subscription pricing tiers and mid-cycle seat upgrade rules."
            })
            
            # Formulate short professional response
            if "pro-rata" in text_lower or "seat" in text_lower:
                res["draft_reply"] = (
                    "Thank you for contacting us. Regarding your pricing query, "
                    "additional seats added mid-cycle are billed on a pro-rata basis for the remaining days of the current billing month. "
                    "Please let us know if you would like us to apply the upgrade to your account."
                )
            else:
                res["draft_reply"] = (
                    "Thank you for contacting us. Our Pro Tier is priced at $79 per seat/month and includes core automation features. "
                    "We also offer a 30% discount for registered non-profit organizations. Let us know how you would like to proceed!"
                )
            
            add_trace(1, "Billing or pricing inquiry observed.",
                      f"Pricing policy {pricing_doc['source_doc']} details the subscription plans, seat additions, and NPO discounts.",
                      "Draft reply using policy parameters, set auto-reply to allowed.")
        else:
            res["draft_reply"] = "Thank you for contacting us. We will review your pricing request and get back to you shortly."
            add_trace(1, "Billing or pricing inquiry observed.",
                      "No matching pricing policy found in direct RAG context; drafting general acknowledgment.",
                      "Draft standard acknowledgment, set auto-reply to allowed.")
        return res

    # 9. API Docs / Bug Rule
    if category == "Bug Report" or any(w in text_lower for w in ["api", "403", "bug", "crash", "webhook", "v2"]):
        res["decision"] = "Prepare technical support response"
        res["recommended_action"] = "Draft response using API docs or route to support if unresolved"
        res["auto_reply_allowed"] = True
        res["requires_human_approval"] = False
        res["escalation_team"] = "technical_support"
        res["safety_level"] = "safe"
        res["next_actions"] = ["Verify header implementation", "Investigate diagnostic logs"]
        
        api_doc = None
        if rag_context:
            for r in rag_context:
                if "api_docs" in r.get("source_doc", "").lower():
                    api_doc = r
                    break
                    
        if api_doc:
            res["policy_sources_used"].append({
                "source_doc": api_doc["source_doc"],
                "policy_ref": api_doc["policy_ref"],
                "reason_used": "Referencing API documentation for header format parameters."
            })
            add_trace(1, "API integration issue or bug reported.",
                      f"API docs {api_doc['source_doc']} note that API v2 calls require the X-Workspace-ID header.",
                      "Draft technical reply specifying required headers, set auto-reply to allowed.")
            res["draft_reply"] = (
                "Thank you for reaching out. For calls made to the API v2 endpoints, please verify that you are "
                "passing the 'X-Workspace-ID' header with your requests. Let us know if you continue to experience errors."
            )
        else:
            add_trace(1, "API integration issue or bug reported.",
                      "Requires investigation of system logs and ticket routing to technical support.",
                      "Draft standard technical support acknowledgment.")
            res["draft_reply"] = "Thank you for your technical support inquiry. Our engineering team has been notified and is investigating the issue."
        return res

    # 10. Generic Inquiry Rule
    res["draft_reply"] = "Thank you for contacting us. A customer support representative will review your request and follow up shortly."
    add_trace(1, "Inquiry did not match any restricted or high-risk rules.",
              "General requests are routed to standard support with standard automated acknowledgments.",
              "Draft standard acknowledgment, set auto-reply to allowed.")
    res["next_actions"] = ["Assign ticket to general support queue"]
    return res

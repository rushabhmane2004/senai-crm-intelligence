from typing import Dict, Any, Optional

def classify_email_heuristically(sender: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Classifies an incoming email heuristically based on sender domain and body/subject keywords.
    Evaluation order is strict:
      1. Security
      2. Legal
      3. GDPR / Compliance legal
      4. Internal
      5. Spam
      6. P0 / Outage
      7. Reputation crisis / Churn
      8. Refund / Angry complaint
      9. Bug report
      10. Compliance
      11. Billing
      12. Pricing / Sales inquiry
      13. Feature request
      14. Default (Other)
    """
    sender_lower = sender.lower()
    text = f"{subject} {body}".lower()
    
    # Extract sender domain
    domain = sender_lower.split("@")[-1] if "@" in sender_lower else sender_lower

    # Base response dictionary structure
    result = {
        "category": "Other",
        "urgency": "Low",
        "priority_score": 20,
        "requires_human": False,
        "status": "Processing",
        "routing_queue": "general",
        "escalation_reason": None,
        "is_spam": False,
        "is_internal": False,
        "security_flag": False,
        "legal_flag": False
    }

    security_kws = [
        "ransomware", "exfiltrated", "publish the data", "dark web", "send 2 btc",
        "suspicious login", "unknown location", "valid credentials", "data breach",
        "stolen data"
    ]
    if any(kw in text for kw in security_kws) or ("breach" in text and "sla breach" not in text):
        result.update({
            "category": "Security",
            "urgency": "Critical",
            "priority_score": 100,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "security",
            "security_flag": True,
            "escalation_reason": "Critical security threat detected. Do not auto-reply."
        })
        return result

    # 2. Legal
    legal_kws = [
        "cease and desist", "legal action", "legal team", "formal correspondence",
        "attorney", "trademark", "lawsuit", "legal review"
    ]
    if any(kw in text for kw in legal_kws):
        result.update({
            "category": "Legal",
            "urgency": "Critical",
            "priority_score": 95,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "legal",
            "legal_flag": True,
            "escalation_reason": "Legal threat detected. Requires human/legal review."
        })
        return result

    # 3. GDPR / Compliance legal
    gdpr_kws = [
        "gdpr", "article 20", "data portability", "data export", "personal data",
        "statutory 30-day window"
    ]
    if any(kw in text for kw in gdpr_kws):
        result.update({
            "category": "Compliance",
            "urgency": "Critical",
            "priority_score": 95,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "compliance",
            "legal_flag": True,
            "escalation_reason": "Formal GDPR/compliance request detected. Requires compliance review."
        })
        return result

    # 4. Internal
    internal_domains = ["internal.com", "mycompany.com"]
    if any(domain == d or domain.endswith("." + d) for d in internal_domains):
        result.update({
            "category": "Internal",
            "urgency": "Low",
            "priority_score": 10,
            "requires_human": False,
            "status": "Ignored",
            "routing_queue": "internal",
            "is_internal": True
        })
        return result

    # 5. Spam
    spam_kws = [
        "boost your seo", "front page of google", "nigerian prince", "inheritance",
        "processing fee", "cold outreach", "quick question for the right person",
        "limited offer", "click here", "dear sir/madam", "collab opportunity"
    ]
    spam_domains = ["marketing-guru.io", "spammy-outreach.com", "wealth-transfer.com", "coldoutreach.com"]
    if any(kw in text for kw in spam_kws) or any(domain == d or domain.endswith("." + d) for d in spam_domains):
        result.update({
            "category": "Spam",
            "urgency": "Low",
            "priority_score": 5,
            "requires_human": False,
            "status": "Spam",
            "routing_queue": "spam",
            "is_spam": True
        })
        return result

    # 6. P0 / Outage
    outage_kws = [
        "p0", "production down", "production system down", "outage", "downtime",
        "sla breach", "root cause analysis", "rca"
    ]
    if any(kw in text for kw in outage_kws):
        result.update({
            "category": "Complaint",
            "urgency": "Critical",
            "priority_score": 90,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "support_lead",
            "escalation_reason": "Critical outage or SLA escalation detected."
        })
        return result

    # 7. Reputation crisis / churn
    reputation_kws = [
        "public review", "trustpilot", "g2", "capterra", "twitter",
        "cancelling my subscription", "leaving detailed negative reviews",
        "churn", "no human response", "final warning"
    ]
    if any(kw in text for kw in reputation_kws):
        result.update({
            "category": "Complaint",
            "urgency": "High",
            "priority_score": 85,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "customer_success",
            "escalation_reason": "Reputation or churn risk detected."
        })
        return result

    # 8. Refund / Angry complaint
    refund_kws = [
        "refund", "unhappy", "worst experience", "delete my account",
        "never use this again", "unacceptable service"
    ]
    if any(kw in text for kw in refund_kws):
        result.update({
            "category": "Complaint",
            "urgency": "High",
            "priority_score": 80,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "support",
            "escalation_reason": "High-risk customer complaint or refund request."
        })
        return result

    # 9. Bug report
    bug_kws = [
        "bug", "crashes", "server error 500", "failing silently", "data missing",
        "not working", "broken", "steps to reproduce"
    ]
    if any(kw in text for kw in bug_kws):
        result.update({
            "category": "Bug Report",
            "urgency": "Medium",
            "priority_score": 60,
            "requires_human": True,
            "status": "Processing",
            "routing_queue": "engineering_support"
        })
        return result

    # 10. Compliance
    compliance_kws = [
        "hipaa", "baa", "soc 2", "iso 27001", "compliance questionnaire", "data residency"
    ]
    if any(kw in text for kw in compliance_kws):
        result.update({
            "category": "Compliance",
            "urgency": "High",
            "priority_score": 75,
            "requires_human": True,
            "status": "Escalated",
            "routing_queue": "compliance"
        })
        return result

    # 11. Billing
    billing_kws = [
        "invoice", "billing", "payment failed", "overdue", "subscription renews",
        "pro-rata", "prorated"
    ]
    if any(kw in text for kw in billing_kws):
        result.update({
            "category": "Billing",
            "urgency": "Medium",
            "priority_score": 50,
            "requires_human": False,
            "status": "Processing",
            "routing_queue": "billing"
        })
        return result

    # 12. Pricing / sales inquiry
    sales_kws = [
        "pricing", "discount", "enterprise plan", "standard plan",
        "academic license", "reseller", "white-label", "rfp"
    ]
    if any(kw in text for kw in sales_kws):
        result.update({
            "category": "Inquiry",
            "urgency": "Medium",
            "priority_score": 45,
            "requires_human": False,
            "status": "Processing",
            "routing_queue": "sales"
        })
        return result

    # 13. Feature request
    feature_kws = [
        "feature request", "roadmap", "dark mode", "custom branding", "native ios app"
    ]
    if any(kw in text for kw in feature_kws):
        result.update({
            "category": "Feature Request",
            "urgency": "Low",
            "priority_score": 30,
            "requires_human": False,
            "status": "Processing",
            "routing_queue": "product"
        })
        return result

    # 14. Default (Other)
    return result

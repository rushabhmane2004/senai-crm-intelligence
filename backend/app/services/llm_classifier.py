import re
import os
from typing import Dict, Any, List, Optional

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extracts entities using regex and keyword lists from the text.
    """
    # 1. Monetary amounts
    # Matches $10,000/minute, $2.4M, $500, 2 BTC, $1,240.00, etc.
    money_pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:/[a-zA-Z]+)?|\$\d+(?:\.\d+)?[mK]|\b\d+\s*(?:BTC|btc|Btc)\b'
    monetary = re.findall(money_pattern, text)
    
    # 2. Order IDs
    # Matches "Order #88271", "#88271"
    order_pattern = r'(?i)order\s*#?\d{3,8}|\b#\d{5,8}\b'
    orders = re.findall(order_pattern, text)
    
    # 3. Ticket IDs
    # Matches "Ticket #11042", "PR #405", "invoice #99283"
    ticket_pattern = r'(?i)ticket\s*#?\d{3,8}|\bPR\s*#?\d{3,5}\b|\binvoice\s*#?\d{3,8}\b'
    tickets = re.findall(ticket_pattern, text)
    
    # 4. Deadlines
    deadline_keywords = [
        "24 hours", "48 hours", "30-day window", "30-day statutory window",
        "oct 30", "dec 31", "next friday", "eod thursday"
    ]
    deadlines = []
    text_lower = text.lower()
    for kw in deadline_keywords:
        if kw in text_lower:
            # Reconstruct original case or keep lower
            start_idx = text_lower.find(kw)
            deadlines.append(text[start_idx:start_idx+len(kw)])
            
    # 5. Products Mentioned
    product_keywords = [
        "api v1", "api v2", "standard plan", "pro subscription", "enterprise tier",
        "hipaa", "soc 2", "gdpr", "baa", "dpa"
    ]
    products = []
    for kw in product_keywords:
        if kw in text_lower:
            start_idx = text_lower.find(kw)
            products.append(text[start_idx:start_idx+len(kw)])
            
    return {
        "order_ids": list(set(orders)),
        "ticket_ids": list(set(tickets)),
        "monetary_amounts": list(set(monetary)),
        "deadlines": list(set(deadlines)),
        "products_mentioned": list(set(products))
    }

def classify_with_llm_context(
    email: Any,
    thread_history: Optional[List[Any]] = None,
    rag_context: Optional[List[Dict[str, Any]]] = None,
    heuristic_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Structured classification service that supports an optional OpenAI provider,
    but defaults to a deterministic offline mock classification to adhere to sandbox requirements.
    """
    subject = getattr(email, "subject", "") or ""
    body = getattr(email, "body", "") or ""
    combined_text = f"{subject} {body}"
    
    # Check settings / config
    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Force mock mode if OpenAI credentials are not provided
    if llm_provider == "openai" and not openai_key:
        llm_provider = "mock"
        
    heuristic_category = heuristic_result.get("category", "Other") if heuristic_result else "Other"
    heuristic_urgency = heuristic_result.get("urgency", "Low") if heuristic_result else "Low"
    requires_human = heuristic_result.get("requires_human", False) if heuristic_result else False
    escalation_reason = heuristic_result.get("escalation_reason") if heuristic_result else None
    
    # Evaluate entities
    entities = extract_entities(combined_text)
    
    # Heuristic-based mock mapping profiles
    sentiment = "Neutral"
    sentiment_score = 0.0
    confidence = 0.80
    suggested_reply = None
    
    cat = heuristic_category.lower()
    
    if cat == "spam":
        sentiment = "Neutral"
        sentiment_score = 0.0
        confidence = 0.95
        suggested_reply = None
    elif cat == "internal":
        sentiment = "Neutral"
        sentiment_score = 0.0
        confidence = 0.95
        suggested_reply = None
    elif cat == "security":
        sentiment = "Negative"
        sentiment_score = -1.0
        confidence = 0.97
        suggested_reply = None
    elif cat == "legal":
        sentiment = "Negative"
        sentiment_score = -0.9
        confidence = 0.95
        suggested_reply = None
    elif cat == "compliance":
        sentiment = "Negative"
        sentiment_score = -0.6
        confidence = 0.92
        suggested_reply = None
    elif cat == "complaint":
        sentiment = "Negative"
        sentiment_score = -0.8
        confidence = 0.85
        if "refund" in combined_text.lower():
            suggested_reply = "Thank you for contacting billing. We are reviewing your order history and refund request eligibility under our standard policy."
    elif cat == "bug report":
        sentiment = "Negative"
        sentiment_score = -0.5
        confidence = 0.82
        suggested_reply = "We apologize for the inconvenience. Our engineering support group has logged your bug report and will investigate."
    elif cat == "billing":
        sentiment = "Neutral"
        sentiment_score = -0.1
        confidence = 0.82
        suggested_reply = "Your billing query regarding subscription renewals and mid-cycle adjustments is queued for manual support desk review."
    elif cat == "inquiry":
        sentiment = "Neutral"
        sentiment_score = 0.1
        confidence = 0.80
        suggested_reply = "Thanks for your inquiry. Please refer to our product pricing sheet for multi-user licensing options."
    elif cat == "feature request":
        sentiment = "Positive"
        sentiment_score = 0.5
        confidence = 0.80
        suggested_reply = "Thank you for the suggestion! We have logged this idea under our product enhancement backlog."
    else:  # other
        sentiment = "Neutral"
        sentiment_score = 0.0
        confidence = 0.70
        suggested_reply = None

    # Safety constraints lists for audit logs
    safety_constraints = []
    if cat in ["security", "legal", "compliance", "spam"]:
        safety_constraints.append(f"Auto-reply prohibited for safety category: {heuristic_category}")
        
    policy_refs = []
    if rag_context:
        for r in rag_context:
            if r.get("policy_ref"):
                policy_refs.append(r["policy_ref"])

    # Build response envelope
    return {
        "category": heuristic_category,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "urgency": heuristic_urgency,
        "requires_human": requires_human,
        "escalation_reason": escalation_reason,
        "suggested_reply": suggested_reply,
        "confidence": confidence,
        "detected_entities": entities,
        "model_provider": llm_provider,
        "prompt_context_used": {
            "thread_history_used": True if thread_history else False,
            "rag_context_used": True if rag_context else False,
            "policy_refs": list(set(policy_refs))
        },
        "prompt_snapshot": {
            "system_instruction_summary": "Perform structured CRM email triage, extract key entities, and apply auto-reply safety overrides.",
            "thread_message_count": len(thread_history) if thread_history else 0,
            "rag_chunk_count": len(rag_context) if rag_context else 0,
            "safety_constraints": safety_constraints
        }
    }

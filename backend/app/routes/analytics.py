from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/sentiment-trend", status_code=status.HTTP_200_OK)
def get_sentiment_trend(
    sender: str = Query(None),
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    query = db.query(Email)
    if sender:
        query = query.filter(Email.sender.ilike(sender.strip()))
    
    # Calculate cutoff time based on the latest email timestamp for this query
    if sender:
        max_ts = db.query(func.max(Email.timestamp)).filter(Email.sender.ilike(sender.strip())).scalar()
    else:
        max_ts = db.query(func.max(Email.timestamp)).scalar()
        
    if not max_ts:
        max_ts = datetime.utcnow()
    cutoff_time = max_ts - timedelta(days=days)
    
    # Filter by date range and sort chronologically
    emails = query.filter(Email.timestamp >= cutoff_time).order_by(Email.timestamp.asc()).all()
    
    points = []
    for email in emails:
        # Resolve sentiment score with fallbacks
        score = None
        if email.sentiment_score is not None:
            score = email.sentiment_score
        elif email.raw_entities and isinstance(email.raw_entities, dict):
            llm_class = email.raw_entities.get("llm_classification")
            if isinstance(llm_class, dict):
                score = llm_class.get("sentiment_score")
        
        if score is None:
            category = email.category
            heuristics = {
                "security": -1.0,
                "legal": -0.9,
                "compliance": -0.6,
                "complaint": -0.8,
                "bug report": -0.5,
                "billing": -0.1,
                "inquiry": 0.1,
                "feature request": 0.5,
                "spam": 0.0,
                "internal": 0.0,
                "other": 0.0
            }
            score = heuristics.get((category or "").lower(), 0.0)
            
        points.append({
            "timestamp": email.timestamp.isoformat(),
            "message_id": email.message_id,
            "sender": email.sender,
            "category": email.category or "Other",
            "urgency": email.urgency or "Medium",
            "sentiment_score": score
        })
        
    # Calculate moving averages
    scores = [pt["sentiment_score"] for pt in points]
    for i in range(len(points)):
        window = scores[max(0, i - 2):i + 1]
        points[i]["moving_average"] = round(sum(window) / len(window), 3)
        
    # Sentiment deterioration detection: 3+ consecutive negative emails (sentiment_score < -0.4)
    consecutive_negative = 0
    deterioration_detected = False
    for pt in points:
        if pt["sentiment_score"] < -0.4:
            consecutive_negative += 1
            if consecutive_negative >= 3:
                deterioration_detected = True
        else:
            consecutive_negative = 0
            
    latest_moving_average = points[-1]["moving_average"] if points else None
    
    return {
        "sender": sender,
        "days": days,
        "total_points": len(points),
        "points": points,
        "deterioration_detected": deterioration_detected,
        "deterioration_reason": "3 consecutive negative emails detected" if deterioration_detected else None,
        "latest_moving_average": latest_moving_average
    }

@router.get("/category-breakdown", status_code=status.HTTP_200_OK)
def get_category_breakdown(db: Session = Depends(get_db)):
    total = db.query(Email).count()
    if total == 0:
        return {
            "total": 0,
            "categories": []
        }
        
    results = db.query(Email.category, func.count(Email.id)).group_by(Email.category).all()
    
    categories_dict = {}
    for category, count in results:
        cat_name = category if category else "Other"
        categories_dict[cat_name] = categories_dict.get(cat_name, 0) + count
        
    categories_list = []
    for cat_name, count in categories_dict.items():
        percentage = round((count / total) * 100, 2)
        categories_list.append({
            "category": cat_name,
            "count": count,
            "percentage": percentage
        })
        
    # Sort categories by count descending
    categories_list.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total": total,
        "categories": categories_list
    }

@router.get("/risk-summary", status_code=status.HTTP_200_OK)
def get_risk_summary(db: Session = Depends(get_db)):
    emails = db.query(Email).all()
    total_emails = len(emails)
    
    critical_count = 0
    escalated_count = 0
    spam_count = 0
    auto_reply_allowed_count = 0
    
    for email in emails:
        urg = (email.urgency or "").lower()
        if urg == "critical":
            critical_count += 1
            
        status_val = (email.status or "").lower()
        if status_val == "escalated":
            escalated_count += 1
            
        cat = (email.category or "").lower()
        if cat == "spam" or status_val == "spam":
            spam_count += 1
            
        raw = email.raw_entities or {}
        if raw.get("auto_reply_allowed") is True:
            auto_reply_allowed_count += 1
            
    auto_reply_blocked_count = total_emails - auto_reply_allowed_count
    
    # Top at risk senders
    from collections import defaultdict
    emails_by_sender = defaultdict(list)
    for email in emails:
        emails_by_sender[email.sender].append(email)
        
    top_at_risk = []
    for sender, sender_emails in emails_by_sender.items():
        # Sort chronologically
        sender_emails.sort(key=lambda x: x.timestamp)
        
        # Calculate sentiment scores
        scores = []
        urgencies = []
        for e in sender_emails:
            score = None
            if e.sentiment_score is not None:
                score = e.sentiment_score
            elif e.raw_entities and isinstance(e.raw_entities, dict):
                llm_class = e.raw_entities.get("llm_classification")
                if isinstance(llm_class, dict):
                    score = llm_class.get("sentiment_score")
            
            if score is None:
                category = e.category
                heuristics = {
                    "security": -1.0,
                    "legal": -0.9,
                    "compliance": -0.6,
                    "complaint": -0.8,
                    "bug report": -0.5,
                    "billing": -0.1,
                    "inquiry": 0.1,
                    "feature request": 0.5,
                    "spam": 0.0,
                    "internal": 0.0,
                    "other": 0.0
                }
                score = heuristics.get((category or "").lower(), 0.0)
                
            scores.append(score)
            if e.urgency:
                urgencies.append(e.urgency)
                
        # Consecutive check: 3+ with score < -0.4
        consecutive = 0
        det_detected = False
        for s in scores:
            if s < -0.4:
                consecutive += 1
                if consecutive >= 3:
                    det_detected = True
            else:
                consecutive = 0
                
        # Highest urgency
        urgency_map = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
        highest_urgency_str = "Low"
        highest_urgency_val = 0
        for u in urgencies:
            u_lower = u.lower()
            if urgency_map.get(u_lower, 0) > highest_urgency_val:
                highest_urgency_val = urgency_map[u_lower]
                highest_urgency_str = u
                
        latest_sentiment_score = scores[-1] if scores else 0.0
        
        # Include sender in top_at_risk if det_detected is True OR latest_sentiment_score < 0.0
        if det_detected or latest_sentiment_score < 0.0:
            top_at_risk.append({
                "sender": sender,
                "message_count": len(sender_emails),
                "latest_sentiment_score": latest_sentiment_score,
                "deterioration_detected": det_detected,
                "highest_urgency": highest_urgency_str if urgencies else "Low"
            })
            
    # Sort top_at_risk senders by:
    # 1. deterioration_detected (True first)
    # 2. latest_sentiment_score (lowest first)
    # 3. message_count (highest first)
    top_at_risk.sort(key=lambda x: (not x["deterioration_detected"], x["latest_sentiment_score"], -x["message_count"]))
    
    return {
        "total_emails": total_emails,
        "critical_count": critical_count,
        "escalated_count": escalated_count,
        "spam_count": spam_count,
        "auto_reply_allowed_count": auto_reply_allowed_count,
        "auto_reply_blocked_count": auto_reply_blocked_count,
        "top_at_risk_senders": top_at_risk
    }


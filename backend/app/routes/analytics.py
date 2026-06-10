from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/category-breakdown", status_code=status.HTTP_200_OK)
def get_category_breakdown(db: Session = Depends(get_db)):
    results = db.query(Email.category, func.count(Email.id)).group_by(Email.category).all()
    
    breakdown = {}
    for category, count in results:
        key = category if category else "Other"
        breakdown[key] = count
        
    return breakdown

@router.get("/sentiment-trend", status_code=status.HTTP_200_OK)
def get_sentiment_trend(sender: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    emails = db.query(Email).filter(Email.sender.ilike(sender.strip())).order_by(Email.timestamp.asc()).all()
    
    trend = []
    for email in emails:
        score = email.sentiment_score
        
        # If sentiment_score is not populated, use category/urgency derived heuristics
        if score is None:
            urgency = (email.urgency or "").lower()
            category = (email.category or "").lower()
            
            if urgency == "critical":
                score = -0.8
            elif urgency == "high":
                score = -0.5
            elif "complaint" in category or "issue" in category:
                score = -0.4
            elif "spam" in category:
                score = -0.2
            elif urgency == "medium":
                score = -0.1
            elif "billing" in category or "pricing" in category:
                score = 0.2
            else:
                score = 0.0
                
        trend.append({
            "message_id": email.message_id,
            "timestamp": email.timestamp,
            "sentiment_score": score,
            "category": email.category,
            "urgency": email.urgency
        })
        
    return {
        "sender": sender,
        "data_points_count": len(trend),
        "trend_type": "heuristic_sentiment_score",
        "trend": trend
    }

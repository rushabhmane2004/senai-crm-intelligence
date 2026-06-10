from fastapi import APIRouter, Query, status

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/reputation", status_code=status.HTTP_200_OK)
def get_company_reputation(company: str = Query(..., min_length=1)):
    company_lower = company.lower().strip()
    
    # Check if company matches Karen scenario / Retail-Co profiles
    if "retail-co" in company_lower or "retail_co" in company_lower or "karen" in company_lower:
        return {
            "company": company,
            "reputation_source": "Trustpilot / G2 Meta-Scraping Engine (Cached)",
            "average_rating": 1.8,
            "review_count": 42,
            "verdict": "high-risk-public-churn-threat",
            "details": "Customer Karen escalation detected. Highly critical negative ratings registered regarding pro-rata billing disputes and refund eligibility rules. High risk of immediate churn and public forum brand damage.",
            "is_mock": True,
            "is_live": False
        }
        
    # Standard graceful fallback
    return {
        "company": company,
        "reputation_source": "System Offline Database Cache",
        "average_rating": 4.2,
        "review_count": 115,
        "verdict": "standard-satisfactory-profile",
        "details": "Standard satisfactory customer reputation rating. No public escalations or churn indicators found in offline cache.",
        "is_mock": True,
        "is_live": False
    }

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.web_intelligence import get_reputation_intelligence

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/reputation", status_code=status.HTTP_200_OK)
def get_company_reputation(
    company: str = Query(..., min_length=1, description="Company name or domain, e.g. retail-co.com"),
    db: Session = Depends(get_db),
):
    """
    Return cached offline public reputation intelligence for a company/domain.

    - **scraping_mode**: always "offline_mock" in this safe evaluation build.
    - **robots_checked**: always True — robots.txt compliance intent is preserved.
    - **cache_status**: "hit" if served from DB cache, "miss" on first fetch, "fallback" on error.
    - **expires_at**: cache record expires 6 hours after creation.

    Live scraping can be enabled later by swapping `get_reputation_intelligence` for
    a live implementation while keeping the same response schema.
    """
    result = get_reputation_intelligence(company.strip(), db)
    return result

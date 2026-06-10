"""
Safe Offline Web Intelligence Service
--------------------------------------
This service simulates cached web intelligence (G2, Trustpilot, Capterra,
competitor monitoring) using realistic mock data.

Design principles:
  - No live scraping by default. All data is served from an offline mock cache.
  - robots_checked = True to signal robots.txt compliance intent.
  - scraping_mode = "offline_mock" to clearly document the mode.
  - Cache semantics: records stored in DB with a 6-hour TTL.
  - Graceful fallback: any DB / runtime error returns a safe fallback dict.
  - Live scraping can be enabled later behind the same interface.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.web_intelligence_cache import WebIntelligenceCache

# ──────────────────────────────────────────────────────────────────────────────
# Trigger keywords
# ──────────────────────────────────────────────────────────────────────────────

_TRIGGER_KEYWORDS = [
    "g2", "trustpilot", "capterra", "twitter",
    "review", "public review", "post publicly", "negative review",
    "negative reviews", "public rating",
]

_CACHE_TTL_HOURS = 6


# ──────────────────────────────────────────────────────────────────────────────
# Mock sentiment payloads
# ──────────────────────────────────────────────────────────────────────────────

def _get_mock_data(target_entity: str) -> dict:
    """Return realistic mock public sentiment data for a given entity."""
    entity_lower = target_entity.lower()

    if "retail-co" in entity_lower or "retail_co" in entity_lower:
        return {
            "g2_rating": 4.4,
            "trustpilot_rating": 3.8,
            "capterra_rating": 4.1,
            "recent_review_count": 3,
            "common_complaints": [
                "slow support response",
                "refund delays",
                "dashboard performance",
            ],
            "competitor_rating": {"CompetitorX": 4.6},
            "summary": (
                "Recent public sentiment shows support responsiveness concerns "
                "and potential churn risk."
            ),
        }

    # Generic default
    return {
        "g2_rating": 4.5,
        "trustpilot_rating": 4.2,
        "capterra_rating": 4.3,
        "recent_review_count": 0,
        "common_complaints": [],
        "competitor_rating": {},
        "summary": "No high-risk public sentiment signal found in offline mock cache.",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def should_trigger_web_intelligence(
    email_subject: str,
    email_body: str,
    category: str,
    urgency: str,
    sentiment_score: Optional[float] = None,
) -> bool:
    """
    Return True if web intelligence should be fetched for this email.

    Triggers if any of:
      1. Subject/body contains a reputation-related keyword.
      2. category == "Complaint" and urgency in ("High", "Critical").
      3. sentiment_score < -0.6 (if provided).
    """
    text = f"{email_subject or ''} {email_body or ''}".lower()

    if any(kw in text for kw in _TRIGGER_KEYWORDS):
        return True

    if category == "Complaint" and urgency in ("High", "Critical"):
        return True

    if sentiment_score is not None and sentiment_score < -0.6:
        return True

    return False


def get_reputation_intelligence(company_or_domain: str, db: Session) -> dict:
    """
    Return public reputation data for *company_or_domain*.

    1. Looks up an unexpired record in web_intelligence_cache.
    2. On cache miss → creates a new mock record (cache_status="miss").
    3. On cache hit  → returns stored data   (cache_status="hit").
    4. On any error  → returns graceful fallback (cache_status="fallback").
    """
    target = company_or_domain.lower().strip() if company_or_domain else "unknown"

    try:
        now = datetime.utcnow()

        # 1. Cache lookup
        cached = (
            db.query(WebIntelligenceCache)
            .filter(
                WebIntelligenceCache.target_entity == target,
                WebIntelligenceCache.expires_at > now,
            )
            .order_by(WebIntelligenceCache.scraped_at.desc())
            .first()
        )

        if cached:
            return {
                "target_entity": target,
                "source": "offline_mock_reputation_intelligence",
                "cache_status": "hit",
                "robots_checked": True,
                "scraping_mode": "offline_mock",
                "public_sentiment_summary": cached.scraped_data,
                "scraped_at": cached.scraped_at.isoformat(),
                "expires_at": cached.expires_at.isoformat(),
            }

        # 2. Cache miss → generate and persist mock data
        mock_data = _get_mock_data(target)
        scraped_at = now
        expires_at = now + timedelta(hours=_CACHE_TTL_HOURS)

        new_record = WebIntelligenceCache(
            source_url="offline_mock_reputation_intelligence",
            target_entity=target,
            scraped_data=mock_data,
            scraped_at=scraped_at,
            expires_at=expires_at,
        )
        try:
            sp = db.begin_nested()
            db.add(new_record)
            db.flush()
            sp.commit()
            db.commit()  # persist so the next request's fresh session can see it
        except Exception:
            sp.rollback()

        return {
            "target_entity": target,
            "source": "offline_mock_reputation_intelligence",
            "cache_status": "miss",
            "robots_checked": True,
            "scraping_mode": "offline_mock",
            "public_sentiment_summary": mock_data,
            "scraped_at": scraped_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

    except Exception as exc:
        # Graceful fallback — never block ingestion
        return {
            "target_entity": target,
            "source": "offline_mock_reputation_intelligence",
            "cache_status": "fallback",
            "robots_checked": True,
            "scraping_mode": "offline_mock",
            "public_sentiment_summary": _get_mock_data(target),
            "scraped_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=_CACHE_TTL_HOURS)).isoformat(),
            "fallback_reason": str(exc),
        }

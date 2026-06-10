from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contact import Contact
from app.models.thread import Thread
from app.models.email import Email
from app.schemas.email import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # 1. Total emails count
    total_emails = db.query(Email).count()

    # 2. Pending emails count (Status: Received or Processing)
    pending_emails = db.query(Email).filter(Email.status.in_(["Received", "Processing"])).count()

    # 3. Spam emails count (Category is Spam or Status is Spam)
    spam_emails = db.query(Email).filter((Email.category == "Spam") | (Email.status == "Spam")).count()

    # 4. Escalated emails count (Status: Escalated)
    escalated_emails = db.query(Email).filter(Email.status == "Escalated").count()

    # 5. Critical emails count (Urgency is Critical)
    critical_emails = db.query(Email).filter(Email.urgency == "Critical").count()

    # 6. Total contacts count
    total_contacts = db.query(Contact).count()

    # 7. Total threads count
    total_threads = db.query(Thread).count()

    return DashboardStatsResponse(
        total_emails=total_emails,
        pending_emails=pending_emails,
        spam_emails=spam_emails,
        escalated_emails=escalated_emails,
        critical_emails=critical_emails,
        total_contacts=total_contacts,
        total_threads=total_threads
    )

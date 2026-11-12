from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Invoice
from app.schemas.schemas import DashboardStats, InvoiceSummary

router = APIRouter()


@router.get("/", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.upload_time.desc()).all()

    total = len(invoices)
    approved = sum(1 for i in invoices if i.final_status == "approved")
    needs_review = sum(1 for i in invoices if i.final_status == "needs_review")
    flagged = sum(1 for i in invoices if i.final_status == "rejected")

    recent = invoices[:10]

    return DashboardStats(
        total_processed=total,
        approved=approved,
        needs_review=needs_review,
        flagged=flagged,
        recent_invoices=[InvoiceSummary.model_validate(i) for i in recent],
    )

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models.models import PurchaseOrder
from app.schemas.schemas import PurchaseOrderOut

router = APIRouter()


@router.get("/", response_model=List[PurchaseOrderOut])
def list_purchase_orders(db: Session = Depends(get_db)):
    return db.query(PurchaseOrder).options(joinedload(PurchaseOrder.line_items)).all()


@router.get("/{po_number}", response_model=PurchaseOrderOut)
def get_purchase_order(po_number: str, db: Session = Depends(get_db)):
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.line_items))
        .filter(PurchaseOrder.po_number == po_number)
        .first()
    )

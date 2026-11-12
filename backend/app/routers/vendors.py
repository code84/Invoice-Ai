from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Vendor
from app.schemas.schemas import VendorOut

router = APIRouter()


@router.get("/", response_model=List[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: str, db: Session = Depends(get_db)):
    return db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()

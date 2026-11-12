"""
Demo Reset Script
=================
Run this before EVERY demo / interview to get a clean database state.
Clears all invoices, runs, and audit events.
Resets PO balances.
Keeps vendor master and POs intact.

Usage:  python reset_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models.models import (
    AuditEvent, ValidationResult, ProcessingStage,
    ProcessingRun, Invoice, PurchaseOrder
)
import shutil

def reset():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Resetting database for demo...")

    # 1. Clear all processing data (order matters for FK constraints)
    deleted = {}
    deleted["AuditEvents"]       = db.query(AuditEvent).delete()
    deleted["ValidationResults"] = db.query(ValidationResult).delete()
    deleted["ProcessingStages"]  = db.query(ProcessingStage).delete()
    deleted["ProcessingRuns"]    = db.query(ProcessingRun).delete()
    deleted["Invoices"]          = db.query(Invoice).delete()
    db.commit()

    # 2. Reset PO invoiced amounts and remaining balances
    pos = db.query(PurchaseOrder).all()
    for po in pos:
        po.invoiced_amount   = 0.0
        po.remaining_balance = po.total_amount
    db.commit()
    deleted["POs reset"] = len(pos)

    # 3. Clear uploaded files (keep test_invoices folder intact)
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            fp = os.path.join(upload_dir, f)
            if os.path.isfile(fp):
                os.remove(fp)
        deleted["Uploaded files cleared"] = True

    db.close()

    print("\nReset complete:")
    for k, v in deleted.items():
        print(f"  {k}: {v}")

    print("\nDatabase is clean and ready for the demo.")
    print("\nTest invoices available at: test_invoices/")
    print("  happy_path          -> test_invoices/invoice_happy_path.pdf")
    print("  EC-01 Duplicate     -> test_invoices/ec01_duplicate.pdf")
    print("  EC-02 Missing #     -> test_invoices/ec02_missing_number.pdf")
    print("  EC-03 PO Mismatch   -> test_invoices/ec03_po_mismatch.pdf")
    print("  EC-04 Poor Scan     -> test_invoices/ec04_poor_scan.pdf")

if __name__ == "__main__":
    reset()

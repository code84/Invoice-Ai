"""
Phase 4 end-to-end test — runs all 4 key scenarios and prints results.
"""
import os, shutil, uuid
from app.database import SessionLocal
from app.models.models import Invoice, ProcessingStage, ValidationResult
from app.services.run_manager import create_run
from app.services.pipeline import process_invoice

SCENARIOS = [
    ("Happy path",        "test_invoices/invoice_happy_path.pdf"),
    ("Missing inv num",   "test_invoices/invoice_missing_number.pdf"),
    ("PO mismatch",       "test_invoices/invoice_po_mismatch.pdf"),
    ("Inactive vendor",   "test_invoices/invoice_inactive_vendor.pdf"),
]

def run_scenario(label, src):
    db = SessionLocal()
    dst = f"uploads/test_{uuid.uuid4().hex}.pdf"
    shutil.copy(src, dst)

    invoice = Invoice(
        id=str(uuid.uuid4()),
        filename=os.path.basename(src),
        file_path=dst,
        file_size=os.path.getsize(dst),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    run = create_run(invoice.id, db)
    process_invoice(invoice, run, db)
    db.refresh(invoice)

    print(f"\n{'='*65}")
    print(f"SCENARIO: {label}")
    print(f"{'='*65}")
    print(f"  Status        : {invoice.final_status}")
    print(f"  Vendor        : {invoice.vendor_name}")
    print(f"  Invoice #     : {invoice.invoice_number}")
    print(f"  Total         : {invoice.total}")
    print(f"  PO matched    : {invoice.matched_po_id is not None}")
    print(f"  Is duplicate  : {invoice.is_duplicate}")
    print(f"  Confidence    : {invoice.extraction_confidence}")
    print(f"\n  Decision:")
    for line in (invoice.decision_explanation or "").split("\n"):
        print(f"    {line}")
    print(f"\n  Action: {invoice.recommended_action}")

    # Show triggered rules only
    rules = (
        db.query(ValidationResult)
        .filter_by(run_id=run.id)
        .filter(ValidationResult.check_name.like("R%"))
        .all()
    )
    triggered = [r for r in rules if r.result == "failed"]
    if triggered:
        print(f"\n  Triggered rules ({len(triggered)}):")
        for r in triggered:
            print(f"    • {r.check_name}: {r.message[:80]}")

    db.close()

for label, src in SCENARIOS:
    try:
        run_scenario(label, src)
    except Exception as e:
        print(f"\nSCENARIO {label} ERROR: {e}")
        import traceback; traceback.print_exc()

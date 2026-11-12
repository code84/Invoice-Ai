"""Test the duplicate invoice scenario"""
from app.database import SessionLocal
from app.models.models import Invoice, ProcessingRun, ProcessingStage
from app.services.run_manager import create_run
from app.services.pipeline import process_invoice
import uuid, os, shutil

db = SessionLocal()

# Submit the same invoice a second time (EC-01 duplicate)
src = 'test_invoices/invoice_duplicate.pdf'
dst = 'uploads/test_duplicate.pdf'
shutil.copy(src, dst)

invoice = Invoice(
    id=str(uuid.uuid4()),
    filename='invoice_duplicate.pdf',
    file_path=dst,
    file_size=os.path.getsize(dst),
)
db.add(invoice)
db.commit()
db.refresh(invoice)

run = create_run(invoice.id, db)
process_invoice(invoice, run, db)

db.refresh(invoice)
print('Duplicate test result:')
print('  Is duplicate:', invoice.is_duplicate)
print('  Duplicate of:', invoice.duplicate_of_id)
print('  Final status:', invoice.final_status)

stages = db.query(ProcessingStage).filter_by(run_id=run.id).order_by(ProcessingStage.order_index).all()
for s in stages:
    if s.stage_name == 'duplicate':
        print('  Duplicate stage:', s.output_summary)

db.close()

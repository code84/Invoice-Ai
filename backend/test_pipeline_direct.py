from app.database import SessionLocal
from app.models.models import Invoice, ProcessingRun, ProcessingStage
from app.services.run_manager import create_run
from app.services.pipeline import process_invoice
import uuid, os, shutil

db = SessionLocal()

src = 'test_invoices/invoice_happy_path.pdf'
dst = 'uploads/test_happy_path_2.pdf'
shutil.copy(src, dst)

invoice = Invoice(
    id=str(uuid.uuid4()),
    filename='invoice_happy_path.pdf',
    file_path=dst,
    file_size=os.path.getsize(dst),
)
db.add(invoice)
db.commit()
db.refresh(invoice)
print('Invoice created:', invoice.id)

run = create_run(invoice.id, db)
print('Run created:', run.run_id)

try:
    process_invoice(invoice, run, db)
    print('Pipeline complete. Run status:', run.status)
except Exception as e:
    import traceback
    traceback.print_exc()

db.refresh(run)
stages = db.query(ProcessingStage).filter_by(run_id=run.id).order_by(ProcessingStage.order_index).all()
for s in stages:
    summary = (s.output_summary or '')[:70]
    err = (s.error_message or '')[:70]
    print(f'  {s.stage_label:28s} -> {s.status:10s} | {summary or err}')

db.refresh(invoice)
print()
print('Invoice final_status:', invoice.final_status)
print('Vendor name extracted:', invoice.vendor_name)
print('Invoice number:', invoice.invoice_number)
print('Total:', invoice.total)
print('Matched PO:', invoice.matched_po_id)
print('Is duplicate:', invoice.is_duplicate)

db.close()

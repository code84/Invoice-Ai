from app.database import SessionLocal
from app.models.models import Invoice
from app.services.duplicate_detector import check_duplicate

db = SessionLocal()
existing = db.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-001').first()
vid = existing.matched_vendor_id

cases = [
    ('Exact duplicate',             'INV-2026-001', 53100.0, '2026-11-10'),
    ('Different inv# same vendor',  'INV-2026-003', 82600.0, '2026-11-08'),
    ('OCR noise + same amt+date',   'INV-2O26-001', 53100.0, '2026-11-10'),
    ('Same inv# different amount',  'INV-2026-001', 99999.0, '2026-11-10'),
]

for label, inv_num, total, date in cases:
    r = check_duplicate('ABC Technologies Pvt Ltd', vid, inv_num, total, date, 'new-id', db)
    dup = r['is_duplicate']
    pos = r['possible_duplicate']
    msg = r['message'][:100]
    print(f'{label}:')
    print(f'  is_duplicate={dup}  possible_duplicate={pos}')
    print(f'  {msg}')
    print()

db.close()

"""Prove the duplicate logic with numbers that have never been processed."""
from app.database import SessionLocal
from app.models.models import Invoice
from app.services.duplicate_detector import check_duplicate

db = SessionLocal()
existing = db.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-001').first()
vid = existing.matched_vendor_id

cases = [
    # Fresh numbers never in the DB
    ('Fresh new invoice',            'INV-2026-099', 15000.0,  '2026-11-15'),
    ('Different vendor same number', 'INV-2026-001', 53100.0,  '2026-11-10'),  # diff vendor
    ('OCR noise same amt+date',      'INV-2O26-001', 53100.0,  '2026-11-10'),  # OCR: O vs 0
    ('OCR noise diff date',          'INV-2O26-001', 53100.0,  '2026-11-11'),  # diff date
]

vendors = ['XYZ Corp', 'ABC Technologies Pvt Ltd', 'ABC Technologies Pvt Ltd', 'ABC Technologies Pvt Ltd']

for (label, inv_num, total, date), vname in zip(cases, vendors):
    r = check_duplicate(vname, vid if vname != 'XYZ Corp' else None,
                        inv_num, total, date, 'brand-new-id', db)
    dup = r['is_duplicate']
    pos = r['possible_duplicate']
    print(f'{label}:')
    print(f'  is_duplicate={dup}  possible_duplicate={pos}')
    print(f'  {r["message"][:110]}')
    print()

db.close()

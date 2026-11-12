"""
Seed the database with vendor master data and purchase orders.
Run this once: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.models.models import Vendor, PurchaseOrder, PurchaseOrderLineItem
import uuid


def generate_uuid():
    return str(uuid.uuid4())


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing seed data
    db.query(PurchaseOrderLineItem).delete()
    db.query(PurchaseOrder).delete()
    db.query(Vendor).delete()
    db.commit()

    # ── Vendors ──────────────────────────────────────────────────────────────
    vendors = [
        Vendor(
            id=generate_uuid(),
            vendor_id="V001",
            legal_name="ABC Technologies Pvt Ltd",
            aliases=["ABC Technologies", "ABC Tech", "ABC Technologies Pvt. Ltd.", "ABC Tech Pvt Ltd"],
            tax_id="TEST-TAX-001",
            status="approved",
            is_approved=True,
            currency="INR",
            country="IN",
        ),
        Vendor(
            id=generate_uuid(),
            vendor_id="V002",
            legal_name="XYZ Solutions Pvt Ltd",
            aliases=["XYZ Solutions", "XYZ Sol", "XYZ Solutions Ltd"],
            tax_id="TEST-TAX-002",
            status="approved",
            is_approved=True,
            currency="INR",
            country="IN",
        ),
        Vendor(
            id=generate_uuid(),
            vendor_id="V003",
            legal_name="Global Services Inc",
            aliases=["Global Services", "Global Svc", "Global Services Incorporated"],
            tax_id="TEST-TAX-003",
            status="inactive",
            is_approved=False,
            currency="INR",
            country="IN",
        ),
        Vendor(
            id=generate_uuid(),
            vendor_id="V004",
            legal_name="Northstar Systems Ltd",
            aliases=["Northstar Systems", "Northstar", "Northstar Sys"],
            tax_id="TEST-TAX-004",
            status="approved",
            is_approved=True,
            currency="INR",
            country="IN",
        ),
        Vendor(
            id=generate_uuid(),
            vendor_id="V005",
            legal_name="Pinnacle Consulting Group",
            aliases=["Pinnacle Consulting", "Pinnacle Group", "PCG"],
            tax_id="TEST-TAX-005",
            status="approved",
            is_approved=True,
            currency="INR",
            country="IN",
        ),
        Vendor(
            id=generate_uuid(),
            vendor_id="V006",
            legal_name="Northwind Office Supplies Pvt. Ltd.",
            aliases=["Northwind Office Supplies", "Northwind", "Northwind Office",
                     "Northwind Office Supplies Pvt Ltd"],
            tax_id="05AABCN1234F1Z5",
            status="approved",
            is_approved=True,
            currency="USD",
            country="IN",
        ),
    ]

    db.add_all(vendors)
    db.commit()
    for v in vendors:
        db.refresh(v)

    # ── Purchase Orders ───────────────────────────────────────────────────────
    pos = [
        # V001 — ABC Technologies (two POs)
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10045",
            vendor_id=vendors[0].id,
            po_date="2026-10-01",
            status="approved",
            currency="INR",
            total_amount=53100.00,
            invoiced_amount=0.00,
            remaining_balance=53100.00,
            description="Software subscription and implementation services",
        ),
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10048",
            vendor_id=vendors[0].id,
            po_date="2026-10-15",
            status="approved",
            currency="INR",
            total_amount=120000.00,
            invoiced_amount=0.00,
            remaining_balance=120000.00,
            description="Annual maintenance contract",
        ),
        # V002 — XYZ Solutions
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10046",
            vendor_id=vendors[1].id,
            po_date="2026-10-05",
            status="approved",
            currency="INR",
            total_amount=25000.00,
            invoiced_amount=0.00,
            remaining_balance=25000.00,
            description="Network infrastructure supplies",
        ),
        # V003 — Global Services (inactive PO)
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10047",
            vendor_id=vendors[2].id,
            po_date="2026-09-20",
            status="inactive",
            currency="INR",
            total_amount=75000.00,
            invoiced_amount=0.00,
            remaining_balance=75000.00,
            description="Consulting services",
        ),
        # V004 — Northstar Systems
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10049",
            vendor_id=vendors[3].id,
            po_date="2026-10-20",
            status="approved",
            currency="INR",
            total_amount=26500.00,
            invoiced_amount=0.00,
            remaining_balance=26500.00,
            description="Hardware procurement",
        ),
        # V005 — Pinnacle Consulting (split invoice PO — large amount)
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-10050",
            vendor_id=vendors[4].id,
            po_date="2026-10-25",
            status="approved",
            currency="INR",
            total_amount=180000.00,
            invoiced_amount=90000.00,          # already partially invoiced
            remaining_balance=90000.00,
            description="Strategic consulting — Phase 1 & Phase 2",
        ),
        # V006 — Northwind Office Supplies (USD, office supplies PO)
        PurchaseOrder(
            id=generate_uuid(),
            po_number="PO-2026-1093",
            vendor_id=vendors[5].id,
            po_date="2026-10-28",
            status="approved",
            currency="USD",
            total_amount=4900.00,
            invoiced_amount=0.00,
            remaining_balance=4900.00,
            description="Office supplies and stationery — Q4 2026",
        ),
    ]

    db.add_all(pos)
    db.commit()
    for po in pos:
        db.refresh(po)

    # ── PO Line Items ─────────────────────────────────────────────────────────
    line_items = [
        # PO-10045 — ABC Technologies
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[0].id, description="Software subscription (annual)", quantity=1, unit_price=45000.00, amount=45000.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[0].id, description="GST 18%", quantity=1, unit_price=8100.00, amount=8100.00),

        # PO-10048 — ABC Technologies (maintenance)
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[1].id, description="Annual maintenance contract", quantity=1, unit_price=101694.92, amount=101694.92),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[1].id, description="GST 18%", quantity=1, unit_price=18305.08, amount=18305.08),

        # PO-10046 — XYZ Solutions
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[2].id, description="Network switch (24-port)", quantity=2, unit_price=8000.00, amount=16000.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[2].id, description="Ethernet patch cables (box)", quantity=5, unit_price=1000.00, amount=5000.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[2].id, description="GST 18%", quantity=1, unit_price=4000.00, amount=4000.00),

        # PO-10047 — Global Services
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[3].id, description="Consulting services", quantity=100, unit_price=635.59, amount=63559.32),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[3].id, description="GST 18%", quantity=1, unit_price=11440.68, amount=11440.68),

        # PO-10049 — Northstar Systems
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[4].id, description="Server rack unit", quantity=1, unit_price=22457.63, amount=22457.63),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[4].id, description="GST 18%", quantity=1, unit_price=4042.37, amount=4042.37),

        # PO-10050 — Pinnacle Consulting
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[5].id, description="Strategic consulting Phase 1", quantity=1, unit_price=76271.19, amount=76271.19),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[5].id, description="Strategic consulting Phase 2", quantity=1, unit_price=76271.19, amount=76271.19),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[5].id, description="GST 18%", quantity=1, unit_price=27457.62, amount=27457.62),

        # PO-2026-1093 — Northwind Office Supplies (USD)
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Copier paper", quantity=1, unit_price=540.00, amount=540.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Ballpoint pens", quantity=1, unit_price=350.00, amount=350.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Office chair", quantity=1, unit_price=1620.00, amount=1620.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Toner cartridge", quantity=1, unit_price=936.00, amount=936.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Desk organizer", quantity=1, unit_price=355.00, amount=355.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Whiteboard markers", quantity=1, unit_price=288.00, amount=288.00),
        PurchaseOrderLineItem(id=generate_uuid(), po_id=pos[6].id, description="Tax 18%", quantity=1, unit_price=511.00, amount=511.00),
    ]

    db.add_all(line_items)
    vendor_summary = [(v.vendor_id, v.legal_name, v.currency, v.tax_id) for v in vendors]
    po_count = len(pos)
    li_count = len(line_items)

    db.commit()
    db.close()

    print("Seed data inserted successfully.")
    print(f"  Vendors: {len(vendor_summary)}")
    print(f"  Purchase Orders: {po_count}")
    print(f"  PO Line Items: {li_count}")
    print()
    print("Vendors seeded:")
    for vid, name, currency, tax_id in vendor_summary:
        print(f"  {vid}  {name}  ({currency})  GSTIN/Tax ID: {tax_id}")


if __name__ == "__main__":
    seed()

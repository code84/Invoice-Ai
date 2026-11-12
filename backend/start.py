"""
start.py — Production startup script for Render.
1. Creates DB tables if they don't exist.
2. Seeds vendor + PO data if the vendors table is empty.
3. Starts uvicorn on the PORT provided by Render.
"""
import os
import sys

# ── 1. Create tables ──────────────────────────────────────────────────────────
from app.database import engine, Base, SessionLocal
from app.models.models import Vendor
Base.metadata.create_all(bind=engine)

# ── 2. Auto-seed if empty ─────────────────────────────────────────────────────
db = SessionLocal()
try:
    count = db.query(Vendor).count()
    if count == 0:
        print("[start.py] No vendors found — seeding database...")
        from seed_data import seed
        seed()
        print("[start.py] Seeding complete.")
    else:
        print(f"[start.py] Found {count} vendors — skipping seed.")
finally:
    db.close()

# ── 3. Start uvicorn ──────────────────────────────────────────────────────────
import uvicorn
port = int(os.environ.get("PORT", "8000"))
print(f"[start.py] Starting uvicorn on port {port}...")
uvicorn.run("app.main:app", host="0.0.0.0", port=port)

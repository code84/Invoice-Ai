from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.config import settings

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Intelligent Invoice Processing System",
    description="AI-assisted Accounts Payable workflow",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploaded files as static (for PDF preview)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers (added incrementally each phase) ─────────────────────────────────
from app.routers import vendors, purchase_orders, dashboard, invoices

app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["Purchase Orders"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Invoice Processing System"}

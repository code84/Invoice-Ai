from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Vendor Schemas ────────────────────────────────────────────────────────────

class VendorOut(BaseModel):
    id: str
    vendor_id: str
    legal_name: str
    aliases: List[str]
    tax_id: Optional[str]
    status: str
    is_approved: bool
    currency: str
    country: str

    class Config:
        from_attributes = True


# ── PO Line Item Schemas ──────────────────────────────────────────────────────

class POLineItemOut(BaseModel):
    id: str
    description: str
    quantity: float
    unit_price: float
    amount: float

    class Config:
        from_attributes = True


# ── Purchase Order Schemas ────────────────────────────────────────────────────

class PurchaseOrderOut(BaseModel):
    id: str
    po_number: str
    vendor_id: str
    po_date: Optional[str]
    status: str
    currency: str
    total_amount: float
    invoiced_amount: float
    remaining_balance: float
    description: Optional[str]
    line_items: List[POLineItemOut] = []

    class Config:
        from_attributes = True


# ── Processing Stage Schemas ──────────────────────────────────────────────────

class ProcessingStageOut(BaseModel):
    id: str
    stage_name: str
    stage_label: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output_summary: Optional[str]
    error_message: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


# ── Validation Result Schemas ─────────────────────────────────────────────────

class ValidationResultOut(BaseModel):
    id: str
    check_name: str
    result: str
    observed_value: Optional[str]
    expected_value: Optional[str]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Audit Event Schemas ───────────────────────────────────────────────────────

class AuditEventOut(BaseModel):
    id: str
    event_type: str
    description: str
    event_metadata: Any
    created_at: datetime

    class Config:
        from_attributes = True


# ── Invoice Schemas ───────────────────────────────────────────────────────────

class InvoiceLineItem(BaseModel):
    description: str
    quantity: Optional[float]
    unit_price: Optional[float]
    amount: Optional[float]


class InvoiceSummary(BaseModel):
    id: str
    filename: str
    upload_time: datetime
    vendor_name: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    po_number: Optional[str]
    currency: Optional[str]
    total: Optional[float]
    final_status: Optional[str]
    is_duplicate: bool

    class Config:
        from_attributes = True


class InvoiceDetail(BaseModel):
    id: str
    filename: str
    file_path: Optional[str]
    file_size: Optional[int]
    upload_time: datetime
    vendor_name: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    due_date: Optional[str]
    po_number: Optional[str]
    currency: Optional[str]
    subtotal: Optional[float]
    tax: Optional[float]
    total: Optional[float]
    tax_rate: Optional[float]
    tax_id: Optional[str]
    billing_address: Optional[str]
    payment_terms: Optional[str]
    line_items: List[Any]
    pdf_type: Optional[str]
    extraction_confidence: Optional[float]
    missing_fields: List[str]
    matched_po_id: Optional[str]
    matched_vendor_id: Optional[str]
    final_status: Optional[str]
    decision_explanation: Optional[str]
    recommended_action: Optional[str]
    is_duplicate: bool
    duplicate_of_id: Optional[str]

    class Config:
        from_attributes = True


# ── Processing Run Schemas ────────────────────────────────────────────────────

class ProcessingRunSummary(BaseModel):
    id: str
    run_id: str
    invoice_id: str
    status: str
    current_stage: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ProcessingRunDetail(BaseModel):
    id: str
    run_id: str
    invoice_id: str
    status: str
    current_stage: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    stages: List[ProcessingStageOut] = []
    validation_results: List[ValidationResultOut] = []
    audit_events: List[AuditEventOut] = []

    class Config:
        from_attributes = True


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_processed: int
    approved: int
    needs_review: int
    flagged: int
    recent_invoices: List[InvoiceSummary]

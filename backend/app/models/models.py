from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, primary_key=True, default=generate_uuid)
    vendor_id = Column(String, unique=True, nullable=False)       # e.g. V001
    legal_name = Column(String, nullable=False)
    aliases = Column(JSON, default=list)                           # list of alternate names
    tax_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="approved")    # approved | inactive
    is_approved = Column(Boolean, default=True)
    currency = Column(String, default="INR")
    country = Column(String, default="IN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class PurchaseOrderLineItem(Base):
    __tablename__ = "po_line_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    po_id = Column(String, ForeignKey("purchase_orders.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    po_number = Column(String, unique=True, nullable=False)        # e.g. PO-10045
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    po_date = Column(String, nullable=True)
    status = Column(String, nullable=False, default="approved")    # approved | inactive | closed
    currency = Column(String, default="INR")
    total_amount = Column(Float, nullable=False)
    invoiced_amount = Column(Float, default=0.0)                   # cumulative invoiced so far
    remaining_balance = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("Vendor", back_populates="purchase_orders")
    line_items = relationship("PurchaseOrderLineItem", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="matched_po")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    # Extracted fields (may be null if not found)
    vendor_name = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    po_number = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    tax_rate = Column(Float, nullable=True)
    tax_id = Column(String, nullable=True)
    billing_address = Column(Text, nullable=True)
    payment_terms = Column(String, nullable=True)
    line_items = Column(JSON, default=list)                        # list of dicts

    # Extraction metadata
    pdf_type = Column(String, nullable=True)                       # digital | scanned
    extraction_confidence = Column(Float, nullable=True)           # 0.0–1.0
    missing_fields = Column(JSON, default=list)                    # fields that could not be extracted
    raw_text = Column(Text, nullable=True)                         # raw extracted text

    # Matching / status
    matched_po_id = Column(String, ForeignKey("purchase_orders.id"), nullable=True)
    matched_vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    final_status = Column(String, nullable=True)                   # approved | needs_review | rejected
    decision_explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String, nullable=True)

    matched_po = relationship("PurchaseOrder", back_populates="invoices")
    processing_runs = relationship("ProcessingRun", back_populates="invoice", cascade="all, delete-orphan")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, unique=True, nullable=False)           # human-friendly e.g. RUN-2026-001
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    status = Column(String, default="running")                     # running | completed | failed
    current_stage = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="processing_runs")
    stages = relationship("ProcessingStage", back_populates="run", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="run", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="run", cascade="all, delete-orphan")


class ProcessingStage(Base):
    __tablename__ = "processing_stages"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("processing_runs.id"), nullable=False)
    stage_name = Column(String, nullable=False)
    stage_label = Column(String, nullable=False)
    status = Column(String, default="pending")                     # pending | running | completed | failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    run = relationship("ProcessingRun", back_populates="stages")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("processing_runs.id"), nullable=False)
    check_name = Column(String, nullable=False)
    result = Column(String, nullable=False)                        # passed | failed | warning
    observed_value = Column(String, nullable=True)
    expected_value = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ProcessingRun", back_populates="validation_results")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("processing_runs.id"), nullable=False)
    event_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ProcessingRun", back_populates="audit_events")

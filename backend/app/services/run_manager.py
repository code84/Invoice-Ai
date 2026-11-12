"""
Processing Run Manager

Creates and updates ProcessingRun + ProcessingStage records so the
frontend can poll for live stage status.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import ProcessingRun, ProcessingStage, AuditEvent
import uuid

STAGE_DEFINITIONS = [
    ("upload",      "Upload received"),
    ("classify",    "PDF classification"),
    ("extract_text","Text / OCR extraction"),
    ("ai_extract",  "AI field extraction"),
    ("normalize",   "Data normalization"),
    ("validate",    "Field validation"),
    ("vendor_po",   "Vendor & PO matching"),
    ("duplicate",   "Duplicate detection"),
    ("rules",       "Business rules engine"),
    ("decision",    "Decision recorded"),
]


def _run_counter(db: Session) -> int:
    return db.query(ProcessingRun).count() + 1


def create_run(invoice_id: str, db: Session) -> ProcessingRun:
    """Create a new ProcessingRun with all stages set to 'pending'."""
    count = _run_counter(db)
    run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y')}-{count:04d}"

    run = ProcessingRun(
        id=str(uuid.uuid4()),
        run_id=run_id,
        invoice_id=invoice_id,
        status="running",
        current_stage="upload",
    )
    db.add(run)
    db.flush()

    for idx, (stage_name, stage_label) in enumerate(STAGE_DEFINITIONS):
        stage = ProcessingStage(
            id=str(uuid.uuid4()),
            run_id=run.id,
            stage_name=stage_name,
            stage_label=stage_label,
            status="pending",
            order_index=idx,
        )
        db.add(stage)

    db.commit()
    db.refresh(run)
    return run


def start_stage(run: ProcessingRun, stage_name: str, db: Session):
    """Mark a stage as running."""
    stage = _get_stage(run, stage_name, db)
    if stage:
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc)
    run.current_stage = stage_name
    db.commit()


def complete_stage(run: ProcessingRun, stage_name: str, summary: str, db: Session):
    """Mark a stage as completed with an output summary."""
    stage = _get_stage(run, stage_name, db)
    if stage:
        stage.status = "completed"
        stage.completed_at = datetime.now(timezone.utc)
        stage.output_summary = summary
    db.commit()


def fail_stage(run: ProcessingRun, stage_name: str, error: str, db: Session):
    """Mark a stage as failed and fail the entire run."""
    stage = _get_stage(run, stage_name, db)
    if stage:
        stage.status = "failed"
        stage.completed_at = datetime.now(timezone.utc)
        stage.error_message = error
    run.status = "failed"
    run.error_message = error
    run.completed_at = datetime.now(timezone.utc)
    db.commit()


def complete_run(run: ProcessingRun, db: Session):
    """Mark the entire run as completed."""
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()


def add_audit_event(run: ProcessingRun, event_type: str, description: str,
                    event_metadata: dict, db: Session):
    """
    Record an audit event with an explicit Python-side timestamp.

    Using datetime.now(timezone.utc) instead of relying on SQLite's
    server_default=func.now() ensures microsecond-precision ordering even
    when multiple events are created within the same wall-clock second
    (which is common for fast digital-PDF processing runs).
    """
    event = AuditEvent(
        id=str(uuid.uuid4()),
        run_id=run.id,
        event_type=event_type,
        description=description,
        event_metadata=event_metadata,
        created_at=datetime.now(timezone.utc),   # explicit — prevents same-second ordering issues
    )
    db.add(event)
    db.commit()


def _get_stage(run: ProcessingRun, stage_name: str, db: Session):
    return (
        db.query(ProcessingStage)
        .filter(ProcessingStage.run_id == run.id, ProcessingStage.stage_name == stage_name)
        .first()
    )

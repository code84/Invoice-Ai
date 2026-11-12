import os
import uuid
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
import aiofiles

from app.database import get_db
from app.config import settings
from app.models.models import Invoice, ProcessingRun, ProcessingStage, ValidationResult, AuditEvent
from app.schemas.schemas import InvoiceSummary, InvoiceDetail, ProcessingRunDetail, ProcessingRunSummary
from app.services import run_manager
from app.services.pipeline import process_invoice

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=ProcessingRunSummary)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF invoice and start the processing pipeline.
    Returns the processing run ID for status polling.
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are accepted. Got: '{ext}'")

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save to disk
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create Invoice record
    invoice = Invoice(
        id=str(uuid.uuid4()),
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Create processing run
    run = run_manager.create_run(invoice.id, db)

    # Run pipeline in background (non-blocking upload response)
    background_tasks.add_task(_run_pipeline, invoice.id, run.id)

    return ProcessingRunSummary.model_validate(run)


def _run_pipeline(invoice_id: str, run_id: str):
    """Background task: open a fresh DB session and run the pipeline."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        run = db.query(ProcessingRun).filter(ProcessingRun.id == run_id).first()
        if invoice and run:
            process_invoice(invoice, run, db)
    except Exception as e:
        print(f"Pipeline error for run {run_id}: {e}")
    finally:
        db.close()


@router.get("/", response_model=List[InvoiceSummary])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.upload_time.desc()).all()
    return [InvoiceSummary.model_validate(i) for i in invoices]


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceDetail.model_validate(invoice)


@router.get("/{invoice_id}/runs", response_model=List[ProcessingRunSummary])
def get_invoice_runs(invoice_id: str, db: Session = Depends(get_db)):
    runs = (
        db.query(ProcessingRun)
        .filter(ProcessingRun.invoice_id == invoice_id)
        .order_by(ProcessingRun.started_at.desc())
        .all()
    )
    return [ProcessingRunSummary.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=ProcessingRunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get full run detail including stages, validation results and audit events."""
    run = (
        db.query(ProcessingRun)
        .options(
            joinedload(ProcessingRun.stages),
            joinedload(ProcessingRun.validation_results),
            joinedload(ProcessingRun.audit_events),
        )
        .filter(ProcessingRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Processing run not found")
    return ProcessingRunDetail.model_validate(run)


@router.get("/runs/{run_id}/stream")
def stream_run_status(run_id: str, db: Session = Depends(get_db)):
    """
    Server-Sent Events endpoint for live stage updates.
    Frontend polls this for real-time progress display.
    """
    import json
    import time

    def event_generator():
        last_stage_count = 0
        while True:
            run = (
                db.query(ProcessingRun)
                .options(joinedload(ProcessingRun.stages))
                .filter(ProcessingRun.id == run_id)
                .first()
            )
            if not run:
                yield f"data: {json.dumps({'error': 'run not found'})}\n\n"
                break

            stages = sorted(run.stages, key=lambda s: s.order_index)
            payload = {
                "run_status": run.status,
                "current_stage": run.current_stage,
                "stages": [
                    {
                        "stage_name": s.stage_name,
                        "stage_label": s.stage_label,
                        "status": s.status,
                        "output_summary": s.output_summary,
                        "error_message": s.error_message,
                        "order_index": s.order_index,
                    }
                    for s in stages
                ],
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if run.status in ("completed", "failed"):
                break

            time.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

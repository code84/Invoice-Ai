"""
Invoice Processing Pipeline

Orchestrates all 10 processing stages for a single invoice:
  upload → classify → extract_text → ai_extract → normalize
  → validate → vendor_po → duplicate → rules → decision

Each stage updates ProcessingRun so the frontend can track live progress.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import Invoice, ValidationResult, ProcessingRun
from app.services.pdf_extractor import extract_text
from app.services.ai_extractor import extract_invoice_fields
from app.services.normalizer import normalize_extraction, validate_extraction, get_missing_fields
from app.services.vendor_verifier import verify_vendor
from app.services.po_matcher import match_po
from app.services.duplicate_detector import check_duplicate
from app.services.rules_engine import run_rules
from app.services.decision_engine import make_decision
from app.services import run_manager


def process_invoice(invoice: Invoice, run: ProcessingRun, db: Session):
    try:
        # ── Stage 1: upload ────────────────────────────────────────────────
        run_manager.start_stage(run, "upload", db)
        run_manager.complete_stage(run, "upload",
            f"Received '{invoice.filename}' ({invoice.file_size or 0} bytes)", db)
        run_manager.add_audit_event(run, "upload", f"Invoice uploaded: {invoice.filename}",
            {"filename": invoice.filename, "file_size": invoice.file_size}, db)

        # ── Stage 2: classify ──────────────────────────────────────────────
        run_manager.start_stage(run, "classify", db)
        try:
            extraction_result = extract_text(invoice.file_path)
        except Exception as e:
            run_manager.fail_stage(run, "classify", str(e), db)
            return

        pdf_type = extraction_result["pdf_type"]
        raw_text = extraction_result["raw_text"]
        ocr_confidence = extraction_result["confidence"]
        invoice.pdf_type = pdf_type
        invoice.raw_text = raw_text
        db.commit()

        run_manager.complete_stage(run, "classify",
            f"PDF type: '{pdf_type}' (text ratio: {extraction_result['text_ratio']:.0%})", db)
        run_manager.add_audit_event(run, "classify", f"PDF classified as {pdf_type}",
            {"pdf_type": pdf_type, "text_ratio": extraction_result["text_ratio"]}, db)

        # ── Stage 3: extract_text ──────────────────────────────────────────
        run_manager.start_stage(run, "extract_text", db)
        if not raw_text or len(raw_text.strip()) < 20:
            run_manager.fail_stage(run, "extract_text",
                "Could not extract readable text from PDF.", db)
            _set_decision(invoice, "needs_review",
                "No readable text could be extracted from this PDF.",
                "Manually review the uploaded file.", db)
            _stub_remaining_stages(run, ["ai_extract","normalize","validate",
                                         "vendor_po","duplicate","rules","decision"], db)
            run_manager.complete_run(run, db)
            return

        run_manager.complete_stage(run, "extract_text",
            f"Extracted {len(raw_text)} characters "
            f"({'OCR' if pdf_type == 'scanned' else 'direct text'})", db)
        run_manager.add_audit_event(run, "extract_text",
            f"Text extraction complete ({len(raw_text)} characters via "
            f"{'OCR' if pdf_type == 'scanned' else 'direct text extraction'})",
            {
                "pdf_type": pdf_type,
                "text_length": len(raw_text),
                "method": "OCR" if pdf_type == "scanned" else "direct",
            }, db)

        # ── Stage 4: ai_extract ────────────────────────────────────────────
        run_manager.start_stage(run, "ai_extract", db)
        try:
            extracted = extract_invoice_fields(raw_text, ocr_confidence)
        except Exception as e:
            run_manager.fail_stage(run, "ai_extract", f"AI extraction error: {str(e)}", db)
            _set_decision(invoice, "needs_review", f"AI extraction failed: {str(e)}",
                "Retry or manually enter invoice details.", db)
            _stub_remaining_stages(run, ["normalize","validate","vendor_po",
                                         "duplicate","rules","decision"], db)
            run_manager.complete_run(run, db)
            return

        ai_confidence = extracted.get("confidence", 0.0)
        low_conf = extracted.get("low_confidence_fields") or []
        run_manager.complete_stage(run, "ai_extract",
            f"Extracted fields (confidence: {ai_confidence:.0%}). "
            f"Low-confidence: {', '.join(low_conf) or 'none'}", db)
        run_manager.add_audit_event(run, "ai_extract", "AI extraction complete",
            {"confidence": ai_confidence, "low_confidence_fields": low_conf}, db)

        # ── Stage 5: normalize ─────────────────────────────────────────────
        run_manager.start_stage(run, "normalize", db)
        normalized = normalize_extraction(extracted)
        missing_fields = get_missing_fields(normalized)

        invoice.vendor_name       = normalized.get("vendor_name")
        invoice.invoice_number    = normalized.get("invoice_number")
        invoice.invoice_date      = normalized.get("invoice_date")
        invoice.due_date          = normalized.get("due_date")
        invoice.po_number         = normalized.get("po_number")
        invoice.currency          = normalized.get("currency")
        invoice.subtotal          = normalized.get("subtotal")
        invoice.tax               = normalized.get("tax")
        invoice.total             = normalized.get("total")
        invoice.tax_rate          = normalized.get("tax_rate")
        invoice.tax_id            = normalized.get("tax_id")
        invoice.billing_address   = normalized.get("billing_address")
        invoice.payment_terms     = normalized.get("payment_terms")
        invoice.line_items        = normalized.get("line_items") or []

        # For scanned PDFs, cap confidence at 0.55 so R07 always triggers.
        # Rationale: OCR errors may exist that Gemini cannot detect from noisy text.
        # Human review is mandatory for any scanned invoice — this is a design policy.
        raw_confidence = normalized.get("confidence") or 0.0
        if pdf_type == "scanned":
            raw_confidence = min(raw_confidence, 0.55)
        invoice.extraction_confidence = raw_confidence
        normalized["confidence"] = raw_confidence

        invoice.missing_fields    = missing_fields
        db.commit()

        run_manager.complete_stage(run, "normalize",
            f"Normalized. Missing fields: {', '.join(missing_fields) or 'none'}", db)

        # ── Stage 6: validate ──────────────────────────────────────────────
        run_manager.start_stage(run, "validate", db)
        validation_results = validate_extraction(normalized)
        for vr in validation_results:
            db.add(ValidationResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                check_name=vr["check_name"],
                result=vr["result"],
                observed_value=vr.get("observed_value"),
                expected_value=vr.get("expected_value"),
                message=vr["message"],
            ))
        db.commit()

        failed_checks  = [v for v in validation_results if v["result"] == "failed"]
        warnings       = [v for v in validation_results if v["result"] == "warning"]
        run_manager.complete_stage(run, "validate",
            f"{len(validation_results)} checks — "
            f"{len(validation_results)-len(failed_checks)-len(warnings)} passed, "
            f"{len(warnings)} warnings, {len(failed_checks)} failed", db)
        run_manager.add_audit_event(run, "validate", "Validation complete",
            {"failed": len(failed_checks), "warnings": len(warnings)}, db)

        # ── Stage 7: vendor_po ─────────────────────────────────────────────
        run_manager.start_stage(run, "vendor_po", db)

        # Vendor verification
        vendor_result = verify_vendor(invoice.vendor_name, invoice.tax_id, db)
        matched_vendor = vendor_result.get("vendor")

        if matched_vendor:
            invoice.matched_vendor_id = matched_vendor.id
            db.commit()

        # PO matching
        po_result = match_po(
            po_number       = invoice.po_number,
            vendor_id       = matched_vendor.id if matched_vendor else None,
            invoice_total   = invoice.total,
            invoice_currency= invoice.currency,
            db              = db,
        )
        matched_po = po_result.get("matched_po")

        if matched_po:
            invoice.matched_po_id = matched_po.id
            # Update PO invoiced amount & remaining balance
            matched_po.invoiced_amount   = round(
                matched_po.invoiced_amount + (invoice.total or 0), 2)
            matched_po.remaining_balance = round(
                matched_po.total_amount - matched_po.invoiced_amount, 2)
            db.commit()

        vendor_po_summary = (
            f"Vendor: {vendor_result['message']} | "
            f"PO: {po_result['message']}"
        )
        run_manager.complete_stage(run, "vendor_po", vendor_po_summary, db)
        # Emit two distinct audit events so the trail shows vendor matching and
        # PO matching as separate steps (matches the required audit sequence).
        run_manager.add_audit_event(run, "vendor_matching", "Vendor matching complete", {
            "vendor_matched":  vendor_result["matched"],
            "vendor_approved": vendor_result["is_approved"],
            "match_method":    vendor_result.get("match_method"),
            "match_score":     vendor_result.get("match_score"),
            "vendor_status":   vendor_result.get("status"),
        }, db)
        run_manager.add_audit_event(run, "po_matching", "PO matching complete", {
            "po_match_type":    po_result["match_type"],
            "amount_variance":  po_result.get("amount_variance"),
            "within_tolerance": po_result.get("within_tolerance"),
            "po_status":        po_result.get("po_status"),
            "po_remaining_balance": po_result.get("po_remaining_balance"),
        }, db)

        # ── Stage 8: duplicate ─────────────────────────────────────────────
        run_manager.start_stage(run, "duplicate", db)
        dup_result = check_duplicate(
            vendor_name         = invoice.vendor_name,
            matched_vendor_id   = invoice.matched_vendor_id,
            invoice_number      = invoice.invoice_number,
            invoice_total       = invoice.total,
            invoice_date        = invoice.invoice_date,
            current_invoice_id  = invoice.id,
            db                  = db,
        )

        if dup_result["is_duplicate"]:
            invoice.is_duplicate    = True
            invoice.duplicate_of_id = dup_result["duplicate_of_id"]
            db.commit()
        elif dup_result.get("is_resubmission") and dup_result.get("duplicate_of_id"):
            # Not a duplicate — but preserve the link to the prior rejected attempt
            # so reviewers can compare both runs side-by-side.
            invoice.is_duplicate    = False
            invoice.duplicate_of_id = dup_result["duplicate_of_id"]
            db.commit()

        run_manager.complete_stage(run, "duplicate", dup_result["message"], db)
        run_manager.add_audit_event(run, "duplicate", "Duplicate check complete",
            {"is_duplicate": dup_result["is_duplicate"],
             "duplicate_of": dup_result.get("duplicate_of_id")}, db)

        # ── Stage 9: rules ─────────────────────────────────────────────────
        run_manager.start_stage(run, "rules", db)

        rule_results = run_rules(
            invoice_number        = invoice.invoice_number,
            invoice_total         = invoice.total,
            invoice_currency      = invoice.currency,
            missing_fields        = invoice.missing_fields or [],
            extraction_confidence = invoice.extraction_confidence,
            validation_failed_checks = failed_checks,

            vendor_matched        = vendor_result["matched"],
            vendor_approved       = vendor_result["is_approved"],
            vendor_status         = vendor_result["status"],
            vendor_match_score    = vendor_result["match_score"],

            po_matched            = po_result["matched_po"] is not None,
            po_match_type         = po_result["match_type"],
            po_status             = po_result.get("po_status"),
            amount_variance       = po_result.get("amount_variance"),
            amount_variance_pct   = po_result.get("amount_variance_pct"),
            within_tolerance      = po_result.get("within_tolerance", False),
            currency_match        = po_result.get("currency_match", True),
            po_candidate_count    = len(po_result.get("candidate_pos") or []),

            is_duplicate          = dup_result["is_duplicate"],
            possible_duplicate    = dup_result.get("possible_duplicate", False),
            is_resubmission       = dup_result.get("is_resubmission", False),
            duplicate_signals     = dup_result.get("match_signals") or [],
        )

        # Persist each rule result as a ValidationResult.
        # result field: "passed" (green PASS), "review" (amber REVIEW), "failed" (red BLOCKING)
        # message prefix: [PASS] / [REVIEW] / [BLOCKING] — clearly distinct from each other.
        for rr in rule_results:
            if rr.result == "passed":
                result_status = "passed"
                label = "PASS"
            elif rr.severity == "blocking":
                result_status = "failed"
                label = "BLOCKING"
            else:
                result_status = "review"
                label = "REVIEW"

            db.add(ValidationResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                check_name=rr.rule_name,
                result=result_status,
                observed_value=rr.observed,
                expected_value=rr.expected,
                message=f"[{label}] {rr.message}",
            ))
        db.commit()

        triggered       = [r for r in rule_results if r.result == "triggered"]
        blocking_fired  = [r for r in triggered if r.severity == "blocking"]
        review_fired    = [r for r in triggered if r.severity == "review"]

        rules_summary = (
            f"{len(rule_results)} rules evaluated — "
            f"{len(rule_results) - len(triggered)} passed, "
            f"{len(review_fired)} review, "
            f"{len(blocking_fired)} blocking"
        )
        run_manager.complete_stage(run, "rules", rules_summary, db)
        run_manager.add_audit_event(run, "rules", "Business rules evaluation complete", {
            "total_rules":    len(rule_results),
            "blocking_fired": len(blocking_fired),
            "review_fired":   len(review_fired),
            "rules_triggered": [r.rule_name for r in triggered],
        }, db)

        # ── Stage 10: decision ─────────────────────────────────────────────
        run_manager.start_stage(run, "decision", db)

        final_status, explanation, action = make_decision(rule_results)
        _set_decision(invoice, final_status, explanation, action, db)

        run_manager.complete_stage(run, "decision",
            f"Decision: {final_status.upper()} — {explanation[:100]}", db)
        run_manager.add_audit_event(run, "decision", f"Final decision: {final_status}", {
            "status":      final_status,
            "explanation": explanation,
            "action":      action,
        }, db)

        run_manager.complete_run(run, db)

    except Exception as e:
        db.rollback()
        try:
            run_manager.fail_stage(run, run.current_stage or "unknown", str(e), db)
        except Exception:
            pass
        raise


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_decision(invoice: Invoice, status: str, explanation: str,
                  action: str, db: Session):
    invoice.final_status          = status
    invoice.decision_explanation  = explanation
    invoice.recommended_action    = action
    db.commit()


def _stub_remaining_stages(run: ProcessingRun, stage_names: list, db: Session):
    for s in stage_names:
        try:
            run_manager.start_stage(run, s, db)
            run_manager.complete_stage(run, s, "Skipped — earlier stage failed", db)
        except Exception:
            pass

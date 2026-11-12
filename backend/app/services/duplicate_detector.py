"""
Duplicate Detection Service

Two-tier matching:

TIER 1 — Exact normalized invoice number + same vendor
         → confirmed duplicate (is_duplicate=True, BLOCKING)
           BUT only if the existing invoice was approved or needs_review.
         → resubmission (is_resubmission=True, REVIEW)
           if the existing invoice was previously *rejected* — a corrected
           resubmission is permitted with human oversight. The link to the
           prior attempt is preserved via duplicate_of_id.

TIER 2 — Same vendor + same amount + same date (non-rejected prior only)
         → possible duplicate (possible_duplicate=True, REVIEW)
         This catches OCR-noisy resubmissions even when the invoice number
         looks slightly different (e.g. INV-2O26-001 vs INV-2026-001).

Design rule: two invoices are NOT duplicates solely because amounts match.
Both vendor identity AND at least one strong corroborating signal are required.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from thefuzz import fuzz

from app.models.models import Invoice


def _normalize_inv_number(inv_num: Optional[str]) -> str:
    """Strip whitespace, uppercase, remove common separators."""
    if not inv_num:
        return ""
    return re.sub(r"[\s\-_/]", "", inv_num.strip().upper())


def _vendor_matches(matched_vendor_id, inv_matched_vendor_id,
                    vendor_name, inv_vendor_name) -> tuple[bool, str]:
    if matched_vendor_id and inv_matched_vendor_id:
        if matched_vendor_id == inv_matched_vendor_id:
            return True, "Same vendor ID in vendor master"
    if vendor_name and inv_vendor_name:
        score = fuzz.token_set_ratio(
            vendor_name.strip().lower(), inv_vendor_name.strip().lower()
        )
        if score >= 80:
            return True, f"Vendor name match (score {score}/100)"
    return False, ""


def check_duplicate(
    vendor_name: Optional[str],
    matched_vendor_id: Optional[str],
    invoice_number: Optional[str],
    invoice_total: Optional[float],
    invoice_date: Optional[str],
    current_invoice_id: str,
    db: Session,
) -> dict:
    """
    Check whether this invoice is a duplicate of an existing one.

    Returns:
        {
            is_duplicate,          # True = confirmed duplicate of approved/review → BLOCKING
            possible_duplicate,    # True = strong circumstantial match → REVIEW
            is_resubmission,       # True = exact match of previously-rejected invoice → REVIEW
            duplicate_of_id,       # ID of the matched prior invoice (set for all three cases)
            duplicate_of_inv_number,
            duplicate_of_status,   # final_status of the prior invoice
            match_signals,
            message
        }
    """
    base = {
        "is_duplicate": False,
        "possible_duplicate": False,
        "is_resubmission": False,
        "duplicate_of_id": None,
        "duplicate_of_inv_number": None,
        "duplicate_of_status": None,
        "match_signals": [],
    }

    if not invoice_number:
        return {**base, "message": "Cannot check duplicates: invoice number is missing."}

    normalized_new = _normalize_inv_number(invoice_number)

    existing = (
        db.query(Invoice)
        .filter(
            Invoice.id != current_invoice_id,
            Invoice.invoice_number.isnot(None),
            Invoice.final_status.isnot(None),
        )
        .all()
    )

    for inv in existing:
        vendor_match, vendor_signal = _vendor_matches(
            matched_vendor_id, inv.matched_vendor_id,
            vendor_name, inv.vendor_name
        )
        if not vendor_match:
            continue

        normalized_existing = _normalize_inv_number(inv.invoice_number)
        inv_num_score = fuzz.ratio(normalized_new, normalized_existing)

        # ── Tier 1: Exact invoice number + vendor match ────────────────────────
        if inv_num_score == 100:
            signals = [f"Exact invoice number match: '{invoice_number}'", vendor_signal]

            if invoice_total is not None and inv.total is not None:
                if abs(invoice_total - inv.total) < 0.01:
                    signals.append(f"Identical total: {invoice_total:,.2f}")

            if invoice_date and inv.invoice_date and invoice_date == inv.invoice_date:
                signals.append(f"Same invoice date: {invoice_date}")

            prior_status = inv.final_status  # "approved" | "needs_review" | "rejected"

            if prior_status == "rejected":
                # Prior attempt was rejected — allow controlled resubmission.
                # Flag as REVIEW so a human must approve before payment, but do NOT block.
                # The link (duplicate_of_id) is preserved so reviewers can compare attempts.
                return {
                    "is_duplicate": False,
                    "possible_duplicate": False,
                    "is_resubmission": True,
                    "duplicate_of_id": inv.id,
                    "duplicate_of_inv_number": inv.invoice_number,
                    "duplicate_of_status": prior_status,
                    "match_signals": signals,
                    "message": (
                        f"RESUBMISSION: Invoice '{invoice_number}' was previously submitted "
                        f"and rejected. This appears to be a corrected resubmission. "
                        f"Human review required before approving. "
                        f"Signals: {'; '.join(signals)}."
                    ),
                }
            else:
                # Approved or needs_review — BLOCKING: prevent double payment.
                return {
                    "is_duplicate": True,
                    "possible_duplicate": False,
                    "is_resubmission": False,
                    "duplicate_of_id": inv.id,
                    "duplicate_of_inv_number": inv.invoice_number,
                    "duplicate_of_status": prior_status,
                    "match_signals": signals,
                    "message": (
                        f"DUPLICATE DETECTED: Invoice '{invoice_number}' from same vendor "
                        f"already exists (status: {prior_status}). "
                        f"Signals: {'; '.join(signals)}. "
                        "Invoice blocked to prevent double payment."
                    ),
                }

        # ── Tier 2: Same vendor + same amount + same date → REVIEW ────────────
        # Only flag against non-rejected prior invoices to avoid suppressing
        # legitimate resubmissions of rejected invoices.
        # Requires TWO corroborating signals (amount AND date) to avoid false positives.
        if inv.final_status == "rejected":
            continue  # don't trigger possible-duplicate for previously-rejected invoices

        amount_match = (
            invoice_total is not None and inv.total is not None
            and abs(invoice_total - inv.total) < 0.01
        )
        date_match = (
            invoice_date is not None and inv.invoice_date is not None
            and invoice_date == inv.invoice_date
        )

        if amount_match and date_match:
            signals = [
                vendor_signal,
                f"Same total amount: {invoice_total:,.2f}",
                f"Same invoice date: {invoice_date}",
            ]
            if inv_num_score >= 80:
                signals.append(
                    f"Similar invoice number (score {inv_num_score}/100): "
                    f"'{invoice_number}' vs '{inv.invoice_number}' — possible OCR noise"
                )
            return {
                "is_duplicate": False,
                "possible_duplicate": True,
                "is_resubmission": False,
                "duplicate_of_id": inv.id,
                "duplicate_of_inv_number": inv.invoice_number,
                "duplicate_of_status": inv.final_status,
                "match_signals": signals,
                "message": (
                    f"POSSIBLE DUPLICATE: Same vendor, amount ({invoice_total:,.2f}) "
                    f"and date ({invoice_date}) match existing invoice "
                    f"'{inv.invoice_number}'. Invoice numbers differ — may be OCR noise "
                    f"on a resubmission. Human verification required."
                ),
            }

    return {**base, "message": f"No duplicate found for invoice '{invoice_number}'."}

"""
Purchase Order Matching Service

Matches an invoice against the PO dataset using:
  1. Explicit PO number match (primary) — with vendor ownership verification
  2. Fuzzy PO number match (handles OCR noise) — with vendor ownership verification
  3. Vendor-scoped candidate search when PO number is missing/ambiguous
     → auto-matches when exactly ONE candidate passes amount tolerance
       (prevents spurious "ambiguous" results when there is a clear winner)
  4. Amount comparison with configurable tolerance threshold (design assumption: 2%)

Design assumption: tolerance threshold = 2% of PO total amount.
This is a business policy decision — documented here, not a Zamp-mandated rule.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from thefuzz import fuzz

from app.models.models import PurchaseOrder, Vendor
from app.config import settings

TOLERANCE_PCT = settings.TOLERANCE_THRESHOLD          # default 0.02 (2%)
PO_FUZZY_THRESHOLD = 80                               # fuzzy score for PO number matching


def _amount_variance(invoice_total: float, po_total: float) -> Tuple[float, float, bool]:
    """
    Returns (variance_amount, variance_pct, within_tolerance).
    variance_pct is relative to PO total.
    """
    if po_total == 0:
        return 0.0, 0.0, True
    variance = invoice_total - po_total
    variance_pct = abs(variance) / po_total
    within = variance_pct <= TOLERANCE_PCT
    return variance, variance_pct, within


def _vendor_owns_po(po: PurchaseOrder, vendor_id: Optional[str]) -> bool:
    """Return True if vendor_id matches the PO's owner, or if vendor_id is unknown."""
    return not vendor_id or po.vendor_id == vendor_id


def match_po(
    po_number: Optional[str],
    vendor_id: Optional[str],
    invoice_total: Optional[float],
    invoice_currency: Optional[str],
    db: Session,
) -> dict:
    """
    Attempt to match the invoice to a Purchase Order.

    Returns a result dict with:
      matched_po, match_type, amount_variance, within_tolerance,
      candidate_pos (when no exact match), message
    """
    all_pos = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.line_items))
        .all()
    )

    # ── 1. Exact PO number match ───────────────────────────────────────────────
    if po_number:
        po_number_clean = po_number.strip().upper()
        exact_po = None
        for po in all_pos:
            if po.po_number.strip().upper() == po_number_clean:
                exact_po = po
                break

        if exact_po is not None:
            # Verify vendor ownership — a PO belonging to a different vendor must not
            # be matched, even if the PO number happens to match.
            if not _vendor_owns_po(exact_po, vendor_id):
                return {
                    "matched_po": None,
                    "match_type": "vendor_mismatch",
                    "amount_variance": None,
                    "amount_variance_pct": None,
                    "within_tolerance": False,
                    "currency_match": True,
                    "candidate_pos": [],
                    "po_status": exact_po.status,
                    "po_remaining_balance": exact_po.remaining_balance,
                    "message": (
                        f"PO {exact_po.po_number} found but belongs to a different vendor. "
                        "Invoice vendor does not own this PO — cannot process."
                    ),
                }
            return _build_result(exact_po, "exact_po_number", invoice_total,
                                 invoice_currency, [], db)

        # ── 1b. Fuzzy PO number match (handles OCR noise like "P0-10045") ─────
        best_po = None
        best_score = 0
        for po in all_pos:
            score = fuzz.ratio(po_number_clean, po.po_number.strip().upper())
            if score > best_score:
                best_score = score
                best_po = po

        if best_score >= PO_FUZZY_THRESHOLD and best_po:
            # Verify vendor ownership for fuzzy match too
            if not _vendor_owns_po(best_po, vendor_id):
                return {
                    "matched_po": None,
                    "match_type": "vendor_mismatch",
                    "amount_variance": None,
                    "amount_variance_pct": None,
                    "within_tolerance": False,
                    "currency_match": True,
                    "candidate_pos": [],
                    "po_status": best_po.status,
                    "po_remaining_balance": best_po.remaining_balance,
                    "message": (
                        f"Best PO match ({best_po.po_number}, score {best_score}/100) "
                        "belongs to a different vendor — cannot match across vendors."
                    ),
                }
            return _build_result(best_po, f"fuzzy_po_number (score:{best_score})",
                                 invoice_total, invoice_currency, [], db)

    # ── 2. No PO number — vendor-scoped candidate search ──────────────────────
    if vendor_id:
        vendor_pos = [po for po in all_pos if po.vendor_id == vendor_id]
    else:
        vendor_pos = all_pos

    # Candidates: approved POs belonging to this vendor with remaining balance
    candidates = [
        po for po in vendor_pos
        if po.status == "approved" and po.remaining_balance > 0
    ]

    if not candidates:
        return {
            "matched_po": None,
            "match_type": "no_match",
            "amount_variance": None,
            "amount_variance_pct": None,
            "within_tolerance": False,
            "currency_match": True,
            "candidate_pos": [],
            "message": "No PO number on invoice and no eligible candidate POs found for this vendor.",
        }

    # Identify candidates whose remaining balance is within tolerance of the invoice total.
    # If exactly ONE candidate passes → auto-match (clear winner, not ambiguous).
    if invoice_total is not None:
        within_tol_candidates = [
            po for po in candidates
            if _amount_variance(invoice_total, po.total_amount)[2]
        ]

        if len(within_tol_candidates) == 1:
            return _build_result(within_tol_candidates[0], "single_candidate_amount_match",
                                 invoice_total, invoice_currency, [], db)

        # If only one candidate exists (regardless of amount tolerance) → auto-match.
        # R11 will flag the amount variance if it's outside tolerance.
        if len(candidates) == 1:
            return _build_result(candidates[0], "single_candidate_amount_match",
                                 invoice_total, invoice_currency, [], db)
    else:
        # No invoice total to compare — auto-match if only one candidate
        if len(candidates) == 1:
            return _build_result(candidates[0], "single_candidate_no_amount",
                                 invoice_total, invoice_currency, [], db)

    # Multiple candidates with no clear winner — human must select
    candidate_summaries = [
        {
            "po_number": po.po_number,
            "total_amount": po.total_amount,
            "remaining_balance": po.remaining_balance,
            "status": po.status,
        }
        for po in candidates[:5]  # cap at 5 for readability
    ]
    return {
        "matched_po": None,
        "match_type": "ambiguous",
        "amount_variance": None,
        "amount_variance_pct": None,
        "within_tolerance": False,
        "currency_match": True,
        "candidate_pos": candidate_summaries,
        "message": (
            f"No explicit PO number found. {len(candidates)} candidate PO(s) exist for this vendor "
            f"({len([po for po in candidates if _amount_variance(invoice_total or 0, po.total_amount)[2]])} "
            f"within amount tolerance). Human selection required."
        ),
    }


def _build_result(
    po: PurchaseOrder,
    match_type: str,
    invoice_total: Optional[float],
    invoice_currency: Optional[str],
    candidate_pos: list,
    db: Session,
) -> dict:
    """Build a full match result for a resolved PO."""
    # Currency check
    currency_ok = True
    currency_msg = ""
    if invoice_currency and po.currency:
        if invoice_currency.upper() != po.currency.upper():
            currency_ok = False
            currency_msg = (
                f"Currency mismatch: invoice is {invoice_currency}, PO is {po.currency}. "
                "Automatic approval blocked."
            )

    # Amount variance
    variance = None
    variance_pct = None
    within_tolerance = True

    if invoice_total is not None:
        variance, variance_pct, within_tolerance = _amount_variance(invoice_total, po.total_amount)

    # Remaining balance check
    balance_msg = ""
    if invoice_total is not None and po.remaining_balance is not None:
        if invoice_total > po.remaining_balance * (1 + TOLERANCE_PCT):
            balance_msg = (
                f"Invoice total ({invoice_total:,.2f}) exceeds PO remaining balance "
                f"({po.remaining_balance:,.2f}). Potential over-invoicing."
            )

    # Build human-readable message
    if invoice_total is None:
        amount_msg = "Invoice total not available for comparison."
    elif within_tolerance:
        amount_msg = (
            f"Invoice total ({invoice_total:,.2f}) vs PO total ({po.total_amount:,.2f}). "
            f"Variance: {variance:+,.2f} ({variance_pct:.2%}) — within {TOLERANCE_PCT:.0%} tolerance."
        )
    else:
        amount_msg = (
            f"Invoice total ({invoice_total:,.2f}) vs PO total ({po.total_amount:,.2f}). "
            f"Variance: {variance:+,.2f} ({variance_pct:.2%}) — EXCEEDS {TOLERANCE_PCT:.0%} tolerance."
        )

    messages = [f"Matched PO {po.po_number} via {match_type}.", amount_msg]
    if balance_msg:
        messages.append(balance_msg)
    if currency_msg:
        messages.append(currency_msg)

    return {
        "matched_po": po,
        "match_type": match_type,
        "amount_variance": round(variance, 2) if variance is not None else None,
        "amount_variance_pct": round(variance_pct * 100, 4) if variance_pct is not None else None,
        "within_tolerance": within_tolerance and currency_ok,
        "currency_match": currency_ok,
        "candidate_pos": candidate_pos,
        "po_status": po.status,
        "po_remaining_balance": po.remaining_balance,
        "message": " ".join(messages),
    }

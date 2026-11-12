"""
Business Rules Engine

Applies deterministic rules to all evidence gathered from previous pipeline stages.
Each rule returns a RuleResult with a severity level:

  BLOCKING  → forces final status = "rejected"
  REVIEW    → forces final status = "needs_review"
  INFO      → informational only, does not change status

Rules run in order. All rules fire (no early exit) so the full picture
is visible in the audit trail.

Design assumptions documented inline — these are policy choices, not Zamp mandates.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from app.config import settings


@dataclass
class RuleResult:
    rule_name: str
    severity: str           # "blocking" | "review" | "info"
    result: str             # "passed" | "triggered"
    message: str
    observed: Optional[str] = None
    expected: Optional[str] = None


def run_rules(
    # Extracted invoice fields
    invoice_number: Optional[str],
    invoice_total: Optional[float],
    invoice_currency: Optional[str],
    missing_fields: List[str],
    extraction_confidence: Optional[float],
    validation_failed_checks: List[dict],

    # Vendor verification result
    vendor_matched: bool,
    vendor_approved: bool,
    vendor_status: str,
    vendor_match_score: int,

    # PO matching result
    po_matched: bool,
    po_match_type: str,
    po_status: Optional[str],
    amount_variance: Optional[float],
    amount_variance_pct: Optional[float],
    within_tolerance: bool,
    currency_match: bool,
    po_candidate_count: int,

    # Duplicate detection result
    is_duplicate: bool,
    possible_duplicate: bool,
    is_resubmission: bool,
    duplicate_signals: List[str],
) -> List[RuleResult]:
    """
    Run all business rules and return the full list of RuleResults.
    """
    rules: List[RuleResult] = []

    # ── RULE 1a: Confirmed duplicate (BLOCKING) ───────────────────────────────
    if is_duplicate:
        rules.append(RuleResult(
            rule_name="R01_duplicate_invoice",
            severity="blocking",
            result="triggered",
            message=(
                f"Confirmed duplicate: exact invoice number + vendor match against an "
                f"already-approved/reviewed invoice. "
                f"Signals: {'; '.join(duplicate_signals)}. "
                "Invoice blocked to prevent double payment."
            ),
            observed="Confirmed duplicate",
            expected="Unique invoice",
        ))
    # ── RULE 1b: Resubmission of a previously-rejected invoice (REVIEW) ───────
    # The prior invoice was rejected — a corrected resubmission is permitted but
    # requires human review before approval. The link to the prior run is preserved.
    elif is_resubmission:
        rules.append(RuleResult(
            rule_name="R01_resubmission",
            severity="review",
            result="triggered",
            message=(
                f"Resubmission detected: this invoice number was previously submitted "
                f"and rejected. Signals: {'; '.join(duplicate_signals)}. "
                "AP team must compare with the prior rejected attempt before approving."
            ),
            observed="Resubmission of rejected invoice",
            expected="Unique invoice or approved resubmission",
        ))
    # ── RULE 1c: Possible duplicate (REVIEW only — never auto-blocks) ─────────
    elif possible_duplicate:
        rules.append(RuleResult(
            rule_name="R01_possible_duplicate",
            severity="review",
            result="triggered",
            message=(
                f"Possible duplicate detected via fuzzy invoice number match. "
                f"Signals: {'; '.join(duplicate_signals)}. "
                "May be OCR noise on a resubmission. Human must verify before approving."
            ),
            observed="Fuzzy duplicate match",
            expected="Unique invoice",
        ))
    else:
        rules.append(RuleResult(
            rule_name="R01_duplicate_invoice",
            severity="blocking",
            result="passed",
            message="No duplicate found. Invoice number is unique for this vendor.",
        ))

    # ── RULE 2: Vendor not found in master ────────────────────────────────────
    if not vendor_matched:
        rules.append(RuleResult(
            rule_name="R02_vendor_not_found",
            severity="blocking",
            result="triggered",
            message=(
                "Vendor not found in vendor master. "
                "Cannot process invoices from unrecognised vendors. "
                "AP team must register vendor before resubmitting."
            ),
            observed="No vendor match",
            expected="Vendor in master",
        ))
    else:
        rules.append(RuleResult(
            rule_name="R02_vendor_not_found",
            severity="blocking",
            result="passed",
            message=f"Vendor found in master (match score: {vendor_match_score}/100).",
        ))

    # ── RULE 3: Vendor inactive / unapproved ──────────────────────────────────
    # Assumption: inactive vendor = blocking. Procurement must reactivate first.
    if vendor_matched and not vendor_approved:
        rules.append(RuleResult(
            rule_name="R03_vendor_inactive",
            severity="blocking",
            result="triggered",
            message=(
                f"Vendor status is '{vendor_status}'. "
                "Automatic approval blocked. "
                "Procurement must reactivate vendor before invoice can be processed."
            ),
            observed=vendor_status,
            expected="approved",
        ))
    elif vendor_matched:
        rules.append(RuleResult(
            rule_name="R03_vendor_inactive",
            severity="blocking",
            result="passed",
            message=f"Vendor is active and approved (status: {vendor_status}).",
        ))

    # ── RULE 4: Missing invoice number ────────────────────────────────────────
    # Assumption: missing invoice number = review (not blocking — other fields
    # may be sufficient for AP to identify and register the invoice manually).
    if not invoice_number:
        rules.append(RuleResult(
            rule_name="R04_missing_invoice_number",
            severity="review",
            result="triggered",
            message=(
                "Invoice number is missing or could not be extracted. "
                "AP team must obtain invoice number from vendor before processing."
            ),
            observed="null",
            expected="Invoice number present",
        ))
    else:
        rules.append(RuleResult(
            rule_name="R04_missing_invoice_number",
            severity="review",
            result="passed",
            message=f"Invoice number present: {invoice_number}.",
        ))

    # ── RULE 5: Mandatory field failures (from validation) ────────────────────
    blocking_validation = [
        v for v in validation_failed_checks
        if v["check_name"] == "required_fields"
    ]
    if blocking_validation:
        rules.append(RuleResult(
            rule_name="R05_mandatory_fields",
            severity="review",
            result="triggered",
            message=blocking_validation[0]["message"],
            observed=blocking_validation[0].get("observed_value"),
            expected=blocking_validation[0].get("expected_value"),
        ))
    else:
        rules.append(RuleResult(
            rule_name="R05_mandatory_fields",
            severity="review",
            result="passed",
            message="All mandatory fields are present.",
        ))

    # ── RULE 6: Arithmetic validation failure ─────────────────────────────────
    arith_failures = [
        v for v in validation_failed_checks
        if v["check_name"] in ("arithmetic_subtotal_plus_tax", "line_item_arithmetic")
    ]
    if arith_failures:
        rules.append(RuleResult(
            rule_name="R06_arithmetic_failure",
            severity="review",
            result="triggered",
            message="; ".join(v["message"] for v in arith_failures),
            observed=arith_failures[0].get("observed_value"),
            expected=arith_failures[0].get("expected_value"),
        ))
    else:
        rules.append(RuleResult(
            rule_name="R06_arithmetic_failure",
            severity="review",
            result="passed",
            message="All arithmetic checks passed (subtotal + tax = total, line items correct).",
        ))

    # ── RULE 7: Low extraction confidence ────────────────────────────────────
    # Assumption: confidence < 0.60 = review required.
    conf = extraction_confidence or 0.0
    if conf < 0.60:
        rules.append(RuleResult(
            rule_name="R07_low_confidence",
            severity="review",
            result="triggered",
            message=(
                f"Extraction confidence is low ({conf:.0%}). "
                "One or more key fields may be inaccurate. Human verification required."
            ),
            observed=f"{conf:.0%}",
            expected=">= 60%",
        ))
    else:
        rules.append(RuleResult(
            rule_name="R07_low_confidence",
            severity="review",
            result="passed",
            message=f"Extraction confidence is acceptable ({conf:.0%}).",
        ))

    # ── RULE 8: No PO match ───────────────────────────────────────────────────
    if not po_matched and po_match_type == "vendor_mismatch":
        rules.append(RuleResult(
            rule_name="R08_no_po_match",
            severity="blocking",
            result="triggered",
            message=(
                "PO number was found in the system but belongs to a different vendor. "
                "Invoice vendor does not own this PO — cannot process without manual correction."
            ),
            observed="PO vendor mismatch",
            expected="PO owned by invoice vendor",
        ))
    elif not po_matched and po_match_type != "ambiguous":
        rules.append(RuleResult(
            rule_name="R08_no_po_match",
            severity="review",
            result="triggered",
            message=(
                "No matching Purchase Order found. "
                "AP team must identify the correct PO before approving payment."
            ),
            observed="No PO matched",
            expected="Matched PO",
        ))
    elif not po_matched and po_match_type == "ambiguous":
        rules.append(RuleResult(
            rule_name="R08_no_po_match",
            severity="review",
            result="triggered",
            message=(
                f"PO reference is ambiguous — {po_candidate_count} candidate PO(s) found. "
                "AP team must select the correct PO."
            ),
            observed=f"{po_candidate_count} candidates",
            expected="Single matched PO",
        ))
    else:
        rules.append(RuleResult(
            rule_name="R08_no_po_match",
            severity="review",
            result="passed",
            message="Purchase Order matched successfully.",
        ))

    # ── RULE 9: PO inactive / closed ─────────────────────────────────────────
    if po_matched and po_status and po_status != "approved":
        rules.append(RuleResult(
            rule_name="R09_po_not_approved",
            severity="blocking",
            result="triggered",
            message=(
                f"Matched PO status is '{po_status}'. "
                "Only invoices against approved POs can be processed automatically."
            ),
            observed=po_status,
            expected="approved",
        ))
    elif po_matched:
        rules.append(RuleResult(
            rule_name="R09_po_not_approved",
            severity="blocking",
            result="passed",
            message="Matched PO is in approved status.",
        ))

    # ── RULE 10: Currency mismatch ────────────────────────────────────────────
    if po_matched and not currency_match:
        rules.append(RuleResult(
            rule_name="R10_currency_mismatch",
            severity="blocking",
            result="triggered",
            message=(
                f"Invoice currency ({invoice_currency}) does not match PO currency. "
                "Currency mismatch blocks automatic approval."
            ),
            observed=invoice_currency,
            expected="Same as PO currency",
        ))
    elif po_matched:
        rules.append(RuleResult(
            rule_name="R10_currency_mismatch",
            severity="blocking",
            result="passed",
            message=f"Invoice and PO currencies match ({invoice_currency}).",
        ))

    # ── RULE 11: Amount tolerance check ──────────────────────────────────────
    # Assumption: 2% tolerance (TOLERANCE_THRESHOLD in config).
    # Within tolerance → continue. Beyond → review.
    if po_matched and amount_variance is not None:
        tol_pct = settings.TOLERANCE_THRESHOLD * 100
        if not within_tolerance:
            rules.append(RuleResult(
                rule_name="R11_amount_tolerance",
                severity="review",
                result="triggered",
                message=(
                    f"Invoice amount variance exceeds {tol_pct:.0f}% tolerance. "
                    f"Variance: {amount_variance:+,.2f} ({amount_variance_pct:.2f}%). "
                    "AP team must investigate before approving."
                ),
                observed=f"{amount_variance_pct:.2f}%",
                expected=f"<= {tol_pct:.0f}%",
            ))
        else:
            rules.append(RuleResult(
                rule_name="R11_amount_tolerance",
                severity="review",
                result="passed",
                message=(
                    f"Amount variance ({amount_variance:+,.2f}, {amount_variance_pct:.2f}%) "
                    f"is within {tol_pct:.0f}% tolerance."
                ),
            ))

    return rules

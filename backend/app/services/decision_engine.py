"""
Decision Engine

Consumes the output of the rules engine and produces:
  - final_status:          "approved" | "needs_review" | "rejected"
  - decision_explanation:  human-readable summary of what happened
  - recommended_action:    what AP should do next
"""
from typing import List, Tuple
from app.services.rules_engine import RuleResult


def make_decision(rules: List[RuleResult]) -> Tuple[str, str, str]:
    """
    Evaluate all rule results and return (status, explanation, action).

    Decision logic:
      - Any BLOCKING rule triggered  → rejected
      - Any REVIEW rule triggered    → needs_review
      - All rules passed             → approved
    """
    blocking_triggered = [r for r in rules if r.severity == "blocking" and r.result == "triggered"]
    review_triggered   = [r for r in rules if r.severity == "review"   and r.result == "triggered"]
    all_passed         = not blocking_triggered and not review_triggered

    # ── Determine status ───────────────────────────────────────────────────
    if blocking_triggered:
        status = "rejected"
    elif review_triggered:
        status = "needs_review"
    else:
        status = "approved"

    # ── Build explanation ──────────────────────────────────────────────────
    if status == "approved":
        explanation = (
            "All checks passed. "
            "Vendor is approved and active, PO is matched and within tolerance, "
            "no duplicate detected, all mandatory fields present, "
            "arithmetic validated. Invoice is eligible for payment."
        )
        action = (
            "Proceed with payment processing. "
            "Post invoice to accounts payable ledger and schedule payment per terms."
        )

    elif status == "rejected":
        reasons = [f"[{r.rule_name}] {r.message}" for r in blocking_triggered]
        explanation = (
            f"Invoice REJECTED. {len(blocking_triggered)} blocking condition(s) found:\n"
            + "\n".join(f"  • {r}" for r in reasons)
        )
        if review_triggered:
            also = [f"[{r.rule_name}] {r.message}" for r in review_triggered]
            explanation += (
                f"\n\nAdditional review issues ({len(review_triggered)}):\n"
                + "\n".join(f"  • {r}" for r in also)
            )
        action = _rejection_action(blocking_triggered)

    else:  # needs_review
        reasons = [f"[{r.rule_name}] {r.message}" for r in review_triggered]
        explanation = (
            f"Invoice requires review. {len(review_triggered)} issue(s) need AP attention:\n"
            + "\n".join(f"  • {r}" for r in reasons)
        )
        action = _review_action(review_triggered)

    return status, explanation, action


def _rejection_action(blocking: List[RuleResult]) -> str:
    """Return specific action guidance based on what was blocked."""
    rule_names = {r.rule_name for r in blocking}
    actions = []

    if "R01_duplicate_invoice" in rule_names:
        actions.append("Notify vendor that this invoice has already been received. Do not pay.")
    if "R02_vendor_not_found" in rule_names:
        actions.append("Contact procurement to register vendor before resubmitting.")
    if "R03_vendor_inactive" in rule_names:
        actions.append("Contact procurement to reactivate vendor account.")
    if "R09_po_not_approved" in rule_names:
        actions.append("Contact procurement to check PO status.")
    if "R10_currency_mismatch" in rule_names:
        actions.append("Contact vendor to reissue invoice in the correct currency.")

    return " | ".join(actions) if actions else "Review blocking conditions with AP manager."


def _review_action(review: List[RuleResult]) -> str:
    """Return specific action guidance for review items."""
    rule_names = {r.rule_name for r in review}
    actions = []

    if "R04_missing_invoice_number" in rule_names:
        actions.append("Request invoice number from vendor.")
    if "R05_mandatory_fields" in rule_names:
        actions.append("Obtain missing fields from vendor.")
    if "R06_arithmetic_failure" in rule_names:
        actions.append("Verify amounts with original invoice document.")
    if "R07_low_confidence" in rule_names:
        actions.append("Manually verify extracted fields against original PDF.")
    if "R08_no_po_match" in rule_names:
        actions.append("Identify and confirm the correct PO with procurement.")
    if "R11_amount_tolerance" in rule_names:
        actions.append("Investigate amount variance with vendor and procurement.")

    return " | ".join(actions) if actions else "Review flagged issues with AP manager."

"""
Data Normalization and Validation Service

Deterministic checks run AFTER AI extraction.
AI handles understanding; this code handles financial correctness.
"""
from typing import Optional, List, Dict, Any
from dateutil import parser as dateutil_parser
import re


REQUIRED_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "total"]
TOLERANCE = 0.01  # 1 cent tolerance for arithmetic checks


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Attempt to parse any date string into YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        parsed = dateutil_parser.parse(str(date_str), dayfirst=False)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return date_str  # Return original if unparseable


def normalize_amount(value: Any) -> Optional[float]:
    """Strip currency symbols and commas; return float or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # String: remove currency symbols, commas, spaces
    cleaned = re.sub(r"[^\d.\-]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_currency(currency: Optional[str]) -> Optional[str]:
    """Normalize currency codes to uppercase 3-letter ISO codes."""
    if not currency:
        return None
    mapping = {
        "rupee": "INR", "rupees": "INR", "rs": "INR", "inr": "INR", "₹": "INR",
        "dollar": "USD", "dollars": "USD", "usd": "USD", "$": "USD",
        "euro": "EUR", "euros": "EUR", "eur": "EUR", "€": "EUR",
        "pound": "GBP", "pounds": "GBP", "gbp": "GBP", "£": "GBP",
    }
    normalized = mapping.get(currency.strip().lower(), currency.strip().upper())
    return normalized


def normalize_vendor_name(name: Optional[str]) -> Optional[str]:
    """Normalize vendor name: strip, collapse whitespace."""
    if not name:
        return None
    return " ".join(name.strip().split())


def normalize_extraction(extracted: dict) -> dict:
    """Apply normalization to all extracted fields."""
    extracted["invoice_date"] = normalize_date(extracted.get("invoice_date"))
    extracted["due_date"] = normalize_date(extracted.get("due_date"))
    extracted["subtotal"] = normalize_amount(extracted.get("subtotal"))
    extracted["tax"] = normalize_amount(extracted.get("tax"))
    extracted["total"] = normalize_amount(extracted.get("total"))
    extracted["tax_rate"] = normalize_amount(extracted.get("tax_rate"))
    extracted["currency"] = normalize_currency(extracted.get("currency"))
    extracted["vendor_name"] = normalize_vendor_name(extracted.get("vendor_name"))

    # Normalize line items
    line_items = extracted.get("line_items") or []
    normalized_lines = []
    for item in line_items:
        normalized_lines.append({
            "description": item.get("description", ""),
            "quantity": normalize_amount(item.get("quantity")),
            "unit_price": normalize_amount(item.get("unit_price")),
            "amount": normalize_amount(item.get("amount")),
        })
    extracted["line_items"] = normalized_lines
    return extracted


def validate_extraction(extracted: dict) -> List[Dict]:
    """
    Run deterministic validation checks.
    Returns a list of validation result dicts:
      { check_name, result, observed_value, expected_value, message }
    """
    results = []

    # 1. Required fields check
    missing = []
    for field in REQUIRED_FIELDS:
        if not extracted.get(field):
            missing.append(field)

    if missing:
        results.append({
            "check_name": "required_fields",
            "result": "failed",
            "observed_value": f"Missing: {', '.join(missing)}",
            "expected_value": f"All required: {', '.join(REQUIRED_FIELDS)}",
            "message": f"Required field(s) missing or null: {', '.join(missing)}",
        })
    else:
        results.append({
            "check_name": "required_fields",
            "result": "passed",
            "observed_value": "All required fields present",
            "expected_value": f"All required: {', '.join(REQUIRED_FIELDS)}",
            "message": "All required fields are present.",
        })

    # 2. Date validity
    inv_date = extracted.get("invoice_date")
    if inv_date:
        try:
            dateutil_parser.parse(str(inv_date))
            results.append({
                "check_name": "date_validity",
                "result": "passed",
                "observed_value": inv_date,
                "expected_value": "Parseable date",
                "message": f"Invoice date '{inv_date}' is valid.",
            })
        except Exception:
            results.append({
                "check_name": "date_validity",
                "result": "failed",
                "observed_value": inv_date,
                "expected_value": "Parseable date",
                "message": f"Invoice date '{inv_date}' could not be parsed.",
            })
    else:
        results.append({
            "check_name": "date_validity",
            "result": "warning",
            "observed_value": "null",
            "expected_value": "Parseable date",
            "message": "Invoice date is missing; cannot validate.",
        })

    # 3. Positive amounts
    for field in ["subtotal", "tax", "total"]:
        val = extracted.get(field)
        if val is not None:
            if val < 0:
                results.append({
                    "check_name": f"positive_amount_{field}",
                    "result": "failed",
                    "observed_value": str(val),
                    "expected_value": ">= 0",
                    "message": f"{field.capitalize()} is negative ({val}), which is invalid.",
                })
            else:
                results.append({
                    "check_name": f"positive_amount_{field}",
                    "result": "passed",
                    "observed_value": str(val),
                    "expected_value": ">= 0",
                    "message": f"{field.capitalize()} amount is valid ({val}).",
                })

    # 4. Arithmetic check: subtotal + tax == total
    subtotal = extracted.get("subtotal")
    tax = extracted.get("tax")
    total = extracted.get("total")

    if subtotal is not None and tax is not None and total is not None:
        expected_total = round(subtotal + tax, 2)
        actual_total = round(total, 2)
        diff = abs(expected_total - actual_total)
        if diff <= TOLERANCE:
            results.append({
                "check_name": "arithmetic_subtotal_plus_tax",
                "result": "passed",
                "observed_value": f"subtotal({subtotal}) + tax({tax}) = {expected_total}",
                "expected_value": f"total = {actual_total}",
                "message": f"Subtotal + Tax ({expected_total}) matches Total ({actual_total}).",
            })
        else:
            results.append({
                "check_name": "arithmetic_subtotal_plus_tax",
                "result": "failed",
                "observed_value": f"subtotal({subtotal}) + tax({tax}) = {expected_total}",
                "expected_value": f"total = {actual_total}",
                "message": f"Arithmetic mismatch: subtotal({subtotal}) + tax({tax}) = {expected_total}, but total is {actual_total}. Difference: {diff:.2f}.",
            })
    elif subtotal is None or total is None:
        results.append({
            "check_name": "arithmetic_subtotal_plus_tax",
            "result": "warning",
            "observed_value": f"subtotal={subtotal}, tax={tax}, total={total}",
            "expected_value": "All three amounts present",
            "message": "Cannot verify arithmetic — subtotal or total is missing.",
        })

    # 5. Tax rate consistency check
    # Only runs when the invoice explicitly states a tax_rate.
    # Never assumes a default rate — uses only the invoice's own stated rate.
    # Result is always "warning" (not "failed") because the tax base may legitimately
    # differ from the full subtotal (e.g. some line items may be tax-exempt).
    tax_rate = extracted.get("tax_rate")
    if tax_rate is not None and subtotal is not None and tax is not None:
        if subtotal > 0 and tax_rate > 0:
            expected_tax = round(subtotal * (tax_rate / 100), 2)
            actual_tax   = round(tax, 2)
            tax_diff     = abs(expected_tax - actual_tax)
            # Relative tolerance: 1% of expected tax (or at least 1 cent).
            # Tighter than the PO 2% threshold because tax errors are high-risk.
            tax_tol = max(TOLERANCE, round(0.01 * expected_tax, 2))
            if tax_diff > tax_tol:
                results.append({
                    "check_name": "tax_rate_consistency",
                    "result": "warning",
                    "observed_value": f"extracted tax = {actual_tax}",
                    "expected_value": f"{tax_rate}% of {subtotal} = {expected_tax}",
                    "message": (
                        f"Extracted tax ({actual_tax}) does not match stated rate: "
                        f"{tax_rate}% × {subtotal} = {expected_tax}. "
                        f"Difference: {tax_diff:.2f}. "
                        "Possible causes: partial tax exemption, incorrect rate extraction, "
                        "or compound tax. Human verification recommended."
                    ),
                })
            else:
                results.append({
                    "check_name": "tax_rate_consistency",
                    "result": "passed",
                    "observed_value": f"extracted tax = {actual_tax}",
                    "expected_value": f"{tax_rate}% of {subtotal} = {expected_tax}",
                    "message": (
                        f"Extracted tax ({actual_tax}) is consistent with stated rate "
                        f"({tax_rate}% of {subtotal} = {expected_tax})."
                    ),
                })

    # 6. Line item arithmetic check
    line_items = extracted.get("line_items") or []
    line_errors = []
    for idx, item in enumerate(line_items):
        qty = item.get("quantity")
        unit_price = item.get("unit_price")
        amount = item.get("amount")
        if qty is not None and unit_price is not None and amount is not None:
            expected = round(qty * unit_price, 2)
            if abs(expected - amount) > TOLERANCE:
                line_errors.append(
                    f"Line {idx + 1} '{item.get('description', '')}': "
                    f"{qty} × {unit_price} = {expected}, but amount is {amount}"
                )

    if line_errors:
        results.append({
            "check_name": "line_item_arithmetic",
            "result": "failed",
            "observed_value": "; ".join(line_errors),
            "expected_value": "qty × unit_price == amount for each line",
            "message": f"Line item arithmetic errors: {'; '.join(line_errors)}",
        })
    elif line_items:
        results.append({
            "check_name": "line_item_arithmetic",
            "result": "passed",
            "observed_value": f"{len(line_items)} line items checked",
            "expected_value": "qty × unit_price == amount for each line",
            "message": "All line item amounts match quantity × unit price.",
        })

    # 7. Extraction confidence
    confidence = extracted.get("confidence", 1.0)
    low_conf_fields = extracted.get("low_confidence_fields") or []
    if confidence < 0.6:
        results.append({
            "check_name": "extraction_confidence",
            "result": "warning",
            "observed_value": f"{confidence:.2f}",
            "expected_value": ">= 0.60",
            "message": f"Low extraction confidence ({confidence:.2f}). Uncertain fields: {', '.join(low_conf_fields) or 'unknown'}. Human review recommended.",
        })
    else:
        results.append({
            "check_name": "extraction_confidence",
            "result": "passed",
            "observed_value": f"{confidence:.2f}",
            "expected_value": ">= 0.60",
            "message": f"Extraction confidence is acceptable ({confidence:.2f}).",
        })

    return results


def get_missing_fields(extracted: dict) -> List[str]:
    """Return list of field names that are null/missing."""
    all_fields = [
        "vendor_name", "invoice_number", "invoice_date", "due_date",
        "po_number", "currency", "subtotal", "tax", "total",
        "tax_rate", "tax_id", "billing_address", "payment_terms",
    ]
    return [f for f in all_fields if not extracted.get(f)]

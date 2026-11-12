"""
Vendor Verification Service

Matches extracted vendor name/tax_id against the vendor master.
Uses fuzzy string matching so minor name variations still resolve correctly.

Match priority:
  1. Exact GSTIN/Tax ID match (most reliable — GSTIN is unique per vendor)
  2. Exact legal name match (case-insensitive, normalised whitespace)
  3. Exact alias match
  4. Fuzzy match against legal name and all aliases (token_set_ratio ≥ 75)
"""
import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from thefuzz import fuzz

from app.models.models import Vendor

# Minimum fuzzy score to consider a name match (0–100)
FUZZY_MATCH_THRESHOLD = 75


def _normalize_gstin(gstin: str) -> str:
    """
    Normalise a GSTIN/Tax ID for comparison.
    Removes all whitespace and uppercases — handles common OCR artefacts
    like spaces inserted in the middle of a 15-character GSTIN.
    """
    return re.sub(r'\s+', '', gstin.strip().upper())


def _normalize_name(name: str) -> str:
    """
    Normalise a vendor name for exact-match comparison.
    Collapses multiple consecutive spaces to a single space and lowercases.
    This catches OCR artefacts where extra spaces are introduced.
    """
    return re.sub(r'\s+', ' ', name.strip().lower())


def find_vendor(
    vendor_name: Optional[str],
    tax_id: Optional[str],
    db: Session,
) -> Tuple[Optional[Vendor], str, int]:
    """
    Attempt to match the extracted vendor against the vendor master.

    Returns:
        (vendor, match_method, match_score)
        match_method: 'exact_tax_id' | 'exact_name' | 'alias' | 'fuzzy' | 'no_match'
        match_score : 0–100 (100 = perfect)
    """
    all_vendors = db.query(Vendor).all()

    # 1. Exact GSTIN / Tax ID match (most reliable — unique per registered vendor)
    if tax_id:
        normalized_tax_id = _normalize_gstin(tax_id)
        for v in all_vendors:
            if v.tax_id:
                if _normalize_gstin(v.tax_id) == normalized_tax_id:
                    return v, "exact_tax_id", 100

    if not vendor_name:
        return None, "no_match", 0

    name_norm = _normalize_name(vendor_name)

    # 2. Exact legal name match (case-insensitive, normalised whitespace)
    for v in all_vendors:
        if _normalize_name(v.legal_name) == name_norm:
            return v, "exact_name", 100

    # 3. Alias match (case-insensitive, normalised whitespace)
    for v in all_vendors:
        for alias in (v.aliases or []):
            if _normalize_name(alias) == name_norm:
                return v, "alias", 100

    # 4. Fuzzy match against legal name and all aliases
    best_vendor = None
    best_score = 0
    best_method = "no_match"

    for v in all_vendors:
        # Score against legal name
        score = fuzz.token_set_ratio(name_norm, _normalize_name(v.legal_name))
        if score > best_score:
            best_score = score
            best_vendor = v
            best_method = "fuzzy"

        # Score against each alias
        for alias in (v.aliases or []):
            alias_score = fuzz.token_set_ratio(name_norm, _normalize_name(alias))
            if alias_score > best_score:
                best_score = alias_score
                best_vendor = v
                best_method = "fuzzy"

    if best_score >= FUZZY_MATCH_THRESHOLD:
        return best_vendor, best_method, best_score

    return None, "no_match", best_score


def verify_vendor(
    vendor_name: Optional[str],
    tax_id: Optional[str],
    db: Session,
) -> dict:
    """
    Full vendor verification result dict for the pipeline.
    """
    vendor, match_method, match_score = find_vendor(vendor_name, tax_id, db)

    if vendor is None:
        return {
            "matched": False,
            "vendor": None,
            "vendor_id": None,
            "match_method": "no_match",
            "match_score": match_score,
            "is_approved": False,
            "status": "unknown",
            "message": (
                f"Vendor '{vendor_name}' not found in vendor master "
                f"(best fuzzy score: {match_score}/100, threshold: {FUZZY_MATCH_THRESHOLD})."
            ),
        }

    return {
        "matched": True,
        "vendor": vendor,
        "vendor_id": vendor.id,
        "match_method": match_method,
        "match_score": match_score,
        "is_approved": vendor.is_approved,
        "status": vendor.status,
        "message": (
            f"Matched to '{vendor.legal_name}' via {match_method} "
            f"(score: {match_score}/100). Status: {vendor.status}."
        ),
    }

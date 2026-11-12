"""
AI Extraction Service

Uses Google Gemini (default) or OpenAI to convert raw invoice text
into a structured JSON object.

Design principle: AI handles document understanding only.
All financial calculations, matching, and decisions stay deterministic.
"""
import json
import re
from app.config import settings

EXTRACTION_SYSTEM_PROMPT = """You are a precise invoice data extraction assistant for an Accounts Payable system.

Your job is to extract structured fields from raw invoice text and return ONLY valid JSON.

Rules:
1. Extract ONLY information explicitly present in the text. Do NOT invent or infer missing data.
2. If a field is absent or unreadable, set it to null.
3. For amounts, return numbers only (no currency symbols or commas).
4. For dates, use ISO format YYYY-MM-DD when possible. If unparseable, return the raw string.
5. For line_items, extract each item with description, quantity, unit_price, and amount.
6. Return a confidence score (0.0 to 1.0) for the overall extraction quality.
7. List any fields you are uncertain about in the low_confidence_fields array.
8. Do NOT return markdown code blocks — return raw JSON only.

Required output format (all fields must be present, use null for missing):
{
  "vendor_name": string | null,
  "invoice_number": string | null,
  "invoice_date": string | null,
  "due_date": string | null,
  "po_number": string | null,
  "currency": string | null,
  "subtotal": number | null,
  "tax": number | null,
  "total": number | null,
  "tax_rate": number | null,
  "tax_id": string | null,
  "billing_address": string | null,
  "payment_terms": string | null,
  "line_items": [
    {
      "description": string,
      "quantity": number | null,
      "unit_price": number | null,
      "amount": number | null
    }
  ],
  "confidence": number,
  "low_confidence_fields": [string]
}"""


def _parse_response(content: str, ocr_confidence: float, provider: str) -> dict:
    """Parse and post-process the model's JSON response."""
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    extracted = json.loads(content)
    ai_confidence = float(extracted.get("confidence", 0.8))
    extracted["confidence"] = round((ai_confidence * 0.7) + (ocr_confidence * 0.3), 3)
    extracted["extraction_method"] = provider
    return _ensure_required_keys(extracted)


def _extract_gemini(raw_text: str, ocr_confidence: float) -> dict:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = (
        EXTRACTION_SYSTEM_PROMPT
        + f"\n\nExtract all invoice fields from the following text:\n\n{raw_text[:8000]}"
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return _parse_response(response.text, ocr_confidence, "gemini")


def _extract_openai(raw_text: str, ocr_confidence: float) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract all invoice fields from the following text:\n\n{raw_text[:8000]}"},
        ],
        temperature=0,
        max_tokens=1500,
    )
    return _parse_response(response.choices[0].message.content, ocr_confidence, "openai")


def extract_invoice_fields(raw_text: str, ocr_confidence: float = 1.0) -> dict:
    """
    Extract structured invoice fields from raw text using the configured AI provider.
    Raises an exception if extraction fails — pipeline handles it as a service failure.
    """
    if not raw_text or len(raw_text.strip()) < 20:
        raise ValueError("Insufficient text to extract invoice fields.")

    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
        return _extract_gemini(raw_text, ocr_confidence)

    elif provider == "openai":
        if not settings.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY is not configured or invalid.")
        return _extract_openai(raw_text, ocr_confidence)

    else:
        raise ValueError(f"Unknown AI_PROVIDER: '{provider}'. Use 'gemini' or 'openai'.")


def _ensure_required_keys(data: dict) -> dict:
    required_keys = [
        "vendor_name", "invoice_number", "invoice_date", "due_date",
        "po_number", "currency", "subtotal", "tax", "total", "tax_rate",
        "tax_id", "billing_address", "payment_terms", "line_items",
        "confidence", "low_confidence_fields",
    ]
    for key in required_keys:
        if key not in data:
            data[key] = [] if key in ("line_items", "low_confidence_fields") else None
    return data

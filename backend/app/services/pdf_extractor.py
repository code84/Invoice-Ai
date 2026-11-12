"""
PDF Classification and Text Extraction Service

Detects whether a PDF is digital (embedded text) or scanned (image-based),
then extracts raw text using PyMuPDF for digital PDFs or Tesseract OCR for scanned ones.
"""
import fitz  # PyMuPDF
import io
import os
from typing import Tuple

# Tesseract binary path (Windows)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Minimum character count to consider a page as having embedded text
MIN_TEXT_CHARS_PER_PAGE = 50


def _get_pytesseract():
    """Lazy import pytesseract and configure tesseract path."""
    import pytesseract as _pt
    if os.path.exists(TESSERACT_CMD):
        _pt.pytesseract.tesseract_cmd = TESSERACT_CMD
    return _pt


def extract_text(file_path: str) -> dict:
    """
    Master extraction function — opens the PDF exactly ONCE.
    Returns: { pdf_type, raw_text, confidence, text_ratio }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    # Open once, do everything, then close
    doc = fitz.open(file_path)

    try:
        total_pages = len(doc)
        if total_pages == 0:
            return {"pdf_type": "digital", "raw_text": "", "confidence": 0.0, "text_ratio": 0.0}

        # ── Step 1: Classify ───────────────────────────────────────────────
        text_pages = 0
        for page in doc:
            if len(page.get_text("text").strip()) >= MIN_TEXT_CHARS_PER_PAGE:
                text_pages += 1
        text_ratio = text_pages / total_pages
        pdf_type = "digital" if text_ratio >= 0.5 else "scanned"

        # ── Step 2: Extract ────────────────────────────────────────────────
        if pdf_type == "digital":
            pages_text = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages_text.append(f"[Page {page_num}]\n{text}")
            raw_text = "\n\n".join(pages_text)
            confidence = 1.0 if raw_text.strip() else 0.0

            # Fall back to OCR if too little text
            if len(raw_text.strip()) < 100:
                pdf_type = "scanned"
                raw_text, confidence = _ocr_doc(doc)
        else:
            raw_text, confidence = _ocr_doc(doc)

    finally:
        doc.close()

    return {
        "pdf_type": pdf_type,
        "raw_text": raw_text,
        "confidence": confidence,
        "text_ratio": text_ratio,
    }


def _ocr_doc(doc: fitz.Document, dpi: int = 100) -> Tuple[str, float]:
    """
    OCR all pages of an already-open fitz.Document.
    Uses image_to_string only (avoids pandas/numpy dependency).
    """
    from PIL import Image

    try:
        pt = _get_pytesseract()
    except Exception as e:
        return f"[OCR unavailable: {str(e)}]", 0.0

    pages_text = []

    for page_num, page in enumerate(doc, start=1):
        try:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_bytes = pix.tobytes("png")
            pix = None  # free memory immediately
            img = Image.open(io.BytesIO(img_bytes))
            page_text = pt.image_to_string(img)
            img.close()
            if page_text.strip():
                pages_text.append(f"[Page {page_num}]\n{page_text.strip()}")
        except Exception as e:
            pages_text.append(f"[Page {page_num}]\n[OCR error: {str(e)}]")

    combined = "\n\n".join(pages_text)
    char_count = len(combined.replace("\n", "").replace(" ", ""))
    # Cap scanned doc confidence at 0.65 — always requires human review
    confidence = round(min(0.65, max(0.1, char_count / 800)), 3) if pages_text else 0.0

    return combined, confidence

"""
Generate all 4 edge case test invoices.
EC-01: Duplicate (same vendor + invoice number, submitted twice)
EC-02: Missing invoice number
EC-03: PO amount mismatch (invoice total >> PO amount)
EC-04: Poor scan / OCR (image-based PDF, blurry text)
"""
import fitz
import io
import os
from PIL import Image, ImageFilter, ImageDraw, ImageFont

OUTPUT_DIR = "test_invoices"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_digital_pdf(filename: str, lines: list, title: str = "INVOICE"):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.draw_rect(fitz.Rect(0, 0, 595, 80), color=None, fill=(0.1, 0.2, 0.4))
    page.insert_text((40, 52), title, fontsize=22, color=(1, 1, 1), fontname="helv")
    y = 108
    for line in lines:
        if line.startswith("##"):
            y += 4
            page.insert_text((40, y), line[2:].strip(), fontsize=11,
                             color=(0.1, 0.2, 0.4), fontname="helv")
            y += 4
            page.draw_line((40, y), (555, y), color=(0.8, 0.8, 0.8), width=0.5)
            y += 10
        elif line.startswith("---"):
            page.draw_line((40, y), (555, y), color=(0.9, 0.9, 0.9), width=0.5)
            y += 8
        elif line == "":
            y += 7
        else:
            page.insert_text((40, y), line, fontsize=10, color=(0.1, 0.1, 0.1))
            y += 16
    path = os.path.join(OUTPUT_DIR, filename)
    doc.save(path)
    doc.close()
    return path


def make_scanned_pdf(filename: str, lines: list, blur_radius: float = 1.5,
                     noise_level: int = 20, title: str = "INVOICE"):
    """
    Creates a 'scanned' PDF by:
    1. Rendering a digital PDF to image
    2. Adding blur + noise to simulate scanner quality
    3. Re-embedding the degraded image into a new PDF
    """
    # Step 1: Create a clean digital PDF in memory
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.draw_rect(fitz.Rect(0, 0, 595, 80), color=None, fill=(0.3, 0.3, 0.3))
    page.insert_text((40, 52), title, fontsize=22, color=(1, 1, 1), fontname="helv")
    y = 108
    for line in lines:
        if line.startswith("##"):
            page.insert_text((40, y), line[2:].strip(), fontsize=11,
                             color=(0.2, 0.2, 0.2), fontname="helv")
            y += 18
        elif line.startswith("---"):
            y += 6
        elif line == "":
            y += 7
        else:
            page.insert_text((40, y), line, fontsize=10, color=(0.15, 0.15, 0.15))
            y += 16

    # Step 2: Render to image (simulate scanner at 150 DPI — lower quality)
    mat = fitz.Matrix(100 / 72, 100 / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Step 3: Degrade image to simulate poor scan quality
    # Add Gaussian blur
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    # Add random noise
    import random
    pixels = img.load()
    w, h = img.size
    for _ in range(w * h // 15):  # noise on ~7% of pixels
        x = random.randint(0, w - 1)
        y_p = random.randint(0, h - 1)
        r, g, b = pixels[x, y_p]
        noise = random.randint(-noise_level, noise_level)
        pixels[x, y_p] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise)),
        )
    # Slight rotation to simulate misaligned scan
    img = img.rotate(0.4, fillcolor=(255, 255, 255))

    # Step 4: Embed degraded image into a new image-only PDF
    doc.close()
    scan_doc = fitz.open()
    scan_page = scan_doc.new_page(width=595, height=842)
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    scan_page.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_buffer.read())

    path = os.path.join(OUTPUT_DIR, filename)
    scan_doc.save(path)
    scan_doc.close()
    print(f"Created scanned PDF: {path}")
    return path


# ── EC-01: Duplicate Invoice ───────────────────────────────────────────────────
# This is EXACTLY the same as the happy path invoice (same vendor + invoice number)
make_digital_pdf("ec01_duplicate.pdf", [
    "## Vendor Details",
    "Vendor Name:    ABC Technologies Pvt Ltd",
    "Tax ID:         TEST-TAX-001",
    "Address:        12 Tech Park, Bangalore, Karnataka 560001",
    "",
    "## Invoice Details",
    "Invoice Number: INV-2026-001",
    "Invoice Date:   10 November 2026",
    "Due Date:       10 December 2026",
    "PO Number:      PO-10045",
    "Currency:       INR",
    "Payment Terms:  Net 30",
    "",
    "## Line Items",
    "---",
    "Software subscription (annual)     1      45,000.00     45,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               45,000.00",
    "GST (18%):                                               8,100.00",
    "Total Amount Due:                                       53,100.00",
], title="INVOICE - DUPLICATE SUBMISSION")


# ── EC-02: Missing Invoice Number ─────────────────────────────────────────────
make_digital_pdf("ec02_missing_number.pdf", [
    "## Vendor Details",
    "Vendor Name:    XYZ Solutions Pvt Ltd",
    "Tax ID:         TEST-TAX-002",
    "Address:        78 Cyber City, Hyderabad 500081",
    "",
    "## Invoice Details",
    "Invoice Number: (number will be assigned separately)",
    "Invoice Date:   05 November 2026",
    "Due Date:       05 December 2026",
    "PO Number:      PO-10046",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Network switch (24-port)           2      8,000.00      16,000.00",
    "Ethernet patch cables (box)        5      1,000.00       5,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               21,000.00",
    "GST (18%):                                               3,780.00",
    "Total Amount Due:                                       24,780.00",
], title="INVOICE - NO NUMBER ASSIGNED")


# ── EC-03: PO Amount Mismatch ─────────────────────────────────────────────────
make_digital_pdf("ec03_po_mismatch.pdf", [
    "## Vendor Details",
    "Vendor Name:    ABC Technologies Pvt Ltd",
    "Tax ID:         TEST-TAX-001",
    "",
    "## Invoice Details",
    "Invoice Number: INV-2026-010",
    "Invoice Date:   08 November 2026",
    "Due Date:       08 December 2026",
    "PO Number:      PO-10045",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Software subscription (annual)     1      45,000.00     45,000.00",
    "Priority support package           1      25,000.00     25,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               70,000.00",
    "GST (18%):                                              12,600.00",
    "Total Amount Due:                                       82,600.00",
    "",
    "Note: Additional support package added per verbal agreement.",
], title="INVOICE - REVISED AMOUNT")


# ── EC-04: Poor Scan / OCR ────────────────────────────────────────────────────
# Image-only PDF with blur + noise — forces OCR path, low confidence
make_scanned_pdf("ec04_poor_scan.pdf", [
    "## Vendor Details",
    "Vendor Name:    Northstar Systems Ltd",
    "Tax ID:         TEST-TAX-004",
    "",
    "## Invoice Details",
    "Invoice Number: INV-NS-2026-088",
    "Invoice Date:   12 November 2026",
    "Due Date:       12 December 2026",
    "PO Number:      PO-10049",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Server rack unit                   1      22,457.63     22,457.63",
    "---",
    "## Summary",
    "Subtotal:                                               22,457.63",
    "GST (18%):                                               4,042.37",
    "Total Amount Due:                                       26,500.00",
], title="INVOICE", blur_radius=0.8, noise_level=12)

print("\nAll 4 edge case PDFs created.")

"""
Generate realistic test invoice PDFs for the happy path and edge cases.
Run: python create_test_invoices.py
"""
import fitz
import os

OUTPUT_DIR = "test_invoices"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_pdf(filename: str, content_lines: list[str], title: str = "INVOICE"):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Header bar
    page.draw_rect(fitz.Rect(0, 0, 595, 80), color=None, fill=(0.1, 0.2, 0.4))
    page.insert_text((40, 50), title, fontsize=24, color=(1, 1, 1), fontname="helv")

    y = 110
    for line in content_lines:
        if line.startswith("##"):  # Section header
            y += 5
            page.insert_text((40, y), line[2:].strip(), fontsize=11,
                             color=(0.1, 0.2, 0.4), fontname="helv")
            y += 5
            page.draw_line((40, y), (555, y), color=(0.8, 0.8, 0.8), width=0.5)
            y += 10
        elif line.startswith("---"):  # Divider
            page.draw_line((40, y), (555, y), color=(0.9, 0.9, 0.9), width=0.5)
            y += 8
        elif line == "":
            y += 8
        else:
            page.insert_text((40, y), line, fontsize=10, color=(0.1, 0.1, 0.1))
            y += 16

    path = os.path.join(OUTPUT_DIR, filename)
    doc.save(path)
    doc.close()
    print(f"Created: {path}")
    return path


# ── Invoice 1: Happy Path ─────────────────────────────────────────────────────
create_pdf("invoice_happy_path.pdf", [
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
    "## Bill To",
    "Acme Corp Accounts Payable",
    "45 Business Avenue, Mumbai 400001",
    "",
    "## Line Items",
    "---",
    "Description                        Qty    Unit Price    Amount",
    "---",
    "Software subscription (annual)     1      45,000.00     45,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               45,000.00",
    "GST (18%):                                               8,100.00",
    "Total Amount Due:                                       53,100.00",
    "",
    "## Bank Details",
    "Bank: HDFC Bank  |  Account: 1234567890  |  IFSC: HDFC0001234",
], title="INVOICE")


# ── Invoice 2: EC-02 Missing Invoice Number ───────────────────────────────────
create_pdf("invoice_missing_number.pdf", [
    "## Vendor Details",
    "Vendor Name:    XYZ Solutions Pvt Ltd",
    "Tax ID:         TEST-TAX-002",
    "Address:        78 Cyber City, Hyderabad 500081",
    "",
    "## Invoice Details",
    "Invoice Number: (not assigned yet)",
    "Invoice Date:   05 November 2026",
    "Due Date:       05 December 2026",
    "PO Number:      PO-10046",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Description                        Qty    Unit Price    Amount",
    "---",
    "Network switch (24-port)           2      8,000.00      16,000.00",
    "Ethernet patch cables (box)        5      1,000.00       5,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               21,000.00",
    "GST (18%):                                               3,780.00",
    "Total Amount Due:                                       24,780.00",
], title="INVOICE")


# ── Invoice 3: EC-03 PO Amount Mismatch ──────────────────────────────────────
create_pdf("invoice_po_mismatch.pdf", [
    "## Vendor Details",
    "Vendor Name:    ABC Technologies Pvt Ltd",
    "Tax ID:         TEST-TAX-001",
    "",
    "## Invoice Details",
    "Invoice Number: INV-2026-003",
    "Invoice Date:   08 November 2026",
    "Due Date:       08 December 2026",
    "PO Number:      PO-10045",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Description                        Qty    Unit Price    Amount",
    "---",
    "Software subscription (annual)     1      45,000.00     45,000.00",
    "Priority support package           1      25,000.00     25,000.00",
    "---",
    "## Summary",
    "Subtotal:                                               70,000.00",
    "GST (18%):                                              12,600.00",
    "Total Amount Due:                                       82,600.00",
], title="INVOICE")


# ── Invoice 4: EC-01 Duplicate (same as Invoice 1 resubmitted) ───────────────
create_pdf("invoice_duplicate.pdf", [
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
], title="INVOICE - RESUBMISSION")


# ── Invoice 5: Inactive Vendor ────────────────────────────────────────────────
create_pdf("invoice_inactive_vendor.pdf", [
    "## Vendor Details",
    "Vendor Name:    Global Services Inc",
    "Tax ID:         TEST-TAX-003",
    "Address:        99 Old Road, Delhi 110001",
    "",
    "## Invoice Details",
    "Invoice Number: INV-GS-2026-055",
    "Invoice Date:   01 November 2026",
    "Due Date:       01 December 2026",
    "PO Number:      PO-10047",
    "Currency:       INR",
    "",
    "## Line Items",
    "---",
    "Consulting services               100      635.59      63,559.00",
    "---",
    "## Summary",
    "Subtotal:                                              63,559.00",
    "GST (18%):                                             11,440.62",
    "Total Amount Due:                                      75,000.00",
], title="INVOICE")

print("\nAll test invoices created in:", OUTPUT_DIR)

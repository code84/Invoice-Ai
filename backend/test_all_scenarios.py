"""
Full End-to-End Test Suite â€” All 5 Scenarios
Runs Happy Path first, then all 4 edge cases.
Verifies expected outcomes for each.
"""
import requests, time, sys

BASE = "http://localhost:8000"
PASS = "PASS"
FAIL = "FAIL"
results = []

def upload_and_wait(pdf_path, label):
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print(f"{'='*60}")

    with open(pdf_path, "rb") as f:
        fname = pdf_path.split("/")[-1]
        r = requests.post(f"{BASE}/api/invoices/upload",
                          files={"file": (fname, f, "application/pdf")})
    if r.status_code != 200:
        print(f"  UPLOAD FAILED: {r.status_code} {r.text}")
        return None, None

    run = r.json()
    run_uuid = run["id"]
    print(f"  Run ID   : {run['run_id']}")

    for i in range(40):
        time.sleep(2)
        data = requests.get(f"{BASE}/api/invoices/runs/{run_uuid}").json()
        if data["status"] in ("completed", "failed"):
            print(f"  Finished : {i*2}s â€” run status: {data['status']}")
            break
        print(f"  [{i*2}s] stage={data['current_stage']}")

    inv = requests.get(f"{BASE}/api/invoices/{data['invoice_id']}").json()
    print(f"  Vendor   : {inv['vendor_name']}")
    print(f"  Invoice# : {inv['invoice_number']}")
    print(f"  Total    : {inv['total']}")
    print(f"  PDF type : {inv['pdf_type']}")
    print(f"  Confidence:{inv['extraction_confidence']}")
    print(f"  Duplicate: {inv['is_duplicate']}")
    print(f"  STATUS   : {inv['final_status']}")
    print(f"  Decision : {(inv['decision_explanation'] or '')[:120]}")
    print(f"  Action   : {inv['recommended_action']}")
    return inv, data


def check(label, inv, expected_status, expected_duplicate=False,
          expected_inv_number_none=False, check_fn=None):
    passed = True
    issues = []

    if inv["final_status"] != expected_status:
        passed = False
        issues.append(f"status={inv['final_status']} expected={expected_status}")
    if inv["is_duplicate"] != expected_duplicate:
        passed = False
        issues.append(f"is_duplicate={inv['is_duplicate']} expected={expected_duplicate}")
    if expected_inv_number_none and inv["invoice_number"] is not None:
        passed = False
        issues.append(f"invoice_number should be None, got={inv['invoice_number']}")
    if check_fn:
        ok, msg = check_fn(inv)
        if not ok:
            passed = False
            issues.append(msg)

    status = PASS if passed else FAIL
    results.append((label, status, issues))
    print(f"\n  >>> {status}: {label}")
    if issues:
        for i in issues:
            print(f"       - {i}")
    return passed


# â”€â”€ HAPPY PATH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inv, run = upload_and_wait("test_invoices/invoice_happy_path.pdf", "Happy Path")
if inv:
    check("Happy Path â†’ approved", inv,
          expected_status="approved",
          expected_duplicate=False)

# â”€â”€ EC-01: DUPLICATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inv, run = upload_and_wait("test_invoices/ec01_duplicate.pdf", "EC-01: Duplicate Invoice")
if inv:
    check("EC-01 â†’ rejected (duplicate)", inv,
          expected_status="rejected",
          expected_duplicate=True)

# â”€â”€ EC-02: MISSING INVOICE NUMBER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inv, run = upload_and_wait("test_invoices/ec02_missing_number.pdf", "EC-02: Missing Invoice Number")
if inv:
    check("EC-02 â†’ needs_review (no inv#)", inv,
          expected_status="needs_review",
          expected_inv_number_none=True)

# â”€â”€ EC-03: PO AMOUNT MISMATCH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inv, run = upload_and_wait("test_invoices/ec03_po_mismatch.pdf", "EC-03: PO Amount Mismatch")
if inv:
    def check_variance(i):
        exp = i["decision_explanation"] or ""
        ok = "variance" in exp.lower() or "tolerance" in exp.lower() or "mismatch" in exp.lower()
        return ok, "decision should mention variance/tolerance"
    check("EC-03 â†’ needs_review (PO mismatch)", inv,
          expected_status="needs_review",
          check_fn=check_variance)

# â”€â”€ EC-04: POOR SCAN / OCR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inv, run = upload_and_wait("test_invoices/ec04_poor_scan.pdf", "EC-04: Poor Scan / OCR")
if inv:
    def check_ocr(i):
        is_scanned = i.get("pdf_type") == "scanned"
        return is_scanned, f"pdf_type should be 'scanned', got {i.get('pdf_type')}"
    check("EC-04 â†’ scanned PDF + needs_review", inv,
          expected_status="needs_review",
          check_fn=check_ocr)

# â”€â”€ SUMMARY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")
all_pass = True
for label, status, issues in results:
    icon = "âœ“" if status == PASS else "âœ—"
    print(f"  {icon} {status}  {label}")
    if issues:
        for i in issues:
            print(f"          {i}")
    if status == FAIL:
        all_pass = False

print(f"\n{'='*60}")
print(f"Overall: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
print(f"{'='*60}")

# Dashboard summary
dash = requests.get(f"{BASE}/api/dashboard/").json()
print(f"\nDashboard: {dash['total_processed']} processed | "
      f"{dash['approved']} approved | "
      f"{dash['needs_review']} review | "
      f"{dash['flagged']} flagged")

sys.exit(0 if all_pass else 1)


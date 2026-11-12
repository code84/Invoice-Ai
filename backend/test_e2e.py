"""Full end-to-end test simulating what the UI does."""
import requests, time

BASE = "http://localhost:8000"

print("=== STEP 1: Upload invoice ===")
with open("test_invoices/invoice_happy_path.pdf", "rb") as f:
    r = requests.post(f"{BASE}/api/invoices/upload",
                      files={"file": ("invoice_happy_path.pdf", f, "application/pdf")})
print(f"  Status: {r.status_code}")
run = r.json()
run_uuid = run["id"]
print(f"  Run ID: {run['run_id']}")

print("\n=== STEP 2: Poll run until complete ===")
for i in range(20):
    time.sleep(2)
    r = requests.get(f"{BASE}/api/invoices/runs/{run_uuid}")
    data = r.json()
    if data["status"] in ("completed", "failed"):
        print(f"  Finished in ~{i*2}s — status: {data['status']}")
        break
    print(f"  [{i*2}s] stage={data['current_stage']}")

print("\n=== STEP 3: Fetch invoice detail ===")
invoice_id = data["invoice_id"]
inv = requests.get(f"{BASE}/api/invoices/{invoice_id}").json()
print(f"  Vendor        : {inv['vendor_name']}")
print(f"  Invoice #     : {inv['invoice_number']}")
print(f"  Total         : {inv['total']}")
print(f"  Final status  : {inv['final_status']}")
print(f"  Decision      : {(inv['decision_explanation'] or '')[:80]}")

print("\n=== STEP 4: Dashboard stats ===")
dash = requests.get(f"{BASE}/api/dashboard/").json()
print(f"  Total processed : {dash['total_processed']}")
print(f"  Approved        : {dash['approved']}")
print(f"  Needs review    : {dash['needs_review']}")
print(f"  Flagged         : {dash['flagged']}")

print("\n=== ALL STEPS PASSED ===")

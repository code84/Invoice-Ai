import requests
import time

# Upload happy path invoice
with open('test_invoices/invoice_happy_path.pdf', 'rb') as f:
    resp = requests.post(
        'http://localhost:8000/api/invoices/upload',
        files={'file': ('invoice_happy_path.pdf', f, 'application/pdf')}
    )

print('Upload status:', resp.status_code)
run = resp.json()
print('Run ID:', run['run_id'])
run_uuid = run['id']

# Poll until pipeline completes
for i in range(30):
    time.sleep(2)
    r = requests.get('http://localhost:8000/api/invoices/runs/' + run_uuid)
    data = r.json()
    status = data['status']
    stage = data['current_stage']
    print(f'  [{i*2}s] status={status} stage={stage}')
    if status in ('completed', 'failed'):
        break

print()
print('Final run status:', data['status'])
stages = sorted(data['stages'], key=lambda s: s['order_index'])
for s in stages:
    label = s['stage_label']
    st = s['status']
    summary = (s['output_summary'] or '')[:70]
    print(f'  {label:28s} -> {st:10s} | {summary}')

print()
print('Validation results:')
for vr in data['validation_results']:
    print(f'  {vr["check_name"]:35s} -> {vr["result"]:8s} | {vr["message"][:60]}')

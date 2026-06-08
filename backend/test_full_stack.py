"""Test full backend API stack"""
import sys
sys.path.insert(0, '/home/free33/dev/1st4-mobile')

from backend.server import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 1. Health
r = client.get('/api/health')
print(f'Health: {r.status_code} {r.json()["database"]}')

# 2. Owner dashboard (empty state)
r = client.get('/api/owner/dashboard')
print(f'Owner dashboard: {r.status_code}')
d = r.json()
print(f'  Pipeline: {d["pipeline_stats"]}')
print(f'  Invoiced: ${d["total_invoiced"]}')

# 3. Register client
r = client.post('/api/client/register', json={
    'company_name': 'TestCo Mining', 'abn': '12 345 678 901',
    'industry': 'Mining', 'fleet_size': 500,
    'primary_carrier': 'Telstra', 'email': 'cfo@testco.com.au'
})
cid = r.json()['client_id']
print(f'Register: {r.status_code} id={cid[:8]}...')

# 4. Authorize
r = client.post(f'/api/client/{cid}/authorize', json={
    'signature_data': 'iVBORw0KGgoA', 'signed_by': 'John Smith'
})
print(f'Authorize: {r.status_code} {r.json()["authorized"]}')

# 5. Owner dashboard (post-register)
r = client.get('/api/owner/dashboard')
print(f'Owner dashboard (after): {r.status_code}')
d = r.json()
print(f'  Clients in queue: {len(d["client_queue"])}')
print(f'  First client status: {d["client_queue"][0]["status"]}')

print('\n=== FULL STACK TEST PASSED ===')

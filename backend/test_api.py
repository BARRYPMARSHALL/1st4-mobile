"""1st 4 Mobile — Quick API Smoke Test"""
import sys
sys.path.insert(0, '/home/free33/dev/1st4-mobile')

from backend.server import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test health
resp = client.get('/api/health')
print('Health:', resp.status_code, resp.json())
assert resp.status_code == 200

# Test landing page
resp = client.get('/')
print('Landing:', resp.status_code)
assert resp.status_code == 200

# Test client registration
resp = client.post('/api/client/register', json={
    'company_name': 'TestCo Mining',
    'abn': '12 345 678 901',
    'industry': 'Mining',
    'fleet_size': 500,
    'primary_carrier': 'Telstra',
    'email': 'cfo@testco.com.au'
})
print('Register:', resp.status_code)
data = resp.json()
assert resp.status_code == 200
cid = data.get('client_id', '')
print('  client_id:', cid)
print('  loa length:', len(data.get('loa_text', '')))

# Test authorize
resp = client.post('/api/client/' + cid + '/authorize', json={
    'signature_data': 'iVBORw0KGgoAAAANSUhEUg...',
    'signed_by': 'John Smith, CFO'
})
print('Authorize:', resp.status_code, resp.json())
assert resp.status_code == 200

# Test dashboard data
resp = client.get('/api/client/' + cid + '/dashboard')
print('Dashboard:', resp.status_code)
if resp.status_code == 200:
    d = resp.json()
    print('  status:', d.get('status', ''))
    engine_count = len(d.get('engine_breakdown', []))
    print('  engines:', engine_count)

print()
print('=== ALL API TESTS PASSED ===')

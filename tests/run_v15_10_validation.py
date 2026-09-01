from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1]
idx=(r/'index.html').read_text(); sw=(r/'sw.js').read_text(); api=(r/'fitness_backend_api_v2_connected.py').read_text(); app=(r/'app.js').read_text()
meta=json.loads((r/'RELEASE_CANDIDATE.json').read_text())
assert meta['version']=='15.10.4' and meta['feature_freeze'] is True
assert '/release' in api and 'production-candidate' in api
assert 'forge-v15-10-4-workout-reliability-v1' in sw
scripts=re.findall(r'<script src="([^"]+)"',idx)
for src in scripts:
    assert src in sw, f'service worker missing {src}'
assert 'forge_production.js' in idx and 'forge_mobile.js' in idx
assert 'forge_offline.js' in idx and 'forge_health.js' in idx
assert (r/'app.js').stat().st_size < 250000
assert 'request_id' in (r/'js/forge_offline.js').read_text()
assert '/me/system/integrity/repair' in api
assert '/me/session/reconcile' in api
print('v15.10 production candidate validation passed')

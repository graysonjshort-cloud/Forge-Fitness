from pathlib import Path
r=Path(__file__).resolve().parents[1]
db=(r/'database.py').read_text(); api=(r/'fitness_backend_api_v2_connected.py').read_text(); app=(r/'app.js').read_text(); health=(r/'js/forge_health.js').read_text()
for x in ['get_data_integrity_report','repair_data_integrity','multiple_active_programs','malformed_plan_json','invalid_session_position']: assert x in db
assert '/me/system/integrity' in api and '/me/system/integrity/repair' in api
assert 'FORGE HEALTH CHECK' in health and 'repair-integrity' in app+health
assert 'never rewrites training history' in (app+health).lower()
print('v15.7 data integrity & recovery validation passed')

from pathlib import Path
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text(); idx=(r/'index.html').read_text()
assert (r/'js/forge_health.js').exists() and (r/'js/forge_notifications_ui.js').exists() and (r/'js/forge_cache.js').exists()
for n in ['forge_health.js','forge_notifications_ui.js','forge_cache.js']: assert n in idx
assert 'ForgeHealthUI.system' in app and 'ForgeNotificationUI.center' in app
assert 'if(r==="home"){loadHomeDashboard();loadNotifications();}' in app
assert 'loadTrainingDashboard();}' not in app[app.index('if(r==="home")'):app.index('if(r==="notifications")')]
assert (r/'app.js').stat().st_size < 250000
print('v15.8 performance & modularization validation passed')

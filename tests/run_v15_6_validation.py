from pathlib import Path
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text(); frontend=app+'\n'+'\n'.join(x.read_text() for x in (r/'js').glob('*.js')); api=(r/'fitness_backend_api_v2_connected.py').read_text(); db=(r/'database.py').read_text(); mod=(r/'js/forge_notifications.js').read_text(); idx=(r/'index.html').read_text()
for key in ['browser_notifications','missed_workout_reminders','incomplete_workout_reminders','recovery_reminders','deload_reminders','schedule_change_alerts']:
    assert key in api and key in db
assert 'ForgeNotifications.permission()' in frontend
assert 'ForgeNotifications.deliver' in frontend
assert 'showNotification' in mod and 'Notification.requestPermission' in mod
assert 'forge_notifications.js' in idx
print('v15.6 notifications & workout reminders validation passed')

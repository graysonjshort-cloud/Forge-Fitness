from pathlib import Path
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text(); off=(r/'js/forge_offline.js').read_text(); idx=(r/'index.html').read_text(); combined=app+off
assert 'forge_offline.js' in idx
assert 'queueable:true' in app
assert 'replayOfflineWorkoutWrites' in app
assert 'request_id' in off and 'session_changed' in off
assert 'Offline — workout is still being saved' in combined
assert 'enqueue(path,opt' in off and 'ForgeOffline.request' in app
print('v15.3 offline workout reliability validation passed')

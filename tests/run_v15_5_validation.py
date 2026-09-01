from pathlib import Path
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text()
assert 'FORGE RECOMMENDATION' in app
assert 'Start Today’s Workout' in app
assert 'READINESS' in app and 'NUTRITION' in app
assert 'Coming Up' in app and 'This Week' in app
assert '${trainingDashboardCard()}' not in app[app.index('function home(){'):app.index('function moduleExerciseTarget')]
print('v15.5 Home 4.0 validation passed')

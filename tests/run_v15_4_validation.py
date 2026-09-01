from pathlib import Path
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text(); css=(r/'styles.css').read_text()
for x in ['focus-workout-top','focus-target','focus-inputs','focus-complete','FORGE ADJUSTMENT']: assert x in app or x in css,x
assert 'data-a=completeset' in app and 'data-a=swap-exercise' in app
assert 'exerciseRecallMarkup(e)' in app and 'exerciseProgressionCard()' in app
print('v15.4 workout screen redesign validation passed')

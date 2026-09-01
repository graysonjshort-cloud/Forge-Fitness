from pathlib import Path
r=Path(__file__).resolve().parents[1];a=(r/'app.js').read_text();c=(r/'styles.css').read_text()
for x in ['PROGRAM CHANGES','EXERCISE CHANGES','Review before applying','SESSION PLAN','NEXT STEP','adaptation-decision','workout-context']: assert x in a+c
assert (r/'app.js').stat().st_size<250000
print('v15.10.2 progression UI validation passed')

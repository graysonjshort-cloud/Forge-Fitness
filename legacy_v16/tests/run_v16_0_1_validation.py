from pathlib import Path
r=Path(__file__).resolve().parents[1]
css=(r/'styles.css').read_text(); idx=(r/'index.html').read_text(); sw=(r/'sw.js').read_text()
for token in [
    'v16.0.1 — Adaptation recommendation layout fix',
    'grid-template-columns:minmax(0,1fr)!important',
    'word-break:normal!important',
    'overflow-wrap:normal!important',
    '@container (min-width:760px)',
    'container-type:inline-size'
]: assert token in css, token
assert '/styles.css?v=16.0.1' in idx
assert 'forge-v16-0-1-adaptation-layout-v1' in sw
assert (r/'app.js').stat().st_size < 100000
print('v16.0.1 adaptation layout validation passed')

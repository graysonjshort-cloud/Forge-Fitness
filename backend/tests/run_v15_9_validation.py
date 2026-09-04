from pathlib import Path
r=Path(__file__).resolve().parents[1]
idx=(r/'index.html').read_text(); css=(r/'styles.css').read_text(); mob=(r/'js/forge_mobile.js').read_text(); app=(r/'app.js').read_text(); frontend=app+'\n'+'\n'.join(x.read_text() for x in (r/'js').glob('*.js'))
assert 'forge_mobile.js' in idx
for x in ['safe-area-inset-top','safe-area-inset-bottom','keyboard-open','min-width:44px','max-width:340px','display-mode:standalone']: assert x in css,x
assert 'visualViewport' in mob and 'scrollIntoView' in mob and 'ForgeMobile.loading' in frontend
assert (r/'app.js').stat().st_size < 250000
print('v15.9 UX/mobile polish validation passed')

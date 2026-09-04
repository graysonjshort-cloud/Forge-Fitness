from pathlib import Path
import re,collections,json
r=Path(__file__).resolve().parents[1]
app=(r/"app.js").read_text()
css=(r/"styles.css").read_text()
idx=(r/"index.html").read_text()
modules="\n".join(x.read_text() for x in (r/"js").glob("*.js")); all_frontend=app+"\n"+modules

# Route/pathway consistency.
m=re.search(r'function render\(\)\{const map=\{(.*?)\};V\.innerHTML',app,re.S)
assert m,"route map missing"
routes={x.split(":",1)[0].strip() for x in m.group(1).split(",")}
go_routes=set(re.findall(r'go\("([A-Za-z0-9_-]+)"\)',app))
assert not (go_routes-routes),f"unmapped go routes: {sorted(go_routes-routes)}"

# Every declarative data-a action has an action handler.
actions=set(re.findall(r'data-a=([A-Za-z0-9_-]+)',all_frontend))|set(re.findall(r'data-a="([A-Za-z0-9_-]+)"',all_frontend))
handlers=set(re.findall(r'a==="([A-Za-z0-9_-]+)"',app))
assert not (actions-handlers),f"unhandled actions: {sorted(actions-handlers)}"

# Duplicate named functions are a logic hazard (the old timer override was one).
names=re.findall(r'\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',app)
dupes=[n for n,c in collections.Counter(names).items() if c>1]
assert not dupes,f"duplicate functions: {dupes}"

# Restored set controls and safety.
for token in ["data-setchange=-1","data-setchange=1","adjustCurrentSets","hasManualSetOverride","exercise-sets"]:
    assert token in all_frontend,token
assert "Math.max(1,session?S.set+1:1)" in app
assert "Reconnect to change sets" in all_frontend
assert "set-count-control" in css and "focus-prescription" in css

# Previously dead Favorites pathway is now handled.
assert 'a==="nutrition-favorites-only"' in app
assert "nutritionFavoritesOnly" in all_frontend

# Visible release strings should not regress.
assert "v14.61.0" not in all_frontend
assert "Forge Fitness v15." in all_frontend
assert "15.11." in idx
assert (r/"app.js").stat().st_size < 250000
print("v15.10.4 UI/pathway cleanup validation passed")

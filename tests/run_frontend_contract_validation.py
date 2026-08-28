from __future__ import annotations
import ast, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
API=(ROOT/'fitness_backend_api_v2_connected.py').read_text(encoding='utf-8')

# Backend route contracts from FastAPI decorators.
route_re=re.compile(r'@app\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
routes={(m.upper(),p) for m,p in route_re.findall(API)}

def canonical(path:str)->str:
    path=re.sub(r'\$\{[^}]+\}', '{x}', path)
    path=re.sub(r'\{[^}]+\}', '{x}', path)
    return path.split('?')[0]

def compatible(front,back):
    a=canonical(front).strip('/').split('/') if front!='/' else []
    b=canonical(back).strip('/').split('/') if back!='/' else []
    if len(a)!=len(b): return False
    return all(x==y or x=='{x}' or y=='{x}' for x,y in zip(a,b))

# Find api("/path", {...}) and api(`/path/${id}`, {...}) calls. Method defaults GET.
call_re=re.compile(r'\bapi\(\s*(["\'`])(/[^"\'`]+)\1\s*(?:,\s*\{([^}]{0,500})\})?',re.S)
calls=[]
for q,path,opt in call_re.findall(APP):
    mm=re.search(r'\bmethod\s*:\s*["\'](GET|POST|PUT|DELETE|PATCH)["\']',opt or '',re.I)
    method=(mm.group(1).upper() if mm else 'GET')
    calls.append((method,path))

missing=[]
for method,path in calls:
    if not any(method==bm and compatible(path,bp) for bm,bp in routes):
        missing.append({'method':method,'frontend_path':path})

# Detect likely raw fetches that bypass Forge's shared authenticated api() helper.
raw_fetch=[]
for m in re.finditer(r'\bfetch\s*\(([^\n;]{1,240})',APP):
    snippet=m.group(0)
    # The one fetch inside api() itself is intentional.
    before=APP[max(0,m.start()-220):m.start()]
    if 'async function api(' not in before:
        raw_fetch.append(snippet[:220])

report={'status':'passed' if not missing and not raw_fetch else 'failed','frontend_api_calls_checked':len(calls),'backend_routes_found':len(routes),'missing_contracts':missing,'raw_fetch_bypasses':raw_fetch}
(ROOT/'V14_38_2_FRONTEND_CONTRACT_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if report['status']!='passed': sys.exit(1)

from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright

SOURCE=Path(__file__).resolve().parents[1]
PORT=int(os.environ.get('FORGE_BROWSER_TEST_PORT','8871'))
BASE=f'http://127.0.0.1:{PORT}'

def req(method,path,body=None,token=None):
    data=None if body is None else json.dumps(body).encode()
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']=f'Bearer {token}'
    r=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(r,timeout=20) as res:
        raw=res.read().decode(); return res.status, json.loads(raw) if raw else {}

def wait_server():
    for _ in range(120):
        try:
            if req('GET','/health')[0]==200:return
        except Exception: time.sleep(.1)
    raise RuntimeError('server did not start')

def seed_user():
    email=f'browser-{int(time.time()*1000)}@forge.test'
    _,reg=req('POST','/auth/register',{'email':email,'password':'ForgeBrowser123!','display_name':'Browser Tester'})
    token=reg['token']
    profile={'goal':'build_muscle','experience':'intermediate','days_per_week':4,'minutes_per_workout':45,
             'equipment':['full_gym'],'preferred_exercises':[],'excluded_exercises':[],'priority_muscles':[],
             'recovery_level':'normal','cardio_preference':'moderate','workout_split':'upper_lower','sport':'general',
             'core_workouts_per_week':2,'cardio_workouts_per_week':2,'seed':14381}
    req('POST','/me/profile',profile,token)
    req('POST','/me/plan/generate',{},token)
    return token

def main():
    runtime=Path(tempfile.mkdtemp(prefix='forge_browser_'))
    shutil.copytree(SOURCE,runtime/'app',ignore=shutil.ignore_patterns('__pycache__','*.zip','tests'),dirs_exist_ok=True)
    env=os.environ.copy();env.update({'FORGE_LLM_ENABLED':'0','NUTRITION_LOOKUP_ENABLED':'0','PYTHONPATH':str(runtime/'app')})
    p=subprocess.Popen([sys.executable,'-m','uvicorn','fitness_backend_api_v2_connected:app','--host','127.0.0.1','--port',str(PORT)],cwd=runtime/'app',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    errors=[];console_errors=[];failed_requests=[];screens=[]
    try:
        wait_server();token=seed_user()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'), args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':390,'height':844}, service_workers='block')
            # Chromium networking is blocked in this execution environment, so the real
            # frontend is executed in-page while all Forge API calls are intercepted and
            # proxied by Python to the real FastAPI test server.
            from urllib.parse import urlparse
            def api_bridge(route):
                r=route.request; u=urlparse(r.url)
                body=r.post_data_buffer
                headers={k:v for k,v in r.headers.items() if k.lower() not in {'host','content-length','origin','referer'}}
                target=BASE+u.path+('?' + u.query if u.query else '')
                q=urllib.request.Request(target,data=body if body else None,headers=headers,method=r.method)
                try:
                    with urllib.request.urlopen(q,timeout=20) as res:
                        route.fulfill(status=res.status,body=res.read(),headers={'Content-Type':res.headers.get('Content-Type','application/json'),'Access-Control-Allow-Origin':'*'})
                except urllib.error.HTTPError as e:
                    route.fulfill(status=e.code,body=e.read(),headers={'Content-Type':e.headers.get('Content-Type','application/json'),'Access-Control-Allow-Origin':'*'})
            context.route('http://forge.test/**', api_bridge)
            page=context.new_page()
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            page.on('console', lambda msg: console_errors.append(msg.text) if msg.type=='error' else None)
            page.on('requestfailed', lambda r: failed_requests.append(f'{r.method} {r.url}: {r.failure}'))
            html=(runtime/'app'/'index.html').read_text(encoding='utf-8')
            html=re.sub(r'<link rel="manifest"[^>]*>','',html); html=re.sub(r'<link rel="apple-touch-icon"[^>]*>','',html); html=re.sub(r'<link rel="stylesheet"[^>]*>','',html); html=re.sub(r'<script src="/app\.js[^"]*"></script>','',html)
            css=(runtime/'app'/'styles.css').read_text(encoding='utf-8')
            html=html.replace('</head>',f'<style>{css}</style></head>')
            page.set_content(html,wait_until='domcontentloaded')
            js=(runtime/'app'/'app.js').read_text(encoding='utf-8')
            js=js.replace('const API = localStorage.getItem("forge_api_url") || (\n  location.protocol==="https:" ? location.origin : `http://${location.hostname}:8000`\n);', 'const API = "http://forge.test";')
            js=js.replace('let authToken = localStorage.getItem("forge_auth_token") || "";', 'let authToken = '+json.dumps(token)+';')
            page.add_script_tag(content=js)
            page.wait_for_selector('#bottomNav:not(.hidden)',timeout=15000)
            assert 'Forge' in page.title()
            assert page.locator('[data-nav="home"]').count()==1

            # Exercise every primary browser route and allow async loaders to settle.
            for route in ['home','plan','workout','progress','nutrition','coach']:
                page.locator(f'#bottomNav [data-nav="{route}"]').click()
                page.wait_for_timeout(700)
                assert page.locator('#view').inner_text().strip(), f'{route} rendered empty'
                screens.append(route)

            # Regression: provider diagnostics must use the shared API helper and not throw API_BASE ReferenceError.
            page.locator('#bottomNav [data-nav="nutrition"]').click();page.wait_for_timeout(400)
            btn=page.locator('#nutritionProviderStatusBtn')
            if btn.count():
                page.once('dialog', lambda d: d.accept())
                btn.click();page.wait_for_timeout(500)

            # Regression: online event must not throw undefined-token ReferenceError.
            page.evaluate("window.dispatchEvent(new Event('online'))")
            page.wait_for_timeout(300)

            # Open More sheet to cover account-dependent global UI.
            page.locator('#moreBtn').click();page.wait_for_timeout(250)
            assert page.locator('.more-sheet').count()==1
            browser.close()

        fatal=[x for x in errors if 'ResizeObserver loop' not in x]
        bad_console=[x for x in console_errors if not any(ok in x.lower() for ok in ['favicon','service worker'])]
        bad_requests=[x for x in failed_requests if not any(ok in x for ok in ['favicon.ico'])]
        if fatal or bad_console or bad_requests:
            raise AssertionError(json.dumps({'page_errors':fatal,'console_errors':bad_console,'failed_requests':bad_requests},indent=2))
        report={'status':'passed','viewport':'390x844','routes':screens,'checks':['authenticated startup','primary nav rendering','no page errors','no console errors','no failed requests','nutrition provider status regression','online-event regression','More sheet']}
        print(json.dumps(report,indent=2))
        (SOURCE/'V14_38_1_BROWSER_SMOKE_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    finally:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill()
        shutil.rmtree(runtime,ignore_errors=True)

if __name__=='__main__': main()

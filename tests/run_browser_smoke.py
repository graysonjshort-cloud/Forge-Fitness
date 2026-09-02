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
    errors=[];console_errors=[];failed_requests=[];screens=[];request_counts={}
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
                request_counts[u.path]=request_counts.get(u.path,0)+1
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
            html=re.sub(r'<link rel="manifest"[^>]*>','',html); html=re.sub(r'<link rel="apple-touch-icon"[^>]*>','',html); html=re.sub(r'<link rel="stylesheet"[^>]*>','',html); html=re.sub(r'<script src="/(?:js/[^"]+|app\.js[^"]*)"></script>','',html)
            css=(runtime/'app'/'styles.css').read_text(encoding='utf-8')
            html=html.replace('</head>',f'<style>{css}</style></head>')
            page.set_content(html,wait_until='domcontentloaded')
            module_scripts=re.findall(r'<script src="/js/([^"?]+)(?:\?[^"]*)?"></script>',(runtime/'app'/'index.html').read_text(encoding='utf-8'))
            for module in module_scripts:
                page.add_script_tag(content=(runtime/'app'/'js'/module).read_text(encoding='utf-8'))
            assert page.evaluate("typeof ForgeCore==='object' && typeof ForgeApi.request==='function' && typeof ForgeEquipment.icon==='function' && typeof ForgePWA.create==='function'")
            js=(runtime/'app'/'app.js').read_text(encoding='utf-8')
            js=re.sub(r'const API = localStorage\.getItem\("forge_api_url"\) \|\| \(\s*location\.protocol==="https:" \? location\.origin : `http://\$\{location\.hostname\}:8000`\s*\);', 'const API = "http://forge.test";', js)
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

            # v14.74.1 regression: exercise history/progression must not refetch on harmless rerenders.
            page.locator('#bottomNav [data-nav="workout"]').click();page.wait_for_timeout(300)
            exbtn=page.locator('[data-ex]').first
            if exbtn.count():
                exbtn.click();page.wait_for_timeout(1000)
                exercise_id=page.evaluate("w().exercises[S.ei].exercise_id")
                history_path=f'/me/exercises/{exercise_id}/history'
                progression_path=f'/me/exercises/{exercise_id}/progression-strategy'
                history_before=request_counts.get(history_path,0)
                progression_before=request_counts.get(progression_path,0)
                page.evaluate("render()")
                page.wait_for_timeout(500)
                assert request_counts.get(history_path,0)==history_before, 'Previous Performance refetched after harmless rerender'
                assert request_counts.get(progression_path,0)==progression_before, 'Progression strategy refetched after harmless rerender'
                assert 'Loading your last performance' not in page.locator('#recallCard').inner_text(), 'Previous Performance returned to loading state'


                # v14.84.0: smart swap loaders must settle once and survive rerenders.
                page.locator('[data-a="swap-exercise"]').click();page.wait_for_timeout(1200)
                substitutions_path=f'/me/exercises/{exercise_id}/substitutions'
                intelligence_path=f'/me/exercises/{exercise_id}/substitution-intelligence'
                assert 'Loading substitutions' not in page.locator('#swapList').inner_text(), 'Smart Swap remained in loading state'
                sub_before=request_counts.get(substitutions_path,0)
                intel_before=request_counts.get(intelligence_path,0)
                page.evaluate('render();render();render()');page.wait_for_timeout(500)
                assert request_counts.get(substitutions_path,0)==sub_before, 'Smart Swap substitutions refetched after harmless rerender'
                assert request_counts.get(intelligence_path,0)==intel_before, 'Substitution Intelligence refetched after harmless rerender'
                assert 'Loading substitutions' not in page.locator('#swapList').inner_text(), 'Smart Swap returned to loading after rerender'
                variety=page.locator('[data-swap-reason="variety"]')
                if variety.count():
                    variety.click();page.wait_for_timeout(800)
                    variety_count=request_counts.get(substitutions_path,0)
                    assert variety_count==sub_before+1, 'Changing swap reason should fetch substitutions exactly once'
                    page.evaluate('render();render()');page.wait_for_timeout(350)
                    assert request_counts.get(substitutions_path,0)==variety_count, 'Swap reason result refetched after rerender'
                    assert request_counts.get(intelligence_path,0)==intel_before, 'Swap reason change incorrectly refetched substitution intelligence'
                page.evaluate("go('exercise')");page.wait_for_timeout(250)

            # v14.84.0 loader audit: sibling loader completions and forced renders must not amplify requests.
            def assert_stable(route, paths, settle=1200):
                page.evaluate(f"go('{route}')")
                page.wait_for_timeout(settle)
                before={path:request_counts.get(path,0) for path in paths}
                page.evaluate('render();render();render()')
                page.wait_for_timeout(500)
                after={path:request_counts.get(path,0) for path in paths}
                assert after==before, f'{route} loader refetch after harmless rerender: before={before}, after={after}'

            assert_stable('plan',['/me/program/adaptation-preview','/me/recovery-intelligence'])
            assert_stable('progress',['/me/progress/hub','/me/training-records','/me/training-dashboard'])
            assert_stable('coach',['/me/coach/history','/me/coach/context','/me/coach/status','/me/coach/briefing','/me/coach/context-v4'])
            assert_stable('history',['/me/history'],800)
            assert_stable('prs',['/me/prs'],800)

            # Exercise-history screen must keep loaded content without re-requesting.
            page.evaluate("S.historyExercise=plan.workouts[0].exercises[0].exercise_id;go('exercisehistory')")
            page.wait_for_timeout(900)
            eh_id=page.evaluate('S.historyExercise')
            eh_path=f'/me/exercises/{eh_id}/history'
            eh_before=request_counts.get(eh_path,0)
            page.evaluate('render();render()');page.wait_for_timeout(400)
            assert request_counts.get(eh_path,0)==eh_before, 'Exercise History refetched after harmless rerender'
            assert 'Loading' not in page.locator('#ehBody').inner_text(), 'Exercise History returned to loading state'

            # Cardio swap must also remain stable when a workout has a cardio module.
            cardio_index=page.evaluate("plan.workouts.findIndex(x=>x.cardio_module)")
            if cardio_index>=0:
                page.evaluate(f"S.wi={cardio_index};go('cardioswap')")
                page.wait_for_timeout(800)
                cardio_before=request_counts.get('/me/cardio/options',0)
                assert 'Loading cardio options' not in page.locator('#cardioSwapList').inner_text(), 'Cardio swap remained loading'
                page.evaluate('render();render()');page.wait_for_timeout(350)
                assert request_counts.get('/me/cardio/options',0)==cardio_before, 'Cardio swap refetched after harmless rerender'
                assert 'Loading cardio options' not in page.locator('#cardioSwapList').inner_text(), 'Cardio swap returned to loading state'

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
        report={'status':'passed','viewport':'390x844','routes':screens,'checks':['authenticated startup','primary nav rendering','no page errors','no console errors','no failed requests','nutrition provider status regression','online-event regression','More sheet','frontend module namespaces','exercise history dedupe regression','async loader stability audit','smart swap dedupe','cardio swap dedupe']}
        print(json.dumps(report,indent=2))
        (SOURCE/'V14_38_2_BROWSER_SMOKE_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    finally:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill()
        shutil.rmtree(runtime,ignore_errors=True)

if __name__=='__main__': main()

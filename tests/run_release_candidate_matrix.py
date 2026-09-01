from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
tests=[
'run_static_validation.py','run_frontend_contract_validation.py','run_plan_precision_validation.py',
'run_v14_79_validation.py','run_v15_2_validation.py','run_v15_3_validation.py','run_v15_6_validation.py',
'run_v15_7_validation.py','run_v15_8_validation.py','run_v15_9_validation.py','run_v15_10_validation.py'
]
failed=[]
for name in tests:
    p=subprocess.run([sys.executable,str(root/'tests'/name)],cwd=root)
    if p.returncode: failed.append(name)
if failed:
    raise SystemExit('Release candidate failures: '+', '.join(failed))
print('Forge v15.10 release-candidate matrix passed:',len(tests),'test groups')

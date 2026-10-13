"""Actual final Compose/MySQL/API checks; read only and secret-free reports."""
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
docker=str(Path.home()/'AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe')
commands=[];checks=[]
def run(args):
    r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    commands.append({'command':subprocess.list2cmdline(args),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    assert r.returncode==0, commands[-1]['command']
    return r.stdout
try:
    status=run([docker,'compose','ps','--all','--format','json'])
    rows=[json.loads(line) for line in status.splitlines() if line.strip()]
    states={r['Service']:r for r in rows}
    assert states['db']['Health']=='healthy' and states['backend']['State']=='running' and states['frontend']['State']=='running' and states['migrate']['ExitCode']==0
    checks.append({'check':'Compose services and migration completion','passed':True,'actual':{k:{'state':v['State'],'health':v.get('Health'),'exit_code':v.get('ExitCode')} for k,v in states.items()}})
    current=run([docker,'compose','exec','-T','backend','alembic','current'])
    assert 'e52ad70491b2 (head)' in current
    run([docker,'compose','exec','-T','backend','alembic','check'])
    run([docker,'compose','exec','-T','backend','python','-m','pip','check'])
    run([sys.executable,'-m','pip','check'])
    for url in ['http://localhost:8000/api/v1/health/live','http://localhost:8000/api/v1/health/ready','http://localhost:5173']:
        r=httpx.get(url,timeout=10)
        assert r.status_code==200
        checks.append({'check':url,'passed':True,'actual':r.status_code})
    print('Final Compose, migration head/check, host/container dependencies and live readiness/frontend checks passed.')
finally:
    prefix=os.environ.get('INVENTORY_TEST_REPORT_PREFIX','phase6')
    assert prefix in {'phase6','publication'}
    (ROOT/f'docs/test-results/{prefix}-stack.json').write_text(json.dumps({'executed_at_utc':datetime.now(UTC).isoformat(),'commands':commands,'checks':checks},indent=2),encoding='utf-8')

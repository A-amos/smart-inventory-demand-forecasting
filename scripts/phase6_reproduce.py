"""Fresh isolated Compose project/volume; never deletes or resets development data."""
import json
import secrets
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local/phase6-repro'
DOCKER=Path.home()/'AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'


def main():
    LOCAL.mkdir(parents=True,exist_ok=True)
    scripts=LOCAL/'scripts';scripts.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'scripts/create_local_env.py',scripts/'create_local_env.py')
    commands=[]
    checks=[]
    passed=False
    def run(args,input=None):
        # Windows text pipes translate LF to CRLF; Linux getpass can retain CR.
        r=subprocess.run(args,cwd=ROOT,input=input.encode('utf-8') if input else None,capture_output=True)
        commands.append({'command':subprocess.list2cmdline([str(a) for a in args]),'exit_code':r.returncode,'stdout':r.stdout.decode('utf-8',errors='replace'),'stderr':r.stderr.decode('utf-8',errors='replace')})
        assert r.returncode==0, commands[-1]['command']
        return r.stdout.decode('utf-8',errors='replace')
    try:
        if not (LOCAL/'.env').exists():run([str(ROOT/'.venv/Scripts/python.exe'),str(scripts/'create_local_env.py')])
        override=LOCAL/'compose.override.yaml'
        override.write_text('services:\n  db:\n    ports: !override ["127.0.0.1:3307:3306"]\n  backend:\n    ports: !override ["127.0.0.1:8001:8000"]\n    environment:\n      CORS_ORIGINS: \'["http://localhost:5174"]\'\n  frontend:\n    ports: !override ["127.0.0.1:5174:5173"]\n',encoding='utf-8')
        base=[str(DOCKER),'compose','--env-file',str(LOCAL/'.env'),'-p','smartinventory-phase6-repro','-f',str(ROOT/'compose.yaml'),'-f',str(override)]
        run(base+['up','--build','-d'])
        for _ in range(40):
            try:
                if httpx.get('http://localhost:8001/api/v1/health/ready',timeout=3).status_code==200:
                    checks.append({'check':'isolated readiness','status':200})
                    break
            except httpx.HTTPError:pass
            time.sleep(1)
        else:raise AssertionError('Isolated backend readiness timeout')
        run(base+['exec','-T','backend','alembic','current'])
        run(base+['exec','-T','backend','alembic','check'])
        run(base+['exec','-T','backend','pip','check'])
        password=secrets.token_urlsafe(24)
        email='phase6.repro.'+secrets.token_hex(4)+'@smartinventory.local'
        (LOCAL/'account.json').write_text(json.dumps({'email':email,'password':password}),encoding='utf-8')
        run(base+['exec','-T','backend','python','-m','app.bootstrap','--email',email,'--name','Phase6 isolated reproduction'],input=password+'\n'+password+'\n')
        with httpx.Client(base_url='http://localhost:8001/api/v1') as client:
            r=client.post('/auth/login',json={'email':email,'password':password});r.raise_for_status()
            checks.append({'check':'authorized manager login','status':r.status_code})
            headers={'Authorization':'Bearer '+r.json()['access_token']}
            r=client.get('/products',headers=headers)
            assert r.status_code==200 and r.json()==[]
            checks.append({'check':'protected catalog accessible','status':r.status_code})
            r=client.post('/auth/logout',headers=headers)
            assert r.status_code==204
            checks.append({'check':'logout','status':r.status_code})
            r=client.get('/products',headers=headers)
            assert r.status_code==401
            checks.append({'check':'revoked session rejected','status':r.status_code})
        r=httpx.get('http://localhost:5174')
        assert r.status_code==200
        checks.append({'check':'isolated frontend','status':r.status_code})
        inference="from ml.artifacts import load_registered; from ml.data import load_daily; from ml.experiment import forecast_contract; m,r=load_registered(); o=forecast_contract(m,r,load_daily(),'20728','2011-11-10',28); assert o.horizon_days==28; print('Frozen historical inference passed: 28 days, no fitting or report mutation')"
        run(base+['exec','-T','backend','python','-c',inference])
        run(base+['ps','--all','--format','json'])
        # Stop the temporary stack to release RAM/ports; both volumes remain recoverable.
        run(base+['stop'])
        passed=True
        print('Fresh environment, isolated MySQL migrations, authorized-user CLI, login/logout, frontend/readiness, pip check and frozen inference passed. Development volume untouched.')
    finally:
        (ROOT/'docs/test-results/phase6-reproduction.json').write_text(json.dumps({'passed':passed,'executed_at_utc':datetime.now(UTC).isoformat(),'project':'smartinventory-phase6-repro','ports':[3307,8001,5174],'volume_policy':'New project-scoped mysql_data; no deletion; development volume untouched','checks':checks,'commands':commands},indent=2),encoding='utf-8')


if __name__=='__main__':main()

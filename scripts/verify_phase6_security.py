"""Bounded real MySQL/API security checks. No participant or penetration-test claims."""
import json
import os
import secrets
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.security import hash_password, token_digest
from app.database import SessionLocal
from app.models import AuthSession, User


def main():
    checks = []
    def check(name, condition, actual):
        checks.append({'check': name, 'passed': bool(condition), 'actual': actual})
        assert condition, name
    try:
        account = json.loads((ROOT / '.local/verification-account.json').read_text())
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=30) as client:
            result = client.post('/auth/login', json=account)
            result.raise_for_status()
            token = result.json()['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            check('Login returns a non-cacheable authorized manager session', result.headers.get('cache-control') == 'no-store' and result.json()['user']['role'] == 'manager', 'HTTP 200, no-store, manager')
            with SessionLocal() as db:
                user = db.scalar(select(User).where(User.email == account['email']))
                check('Password is Argon2id; stored value differs from plaintext', user.password_hash.startswith('$argon2id$') and user.password_hash != account['password'], 'Argon2id prefix; plaintext not stored')
                check('Session stores SHA256 digest only', db.get(AuthSession, token_digest(token)) is not None and db.get(AuthSession, token) is None, 'Digest key found; raw token key absent')
            check('Anonymous dashboard denied', client.get('/dashboard').status_code == 401, 401)
            check('SQL-like login denied with generic error', (r := client.post('/auth/login', json={'email': "a' OR '1'='1@example.com", 'password': 'Never-a-valid-password'})).status_code == 401 and r.json()['detail'] == 'Invalid credentials or account unavailable', r.json())
            tag = secrets.token_hex(4)
            payload = "<script>window.phase6Executed=true</script> ' OR 1=1 --"
            cat = client.post('/categories', headers=headers, json={'name': 'Phase6 text ' + tag}).json()
            product = client.post('/products', headers=headers, json={'sku': 'P6-TEXT-' + tag, 'name': payload, 'category_id': cat['id'], 'initial_stock': '20'}).json()
            check('Script/SQL-like product text round-trips as data', product.get('name') == payload and client.get('/products', headers=headers).status_code == 200, {'product_id': product.get('id'), 'payload': payload})
            check('Missing required product field rejected', client.post('/products', headers=headers, json={'name':'missing sku'}).status_code == 422, 422)
            check('Duplicate SKU rejected', client.post('/products', headers=headers, json={'sku': product['sku'], 'name':'duplicate','category_id':cat['id']}).status_code == 409, 409)
            change = {'name':'Phase6 updated text '+tag,'sku':product['sku'],'category_id':cat['id'],'unit':'unit','safety_stock':'3','lead_time_days':3,'overstock_multiplier':'2'}
            check('Manager product update persisted', (r := client.put(f"/products/{product['id']}",headers=headers,json=change)).status_code == 200 and r.json()['name'] == change['name'], r.status_code)
            check('Malformed CSV schema rejected', client.post('/sales/imports/preview',headers=headers|{'Content-Type':'text/csv'},content='wrong,column\n1,2\n').status_code == 422, 422)
            check('CSV body beyond 1 MiB rejected', client.post('/sales/imports/preview',headers=headers|{'Content-Type':'text/csv'},content=b'x'*(1024*1024+1)).status_code == 413, 413)
            # Expire only this evaluation session, using the actual persistent session table.
            with SessionLocal() as db:
                db.get(AuthSession, token_digest(token)).expires_at = datetime.now(UTC).replace(tzinfo=None)-timedelta(seconds=1)
                db.commit()
            check('Expired persistent session rejected', client.get('/auth/me', headers=headers).status_code == 401, 401)
            result = client.post('/auth/login',json=account); result.raise_for_status()
            headers={'Authorization':'Bearer '+result.json()['access_token']}
            email, password = f'phase6.lock.{tag}@smartinventory.local', secrets.token_urlsafe(24)
            with SessionLocal() as db:
                db.add(User(name='Phase6 isolated lockout', email=email, role='researcher',password_hash=hash_password(password)));db.commit()
            statuses=[client.post('/auth/login',json={'email':email,'password':'incorrect-password'}).status_code for _ in range(5)]
            check('Five failed logins trigger persistent lockout', statuses == [401]*5 and client.post('/auth/login',json={'email':email,'password':password}).status_code == 401, statuses+[401])
            with SessionLocal() as db:
                user=db.scalar(select(User).where(User.email==email))
                check('Lockout expiry recorded 15 minutes ahead', user.locked_until > datetime.now(UTC).replace(tzinfo=None), 'Future lockout timestamp')
                user.locked_until=datetime.now(UTC).replace(tzinfo=None)-timedelta(seconds=1);db.commit()
            research=client.post('/auth/login',json={'email':email,'password':password}); research.raise_for_status()
            rh={'Authorization':'Bearer '+research.json()['access_token']}
            check('Login works after simulated lockout expiry', research.status_code == 200, 'Actual request after controlled timestamp expiry')
            for path, body in [('/categories',{'name':'forbidden'}),('/products',{'sku':'forbidden','name':'forbidden','category_id':cat['id']})]:
                check('Researcher server rejects '+path,client.post(path,headers=rh,json=body).status_code == 403,403)
            check('Researcher inventory write denied', client.put(f"/products/{product['id']}/inventory",headers=rh,json={'on_hand':'1','confirmed_in_transit':'0','allocated':'0','version':1,'reason':'forbidden'}).status_code==403,403)
            check('Logout revokes researcher access',client.post('/auth/logout',headers=rh).status_code==204 and client.get('/auth/me',headers=rh).status_code==401,'204 then 401')
            with SessionLocal() as db:
                db.scalar(select(User).where(User.email==email)).active=False;db.commit()
            client.delete(f"/products/{product['id']}",headers=headers).raise_for_status()
            client.delete(f"/categories/{cat['id']}",headers=headers).raise_for_status()
            check('Manager logout revokes protected access',client.post('/auth/logout',headers=headers).status_code==204 and client.get('/dashboard',headers=headers).status_code==401,'204 then 401')
        ignored=subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','check-ignore','.env','backend/.env','.local/verification-account.json','.local/audit-venv'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
        tracked=subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','ls-files'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
        check('Environment and local credentials ignored by Git',len(ignored)==4 and not any(name=='.env' or name.startswith('.local/') or name=='backend/.env' for name in tracked), {'ignored':ignored,'tracked_file_count':len(tracked)})
        print(f'{len(checks)} bounded live security checks passed; no penetration-test claim.')
    finally:
        prefix = os.environ.get('INVENTORY_TEST_REPORT_PREFIX', 'phase6')
        assert prefix in {'phase6', 'publication'}
        (ROOT/f'docs/test-results/{prefix}-security.json').write_text(json.dumps({'executed_at_utc':datetime.now(UTC).isoformat(),'checks':checks},indent=2),encoding='utf-8')


if __name__=='__main__':main()

"""Verify the running MySQL/API stack and retain only non-secret evidence.

Run from the project root after Compose migrations have succeeded.
Creates one local verification account, whose generated credentials stay ignored.
"""
import json
import argparse
import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import select, text
from alembic.config import Config
from alembic.script import ScriptDirectory

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.core.security import hash_password, token_digest
from app.database import SessionLocal
from app.models import AuthSession, User, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', default='docs/test-results/phase1-live-latest.json')
    args = parser.parse_args()
    evidence = []
    def check(name, condition, actual):
        evidence.append({'check': name, 'passed': bool(condition), 'actual': actual})
        if not condition:
            raise AssertionError(name)

    destination = root / args.report
    migration_config = Config(str(root / 'backend/alembic.ini'))
    migration_config.set_main_option('script_location', str(root / 'backend/migrations'))
    current_head = ScriptDirectory.from_config(migration_config).get_current_head()
    try:
        with SessionLocal() as db:
            version = db.scalar(text('SELECT VERSION()'))
            check('MySQL connectivity', 'sqlite' not in db.bind.dialect.name and bool(version), str(version))
            revision = db.scalar(text('SELECT version_num FROM alembic_version'))
            check('Database at current migration head', revision == current_head, revision)
        credentials_path = root / '.local/verification-account.json'
        credentials_path.parent.mkdir(exist_ok=True)
        if credentials_path.exists():
            credentials = json.loads(credentials_path.read_text())
        else:
            credentials = {'email': 'verification.manager@smartinventory.local', 'password': secrets.token_urlsafe(24)}
            with SessionLocal() as db:
                if db.scalar(select(User).where(User.email == credentials['email'])):
                    raise RuntimeError('Verification account exists without local credentials; no changes made')
                db.add(User(name='Local Verification Manager', email=credentials['email'], role='manager',
                            password_hash=hash_password(credentials['password'])))
                db.commit()
            credentials_path.write_text(json.dumps(credentials), encoding='utf-8')
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == credentials['email']))
            check('Authorized account stored', bool(user and user.active and user.role == 'manager'), 'active manager; password omitted')
            check('Password hashed', user.password_hash.startswith('$argon2id$'), 'Argon2id')
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=10) as client:
            for endpoint in ['live', 'ready']:
                response = client.get(f'/health/{endpoint}')
                check(f'Health {endpoint}', response.status_code == 200, response.status_code)
            check('Anonymous protected access', (r := client.get('/auth/me')).status_code == 401, r.status_code)
            check('Wrong password', (r := client.post('/auth/login', json={**credentials, 'password': 'incorrect'})).status_code == 401, r.status_code)
            response = client.post('/auth/login', json=credentials)
            check('Login', response.status_code == 200, response.status_code)
            headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
            check('Protected authenticated access', (r := client.get('/auth/me', headers=headers)).status_code == 200, r.status_code)
            check('Logout', (r := client.post('/auth/logout', headers=headers)).status_code == 204, r.status_code)
            check('Revoked token rejected', (r := client.get('/auth/me', headers=headers)).status_code == 401, r.status_code)
            response = client.post('/auth/login', json=credentials)
            response.raise_for_status()
            token = response.json()['access_token']
            with SessionLocal() as db:
                db.get(AuthSession, token_digest(token)).expires_at = utc_now() - timedelta(seconds=1)
                db.commit()
            check('Expired token rejected', (r := client.get('/auth/me', headers={'Authorization': 'Bearer ' + token})).status_code == 401, r.status_code)
        with httpx.Client(base_url='http://localhost:5173', timeout=10) as browser_origin:
            check('Frontend service responds', (r := browser_origin.get('/')).status_code == 200, r.status_code)
            check('Frontend API proxy reaches MySQL readiness', (r := browser_origin.get('/api/v1/health/ready')).status_code == 200, r.status_code)
        print(f'{len(evidence)} live checks passed; local credentials saved in ignored .local/verification-account.json')
    finally:
        destination.write_text(json.dumps({'executed_at_utc': datetime.now(UTC).isoformat(), 'checks': evidence}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

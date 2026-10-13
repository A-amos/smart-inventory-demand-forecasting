"""Actual MySQL/HTTP evidence, isolated synthetic stock, no training or secrets in reports."""
import hashlib
import json
import secrets
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal as D
from pathlib import Path
from uuid import uuid4

import httpx
import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.database import SessionLocal
from app.core.security import hash_password
from app.models import User


def operational_digest():
    with SessionLocal() as db:
        result = {}
        for table in ['products', 'sales', 'inventory', 'stock_movements', 'sales_imports']:
            rows = sorted([dict(row) for row in db.execute(text(f'SELECT * FROM {table}')).mappings()], key=lambda row: json.dumps(row, sort_keys=True, default=str))
            result[table] = {'count': len(rows), 'sha256': hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()}
        return result


def main():
    checks = []
    def check(name, passed, actual):
        checks.append({'check': name, 'passed': bool(passed), 'actual': actual})
        if not passed: raise AssertionError(name)
    def request(client, method, path, headers, body=None):
        response = client.request(method, path, headers=headers, json=body)
        response.raise_for_status()
        return response.json() if response.status_code != 204 else None
    tag = secrets.token_hex(4).upper()
    try:
        reference = json.loads((ROOT / 'backend/app/core/phase4-reference.json').read_text())
        check('All protected Phase 4 research files unchanged', all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in reference.items()), len(reference))
        with SessionLocal() as db:
            version = db.scalar(text('SELECT VERSION()'))
            revision = db.scalar(text('SELECT version_num FROM alembic_version'))
            check('Actual MySQL 8.4 and Phase 5 migration', version.startswith('8.4') and revision == 'e52ad70491b2', {'mysql': version, 'revision': revision})
            triggers = list(db.scalars(text("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE() AND TRIGGER_NAME LIKE 'protect_%'")))
            check('Eight database immutability triggers installed', len(triggers) == 8, triggers)
            precision = db.scalar(text("SELECT DATETIME_PRECISION FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='recommendations' AND COLUMN_NAME='created_at'"))
            check('Microsecond evidence timestamps', precision == 6, precision)
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=45) as client:
            for path in ['/health/live', '/health/ready']:
                response = client.get(path); check(path, response.status_code == 200, response.status_code)
            account = json.loads((ROOT / '.local/verification-account.json').read_text())
            session = request(client, 'POST', '/auth/login', {}, account)
            headers = {'Authorization': 'Bearer ' + session['access_token']}
            support = request(client, 'GET', '/forecast-support', headers)
            check('Frozen mean_28 selected; operational forecasts explicitly unavailable', support['selected'] == 'mean_28' and not support['operational_forecasts_available'], support)
            cat = request(client, 'POST', '/categories', headers, {'name': 'Phase 5 synthetic API tests ' + tag})
            item = request(client, 'POST', '/products', headers, dict(category_id=cat['id'], sku='P5-' + tag, name='Phase 5 synthetic stock ' + tag,
                           unit='unit', initial_stock='5', lead_time_days=3, safety_stock='4', overstock_multiplier='2'))
            identifier = item['id']
            def fc(**change): return dict(request_key=str(uuid4()), forecast_origin='2011-11-10', horizon=28, context='research_demo', confirm_research_demo=True) | change
            response = client.post(f'/forecasts/{identifier}/generate', headers=headers, json=fc())
            check('Unsupported/unmapped product rejected safely', response.status_code == 422, response.json())
            mapping = request(client, 'POST', f'/products/{identifier}/forecast-mappings', headers,
                              dict(series_sku='20728', confirm_research_demo=True, reason='Synthetic API test inventory; UK research series only'))
            for label, change, expected in [('Present-day history unavailable', {'forecast_origin': '2026-10-01'}, 409),
                    ('Operational context cannot use historical demo', {'context': 'operational'}, 409), ('Horizon above contract', {'horizon': 29}, 422)]:
                response = client.post(f'/forecasts/{identifier}/generate', headers=headers, json=fc(**change))
                check(label, response.status_code == expected, {'status': response.status_code, 'detail': response.json()})
            values = fc()
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(lambda _: client.post(f'/forecasts/{identifier}/generate', headers=headers, json=values), [1, 2]))
            generated = responses[0].json()
            check('Concurrent forecast retry produces exactly one immutable record', all(r.status_code == 201 for r in responses) and responses[1].json()['id'] == generated['id'] and len(request(client, 'GET', f'/forecasts/{identifier}', headers)) == 1, [r.status_code for r in responses])
            daily = pd.read_csv(ROOT / 'data/processed/phase4/development.csv', dtype={'sku': str})
            expected_mean = daily[daily.sku.eq('20728')].tail(28).demand.mean()
            expected_stored = D(str(expected_mean)).quantize(D('0.000000001'))
            check('Actual frozen inference matches independently calculated last-28-day mean', len(generated['points']) == 28 and all(D(point['predicted_quantity']) == expected_stored for point in generated['points']), {'mean': float(expected_mean), 'stored': str(expected_stored), 'forecast_id': generated['id']})
            check('Forecast-v1 contract and versioned storage identity', generated['contract']['sku'] == '20728' and generated['mapping_id'] == mapping['id'] and generated['artifact_version'] == support['artifact_version'] and generated['points'][0]['forecast_date'] == '2011-11-11', {'model': generated['model_id'], 'version': generated['model_version'], 'artifact': generated['artifact_version']})
            def rec(**changes): return dict(request_key=str(uuid4()), forecast_id=generated['id'], context='research_demo', decision_as_of='2011-11-11', confirm_research_demo=True) | changes
            for label, changes, expected in [('Stale forecast rejected', {'decision_as_of': '2011-11-12'}, 409), ('Missing forecast rejected', {'forecast_id': str(uuid4())}, 404)]:
                response = client.post(f'/recommendations/{identifier}/generate', headers=headers, json=rec(**changes))
                check(label, response.status_code == expected, response.status_code)
            short = request(client, 'POST', f'/forecasts/{identifier}/generate', headers, fc(horizon=2))
            response = client.post(f'/recommendations/{identifier}/generate', headers=headers, json=rec(forecast_id=short['id']))
            check('Insufficient lead-time coverage rejected', response.status_code == 409, response.status_code)
            stock = request(client, 'PUT', f'/products/{identifier}/inventory', headers,
                            dict(on_hand='5', confirmed_in_transit='3', allocated='2', version=1, reason='Synthetic incoming and allocation scenario'))
            before = operational_digest()
            payload = rec()
            saved = request(client, 'POST', f'/recommendations/{identifier}/generate', headers, payload)
            snapshot = saved['snapshot']
            target = expected_stored * 3 + 4
            check('Actual position, multi-day target, safety, reorder and overstock equations',
                  D(snapshot['inventory_position']) == 6 and D(snapshot['predicted_lead_time_demand']) == expected_stored * 3
                  and D(snapshot['target_stock']) == target and D(snapshot['suggested_reorder']) == max(D(0), target - 6)
                  and D(snapshot['overstock_threshold']) == target * 2, snapshot)
            check('Forecasts and recommendations leave operational ledger unchanged', operational_digest() == before, before)
            # Trigger assertions perform no-op UPDATE and DELETE attempts inside transactions.
            for table, condition in [('forecast_mappings', f"id='{mapping['id']}'"), ('forecasts', f"id='{generated['id']}'"),
                                     ('forecast_points', f"forecast_id='{generated['id']}' AND horizon_day=1"), ('recommendations', f"id='{saved['id']}'")]:
                for operation in ['UPDATE', 'DELETE']:
                    blocked = False
                    with SessionLocal() as db:
                        try:
                            column = 'horizon_day' if table == 'forecast_points' else 'id'
                            sql = f'UPDATE {table} SET {column}={column} WHERE {condition}' if operation == 'UPDATE' else f'DELETE FROM {table} WHERE {condition}'
                            db.execute(text(sql)); db.rollback()
                        except DBAPIError as error:
                            blocked = 'Append-only' in str(error.orig); db.rollback()
                    check(f'MySQL blocks {operation} on {table}', blocked, 'SQLSTATE 45000 append-only' if blocked else 'not blocked')
            # Isolate a real artifact failure in the container copy only, restoring in finally.
            docker = Path.home() / 'AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'
            script = "from pathlib import Path; import json; p=Path('/opt/project')/json.loads(Path('/opt/project/docs/research/results/model-registry.json').read_text())['artifact_path']; assert p.is_relative_to('/opt/project/ml/artifacts'); p.rename(p.with_suffix('.phase5-missing'))"
            restore = "from pathlib import Path; import json; p=Path('/opt/project')/json.loads(Path('/opt/project/docs/research/results/model-registry.json').read_text())['artifact_path']; p.with_suffix('.phase5-missing').rename(p)"
            before = operational_digest()
            hidden = False
            try:
                subprocess.run([str(docker), 'compose', 'exec', '-T', 'backend', 'python', '-c', script], cwd=ROOT, check=True, capture_output=True); hidden = True
                response = client.post(f'/forecasts/{identifier}/generate', headers=headers, json=fc())
                check('Actual missing artifact returns clear 503 without ledger corruption', response.status_code == 503 and operational_digest() == before, {'response': response.json(), 'unchanged_tables': list(before)})
                check('Inventory API remains usable during real artifact failure', client.get('/products', headers=headers).status_code == 200 and client.get('/health/ready').status_code == 200, 'products and readiness HTTP 200')
            finally:
                if hidden: subprocess.run([str(docker), 'compose', 'exec', '-T', 'backend', 'python', '-c', restore], cwd=ROOT, check=True, capture_output=True)
            check('Artifact restored and verified after failure test', client.get('/forecast-support', headers=headers).status_code == 200, 'HTTP 200')
            sold = request(client, 'POST', '/sales', headers, dict(product_id=identifier, quantity='1', unit_price=None,
                           sale_date=datetime.now(UTC).isoformat(), inventory_version=stock['version'], request_key=str(uuid4())))
            stock = request(client, 'GET', f'/products/{identifier}', headers)['inventory']
            after_sale = request(client, 'GET', '/dashboard?context=research_demo', headers)
            sale_row = next(row for row in after_sale['products'] if row['product_id'] == identifier)
            check('Existing operational sale updates dashboard stock and invalidates old decision',
                  sold['product_id'] == identifier and D(stock['on_hand']) == 4 and D(sale_row['inventory_position']) == 5
                  and sale_row['risk_status'] == 'UNASSESSED', {'on_hand': stock['on_hand'], 'position': sale_row['inventory_position'], 'status': sale_row['risk_status']})
            check('Sale does not rewrite earlier recommendation evidence', request(client, 'GET', f'/recommendations/{identifier}', headers)[0] == saved, saved['id'])
            stock = request(client, 'PUT', f'/products/{identifier}/inventory', headers,
                            dict(on_hand='999', confirmed_in_transit='0', allocated='0', version=stock['version'], reason='Synthetic overstock scenario'))
            replay = request(client, 'POST', f'/recommendations/{identifier}/generate', headers, payload)
            check('Retry after stock change returns original snapshot without recalculation', replay == saved, replay['id'])
            over = request(client, 'POST', f'/recommendations/{identifier}/generate', headers, rec())
            check('Overstock uses strict configured threshold and zero reorder', over['risk_status'] == 'OVERSTOCK' and D(over['snapshot']['suggested_reorder']) == 0 and D(over['snapshot']['inventory_position']) > D(over['snapshot']['overstock_threshold']), over['snapshot'])
            history = request(client, 'GET', f'/recommendations/{identifier}', headers)
            check('Recommendation history remains immutable and chronologically ordered', len(history) == 2 and history[0]['id'] == over['id'] and history[1] == saved, [row['id'] for row in history])
            overview = request(client, 'GET', '/dashboard?context=research_demo', headers)
            row = next(row for row in overview['products'] if row['product_id'] == identifier)
            current = request(client, 'GET', '/dashboard', headers)
            check('Dashboard distinguishes historical overstock from current unassessed', row['risk_status'] == 'OVERSTOCK' and next(row for row in current['products'] if row['product_id'] == identifier)['risk_status'] == 'UNASSESSED', {'research_status': row['risk_status'], 'operational': 'UNASSESSED'})
            compared = request(client, 'GET', '/research/models', headers)
            source_val = json.loads((ROOT / 'docs/research/results/validation.json').read_text())
            source_final = json.loads((ROOT / 'docs/research/results/final-test.json').read_text())
            check('Live model comparison reproduces all preserved research metrics', compared['selected'] == 'mean_28' and all(row['validation'] == source_val['scores'][row['name']] and row['final_test'] == source_final['scores'].get(row['name']) for row in compared['models']), 'All six validation and four final-test rows match exactly')
            email, password = f'phase5.{tag.lower()}@smartinventory.local', secrets.token_urlsafe(24)
            with SessionLocal() as db:
                db.add(User(name='Phase 5 synthetic verification researcher', email=email, role='researcher', password_hash=hash_password(password))); db.commit()
            research = request(client, 'POST', '/auth/login', {}, {'email': email, 'password': password})
            read_headers = {'Authorization': 'Bearer ' + research['access_token']}
            for path in [f'/forecasts/{identifier}', f'/recommendations/{identifier}', '/research/models', '/dashboard']:
                check('Researcher reads ' + path, client.get(path, headers=read_headers).status_code == 200, 'HTTP 200')
            for role, role_headers, expected in [('Researcher', read_headers, 403), ('Anonymous', {}, 401)]:
                for path, values in [(f'/forecasts/{identifier}/generate', fc()), (f'/recommendations/{identifier}/generate', rec()),
                                     (f'/products/{identifier}/forecast-mappings', dict(series_sku='20728', confirm_research_demo=True, reason='Forbidden mutation'))]:
                    response = client.post(path, headers=role_headers, json=values)
                    check(role + ' cannot modify ' + path, response.status_code == expected, response.status_code)
            request(client, 'POST', '/auth/logout', read_headers)
            with SessionLocal() as db:
                db.scalar(select(User).where(User.email == email)).active = False; db.commit()
            request(client, 'DELETE', f'/products/{identifier}', headers)
            request(client, 'DELETE', f'/categories/{cat["id"]}', headers)
            check('Archived product retains forecast/recommendation evidence', len(request(client, 'GET', f'/forecasts/{identifier}', headers)) == 2 and len(request(client, 'GET', f'/recommendations/{identifier}', headers)) == 2, 'Two forecasts and two recommendations retained')
            check('Vite proxy exposes real Phase 5 API', httpx.get('http://localhost:5173/api/v1/research/models', headers=headers).status_code == 200, 'HTTP 200')
            request(client, 'POST', '/auth/logout', headers)
            check('Logout revokes forecast access', client.get(f'/forecasts/{identifier}', headers=headers).status_code == 401, 'HTTP 401')
        print(f'{len(checks)} actual MySQL/API Phase 5 checks passed; synthetic catalog archived, evidence retained.')
    finally:
        (ROOT / 'docs/test-results/phase5-live.json').write_text(json.dumps({'executed_at_utc': datetime.now(UTC).isoformat(), 'synthetic_inventory': True, 'checks': checks}, indent=2), encoding='utf-8')


if __name__ == '__main__': main()

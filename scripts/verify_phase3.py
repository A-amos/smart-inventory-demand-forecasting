"""Real MySQL and HTTP verification; tagged records retained, then archived.

Run from the project root with the Compose stack up. Credentials are read only
from ignored .local; reports contain no passwords or bearer tokens.
"""
import json
import secrets
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import httpx
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import IntegrityError

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Inventory, Sale, SalesImport, StockMovement, User
from app.sales_schemas import SaleCreate
from app.services.sales import record_sale
from fastapi import HTTPException


def ledger(identifier):
    with SessionLocal() as db:
        stock = db.get(Inventory, identifier)
        return {'on_hand': str(stock.on_hand), 'version': stock.version, 'allocated': str(stock.allocated),
                'incoming': str(stock.confirmed_in_transit),
                'sales': db.scalar(select(func.count(Sale.id)).where(Sale.product_id == identifier)),
                'movements': db.scalar(select(func.count(StockMovement.id)).where(StockMovement.product_id == identifier))}


def main():
    checks = []
    def check(name, condition, actual):
        checks.append({'check': name, 'passed': bool(condition), 'actual': actual})
        if not condition: raise AssertionError(name)
    credentials = json.loads((root / '.local/verification-account.json').read_text())
    tag = secrets.token_hex(4).upper()
    try:
        with SessionLocal() as db:
            check('Actual MySQL version', str(db.scalar(text('SELECT VERSION()'))).startswith('8.4'), db.scalar(text('SELECT VERSION()')))
            revision = db.scalar(text('SELECT version_num FROM alembic_version'))
            check('Phase 3 schema applied', revision == '7cf0674f24d9', revision)
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=30) as client:
            for path in ['/health/live', '/health/ready']:
                check(path, (r := client.get(path)).status_code == 200, r.status_code)
            login = client.post('/auth/login', json=credentials)
            login.raise_for_status()
            headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
            actor = login.json()['user']['id']
            category = client.post('/categories', headers=headers, json={'name': 'Phase 3 verification ' + tag})
            category.raise_for_status()
            category_id = category.json()['id']
            sku = 'SALES-' + tag
            product = client.post('/products', headers=headers, json={'sku': sku, 'name': 'Phase 3 stock ' + tag,
                'category_id': category_id, 'initial_stock': '10'})
            product.raise_for_status()
            identifier = product.json()['id']
            def sale(**changes):
                return {'product_id': identifier, 'quantity': '7', 'unit_price': '80.25',
                        'sale_date': '2026-09-01T10:00:00+03:00', 'inventory_version': 1,
                        'request_key': str(uuid4())} | changes
            # Distinct HTTP requests start together. Stock can support only one.
            barrier = Barrier(2)
            payloads = [sale(), sale()]
            def sell(values):
                barrier.wait(timeout=10)
                return client.post('/sales', headers=headers, json=values)
            with ThreadPoolExecutor(max_workers=2) as workers:
                responses = list(workers.map(sell, payloads))
            statuses = sorted(row.status_code for row in responses)
            check('Two concurrent sales serialized safely', statuses == [201, 409], statuses)
            accepted_index = next(i for i, row in enumerate(responses) if row.status_code == 201)
            accepted = responses[accepted_index].json()
            baseline = ledger(identifier)
            check('Only accepted sale reduces stock and increments version', Decimal(baseline['on_hand']) == 3 and baseline['version'] == 2 and baseline['sales'] == 1 and baseline['movements'] == 2, baseline)
            check('Actor and original SKU persisted', accepted['actor_id'] == actor and accepted['sku_snapshot'] == sku, {'actor_id': accepted['actor_id'], 'sku': accepted['sku_snapshot']})
            with SessionLocal() as db:
                movement = db.scalar(select(StockMovement).where(StockMovement.sale_id == accepted['id']))
                check('Sale linked to exactly one audit movement', movement is not None and movement.kind == 'sale' and movement.on_hand_before == 10 and movement.on_hand_after == 3, '10 -> 3, linked sale')
            replay = client.post('/sales', headers=headers, json=payloads[accepted_index])
            check('Operational request retry idempotent', replay.status_code == 200 and replay.json()['id'] == accepted['id'] and ledger(identifier) == baseline, replay.status_code)
            for name, changes, expected in [
                ('Stale version', {'quantity': '1'}, 409),
                ('Insufficient stock', {'quantity': '4', 'inventory_version': 2}, 409),
                ('Invalid quantity', {'quantity': '-1'}, 422),
                ('Invalid date', {'sale_date': '2026-02-30T00:00:00Z'}, 422),
                ('Invalid product', {'product_id': 2147483647}, 404),
                ('Forged actor', {'actor_id': 999}, 422),
            ]:
                r = client.post('/sales', headers=headers, json=sale(**changes))
                check(name + ' rejected without ledger changes', r.status_code == expected and ledger(identifier) == baseline, r.status_code)
            # Inject failure locally into the service, using a real independent MySQL transaction.
            def fail_audit(mapper, connection, row):
                if row.product_id == identifier and row.kind == 'sale':
                    raise IntegrityError('injected verification audit failure', {}, Exception('expected failure'))
            event.listen(StockMovement, 'before_insert', fail_audit)
            try:
                failed = False
                with SessionLocal() as db:
                    user = db.get(User, actor)
                    try: record_sale(db, SaleCreate.model_validate(sale(quantity='1', inventory_version=2)), user)
                    except HTTPException as exc: failed = exc.status_code == 409
                check('MySQL sale/audit failure rolls back all writes', failed and ledger(identifier) == baseline, ledger(identifier))
            finally:
                event.remove(StockMovement, 'before_insert', fail_audit)
            csv_headers = headers | {'Content-Type': 'text/csv'}
            csv_header = 'sku,sale_date,quantity,unit_price,external_id\n'
            row_a = f'{sku},2026-08-01T10:00:00+03:00,100,80,A\n'
            row_e = f'{sku},2026-08-02T00:00:00Z,1,,E\n'
            csv = csv_header + row_a * 2 + f'{sku},2026-08-01T00:00:00Z,-1,80,B\n{sku},bad,2,80,C\nMISSING-{tag},2026-08-01T00:00:00Z,1,80,D\n' + row_e
            batch_response = client.post('/sales/imports/preview?filename=verification.csv', headers=csv_headers, content=csv)
            check('CSV preview created', batch_response.status_code == 200, batch_response.status_code)
            batch = batch_response.json()
            check('Preview reports duplicate/invalid quantity/date/SKU rows', batch['valid_count'] == 2 and batch['rejected_count'] == 4 and len(batch['rejected_rows']) == 4, {'valid': batch['valid_count'], 'rejected': batch['rejected_count'], 'reasons': [row['reason'] for row in batch['rejected_rows']]})
            check('Preview saves no sales and changes no stock', ledger(identifier) == baseline, ledger(identifier))
            other_csv = csv_header + row_a + f'{sku},2026-08-03T00:00:00Z,2,80,G\n'
            other = client.post('/sales/imports/preview', headers=csv_headers, content=other_csv).json()
            def confirm(batch, accept=True):
                return client.post(f"/sales/imports/{batch['id']}/confirm", headers=headers,
                    json={'preview_version': batch['preview_version'], 'accept_valid_rows': accept})
            check('Explicit confirmation required', (r := confirm(batch, False)).status_code == 422, r.status_code)
            imported = confirm(batch)
            check('Historical confirmation persists valid rows only', imported.status_code == 200 and imported.json()['imported_count'] == 2, imported.status_code)
            after = ledger(identifier)
            check('Historical quantity exceeding current stock still leaves inventory/audit unchanged', all(after[k] == baseline[k] for k in ['on_hand', 'version', 'allocated', 'incoming', 'movements']) and after['sales'] == 3, after)
            check('Repeat confirmation idempotent', (r := confirm(batch)).status_code == 200 and ledger(identifier) == after, r.status_code)
            repeated = client.post('/sales/imports/preview', headers=csv_headers, content=csv).json()
            check('Repeat exact file recognized', repeated['status'] == 'committed' and repeated['id'] == batch['id'] and ledger(identifier) == after, repeated['status'])
            check('Competing overlapping import rolls back entire batch', (r := confirm(other)).status_code == 409 and ledger(identifier) == after, r.status_code)
            with SessionLocal() as db:
                check('Failed import remains uncommitted', db.get(SalesImport, other['id']).status == 'preview', db.get(SalesImport, other['id']).status)
            refreshed = client.post('/sales/imports/preview', headers=csv_headers, content=other_csv).json()
            check('Cross-file duplicate explicitly rejected on fresh preview', refreshed['valid_count'] == 1 and refreshed['rejected_count'] == 1, {'valid': refreshed['valid_count'], 'rejected': refreshed['rejected_count']})
            check('Old preview version cannot confirm', (r := confirm(other)).status_code == 409, r.status_code)
            page = client.get('/sales', headers=headers, params={'product_id': identifier, 'actor_id': actor, 'limit': 2}).json()
            page2 = client.get('/sales', headers=headers, params={'product_id': identifier, 'limit': 2, 'offset': 2}).json()
            check('History persisted and paginated chronologically', page['total'] == 3 and len(page['items']) == 2 and len(page2['items']) == 1 and page['items'][0]['sale_date'] > page['items'][1]['sale_date'] > page2['items'][0]['sale_date'], [r['sale_date'] for r in page['items'] + page2['items']])
            r = client.get('/sales', headers=headers, params={'product_id': identifier, 'source': 'historical', 'date_from': '2026-08-01T00:00:00Z', 'date_to': '2026-08-01T23:59:59Z'})
            check('Date/source history filters', r.status_code == 200 and r.json()['total'] == 1, r.json()['total'])
            check('Server upload size limit', (r := client.post('/sales/imports/preview', headers=csv_headers, content=b'x' * (1024 * 1024 + 1))).status_code == 413, r.status_code)
            email, password = f'phase3.research.{tag.lower()}@smartinventory.local', secrets.token_urlsafe(24)
            with SessionLocal() as db:
                db.add(User(name='Phase 3 verification researcher', email=email, role='researcher', password_hash=hash_password(password)))
                db.commit()
            research = client.post('/auth/login', json={'email': email, 'password': password})
            research.raise_for_status()
            research_headers = {'Authorization': 'Bearer ' + research.json()['access_token']}
            check('Researcher reads sales', (r := client.get('/sales', headers=research_headers)).status_code == 200, r.status_code)
            for role, role_headers, status in [('Researcher', research_headers, 403), ('Anonymous', {}, 401)]:
                check(role + ' cannot record sales', (r := client.post('/sales', headers=role_headers, json=sale(quantity='1', inventory_version=2))).status_code == status, r.status_code)
                check(role + ' cannot preview imports', (r := client.post('/sales/imports/preview', headers=role_headers | {'Content-Type': 'text/csv'}, content=csv)).status_code == status, r.status_code)
                check(role + ' cannot confirm imports', (r := client.post(f"/sales/imports/{batch['id']}/confirm", headers=role_headers, json={'preview_version': 1, 'accept_valid_rows': True})).status_code == status, r.status_code)
            client.post('/auth/logout', headers=research_headers).raise_for_status()
            with SessionLocal() as db:
                db.scalar(select(User).where(User.email == email)).active = False
                db.commit()
            client.delete(f'/products/{identifier}', headers=headers).raise_for_status()
            check('Archived product rejects operational sales', (r := client.post('/sales', headers=headers, json=sale(quantity='1', inventory_version=2))).status_code == 404, r.status_code)
            check('Archived-after-preview import rejected', (r := confirm(refreshed)).status_code == 409 and ledger(identifier) == after, r.status_code)
            client.delete(f'/categories/{category_id}', headers=headers).raise_for_status()
            check('Archive preserves sales history', client.get('/sales', headers=headers, params={'product_id': identifier}).json()['total'] == 3, 3)
            check('Vite proxy exposes real sales API', (r := httpx.get('http://localhost:5173/api/v1/sales', headers=headers)).status_code == 200, r.status_code)
            check('Manager logout revokes sales access', client.post('/auth/logout', headers=headers).status_code == 204 and client.get('/sales', headers=headers).status_code == 401, '204 then 401')
        print(f'{len(checks)} Phase 3 live MySQL/API checks passed; tagged records archived with audit preserved')
    finally:
        (root / 'docs/test-results/phase3-live.json').write_text(json.dumps({'executed_at_utc': datetime.now(UTC).isoformat(), 'checks': checks}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Exercise Phase 2 through the real HTTP API and MySQL, preserving audit data."""
import json
import secrets
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
from sqlalchemy import select, text

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Inventory, Product, StockMovement, User


def main():
    checks = []
    def check(name, condition, actual):
        checks.append({'check': name, 'passed': bool(condition), 'actual': actual})
        if not condition:
            raise AssertionError(name)
    credentials = json.loads((root / '.local/verification-account.json').read_text())
    tag = secrets.token_hex(4).upper()
    try:
        with SessionLocal() as db:
            revision = db.scalar(text('SELECT version_num FROM alembic_version'))
            check('Phase 2 migration applied', revision == '4ceb0a570e41', revision)
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=20) as client:
            login = client.post('/auth/login', json=credentials)
            login.raise_for_status()
            headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
            check('Anonymous catalog rejected', (r := client.get('/products')).status_code == 401, r.status_code)
            category = client.post('/categories', headers=headers, json={'name': f'Verification {tag}'})
            check('Category create', category.status_code == 201, category.status_code)
            category_id = category.json()['id']
            check('Category read', (r := client.get(f'/categories/{category_id}', headers=headers)).status_code == 200, r.status_code)
            check('Category update', (r := client.put(f'/categories/{category_id}', headers=headers, json={'name': f'Verified {tag}'})).status_code == 200, r.status_code)
            check('Duplicate category', (r := client.post('/categories', headers=headers, json={'name': f'verified {tag}'})).status_code == 409, r.status_code)
            payload = {'sku': f'VERIFY-{tag}', 'name': f'Verification stock {tag}', 'category_id': category_id,
                       'unit': 'kg', 'initial_stock': '12.500', 'safety_stock': '3.250', 'lead_time_days': 7, 'overstock_multiplier': '2.500'}
            response = client.post('/products', headers=headers, json=payload)
            check('Product create', response.status_code == 201, response.status_code)
            identifier = response.json()['id']
            check('Opening stock exact', Decimal(response.json()['inventory']['on_hand']) == Decimal('12.500'), response.json()['inventory']['on_hand'])
            check('Duplicate SKU case normalization', (r := client.post('/products', headers=headers, json=payload | {'sku': payload['sku'].lower()})).status_code == 409, r.status_code)
            check('Missing required product field', (r := client.post('/products', headers=headers, json={'sku': f'INVALID-{tag}'})).status_code == 422, r.status_code)
            check('Invalid category rejected', (r := client.post('/products', headers=headers, json=payload | {'sku': f'INVALID-{tag}', 'category_id': 2147483647})).status_code == 422, r.status_code)
            updated_payload = {key: value for key, value in payload.items() if key != 'initial_stock'} | {'lead_time_days': 10, 'safety_stock': '5.500', 'overstock_multiplier': '3.000'}
            response = client.put(f'/products/{identifier}', headers=headers, json=updated_payload)
            check('Product configuration update', response.status_code == 200 and response.json()['lead_time_days'] == 10, response.status_code)
            check('Product read', (r := client.get(f'/products/{identifier}', headers=headers)).status_code == 200, r.status_code)
            check('Referenced category cannot archive', (r := client.delete(f'/categories/{category_id}', headers=headers)).status_code == 409, r.status_code)
            inventory_payload = {'on_hand': '20.125', 'confirmed_in_transit': '10.250', 'allocated': '2.000', 'version': 1, 'reason': 'Live verification stock count'}
            response = client.put(f'/products/{identifier}/inventory', headers=headers, json=inventory_payload)
            check('Inventory update', response.status_code == 200 and response.json()['version'] == 2, response.status_code)
            check('Stale update rejected', (r := client.put(f'/products/{identifier}/inventory', headers=headers, json=inventory_payload)).status_code == 409, r.status_code)
            check('Invalid allocations rejected', (r := client.put(f'/products/{identifier}/inventory', headers=headers, json=inventory_payload | {'version': 2, 'allocated': '30'})).status_code == 422, r.status_code)
            with ThreadPoolExecutor(max_workers=2) as workers:
                responses = list(workers.map(lambda quantity: client.put(f'/products/{identifier}/inventory', headers=headers,
                    json=inventory_payload | {'on_hand': quantity, 'version': 2}), ['21', '22']))
            statuses = sorted(r.status_code for r in responses)
            check('Concurrent editors cannot overwrite same version', statuses == [200, 409], statuses)
            movements = client.get(f'/products/{identifier}/movements', headers=headers).json()
            check('Opening and successful adjustments audited only', len(movements) == 3, len(movements))
            check('Audit captures reason and actor', all(row['actor_id'] > 0 and row['reason'] for row in movements), 'actor and reason present')
            with SessionLocal() as db:
                stock = db.get(Inventory, identifier)
                check('Real MySQL persistence and stock version', stock.version == 3 and stock.on_hand in [Decimal('21'), Decimal('22')], stock.version)
                check('One inventory row per product', len(db.scalars(select(Inventory).where(Inventory.product_id == identifier)).all()) == 1, 1)
                email = f'verification.researcher.{tag.lower()}@smartinventory.local'
                password = secrets.token_urlsafe(24)
                db.add(User(email=email, name='Local Verification Researcher', role='researcher', password_hash=hash_password(password)))
                db.commit()
            researcher_login = client.post('/auth/login', json={'email': email, 'password': password})
            researcher_login.raise_for_status()
            researcher_headers = {'Authorization': 'Bearer ' + researcher_login.json()['access_token']}
            check('Researcher reads catalog', (r := client.get('/products', headers=researcher_headers)).status_code == 200, r.status_code)
            check('Researcher cannot create product', (r := client.post('/products', headers=researcher_headers, json=payload | {'sku': 'DENIED-' + tag})).status_code == 403, r.status_code)
            check('Researcher cannot adjust stock', (r := client.put(f'/products/{identifier}/inventory', headers=researcher_headers, json=inventory_payload | {'version': 3})).status_code == 403, r.status_code)
            check('Researcher logout', (r := client.post('/auth/logout', headers=researcher_headers)).status_code == 204, r.status_code)
            with SessionLocal() as db:
                db.scalar(select(User).where(User.email == email)).active = False
                db.commit()
            check('Product archive', (r := client.delete(f'/products/{identifier}', headers=headers)).status_code == 204, r.status_code)
            check('Archived product hidden', (r := client.get(f'/products/{identifier}', headers=headers)).status_code == 404, r.status_code)
            check('Archive retains audit', len(client.get(f'/products/{identifier}/movements', headers=headers).json()) == 3, 3)
            check('Category archive', (r := client.delete(f'/categories/{category_id}', headers=headers)).status_code == 204, r.status_code)
            check('Category restore', (r := client.put(f'/categories/{category_id}', headers=headers, json={'name': f'Verified {tag}', 'active': True})).status_code == 200, r.status_code)
            check('Product restore', (r := client.put(f'/products/{identifier}', headers=headers, json=updated_payload | {'active': True})).status_code == 200, r.status_code)
            # Preserve verification records/audit, archived so they do not pollute active stock views.
            client.delete(f'/products/{identifier}', headers=headers).raise_for_status()
            client.delete(f'/categories/{category_id}', headers=headers).raise_for_status()
            check('Manager logout', (r := client.post('/auth/logout', headers=headers)).status_code == 204, r.status_code)
        print(f'{len(checks)} Phase 2 live checks passed; verification catalog records archived with history preserved')
    finally:
        (root / 'docs/test-results/phase2-live.json').write_text(json.dumps({'executed_at_utc': datetime.now(UTC).isoformat(), 'checks': checks}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

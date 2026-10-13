from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from pymysql.err import OperationalError as MySQLError

from app.core.security import hash_password
from app.models import Inventory, Sale, SalesImport, StockMovement, User, utc_now
from test_catalog import create_product


def payload(product, **overrides):
    return {'product_id': product['id'], 'inventory_version': 1, 'request_key': str(uuid4()),
            'quantity': '2.500', 'unit_price': '100.25', 'sale_date': '2026-09-01T10:00:00+03:00'} | overrides


def preview(client, headers, text, **kwargs):
    return client.post('/api/v1/sales/imports/preview?filename=sales.csv',
                       headers=headers | {'Content-Type': 'text/csv'}, content=text.encode(), **kwargs)


def confirm(client, headers, batch, **overrides):
    return client.post(f"/api/v1/sales/imports/{batch['id']}/confirm", headers=headers,
                       json={'preview_version': batch['preview_version'], 'accept_valid_rows': True} | overrides)


def ledger(factory, identifier):
    with factory() as db:
        stock = db.get(Inventory, identifier)
        return (stock.on_hand, stock.version, stock.allocated, stock.confirmed_in_transit,
                db.scalar(select(func.count(Sale.id)).where(Sale.product_id == identifier)),
                db.scalar(select(func.count(StockMovement.id)).where(StockMovement.product_id == identifier)))


def test_operational_sale_persists_actor_snapshot_and_linked_audit(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    response = client.post('/api/v1/sales', headers=login, json=payload(product))
    assert response.status_code == 201, response.text
    row = response.json()
    assert row['actor_id'] == 1 and row['sku_snapshot'] == 'RICE-1'
    assert row['sale_date'] == '2026-09-01T07:00:00Z' and row['source'] == 'operational'
    assert ledger(factory, product['id']) == (Decimal('10'), 2, Decimal('0'), Decimal('0'), 1, 2)
    movement = client.get(f"/api/v1/products/{product['id']}/movements", headers=login).json()[0]
    assert movement['sale_id'] == row['id'] and movement['kind'] == 'sale'
    assert Decimal(movement['on_hand_before']) == Decimal('12.5') and Decimal(movement['on_hand_after']) == 10


def test_optional_price_and_exact_available_stock(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    response = client.post('/api/v1/sales', headers=login, json=payload(product, quantity='12.500', unit_price=None))
    assert response.status_code == 201 and response.json()['unit_price'] is None
    assert ledger(factory, product['id'])[0] == 0


def test_deadlock_retry_rolls_back_audit_then_persists_sale_once(environment, login, monkeypatch):
    from app.services import sales
    monkeypatch.setattr(sales, 'sleep', lambda _: None)
    client, factory = environment
    product, _ = create_product(client, login)
    attempts = []
    def fail_first_audit(*_):
        attempts.append(1)
        if len(attempts) == 1:
            raise OperationalError(None, None, MySQLError(1213, 'Deadlock victim'))
    event.listen(StockMovement, 'before_insert', fail_first_audit)
    try:
        body = payload(product)
        response = client.post('/api/v1/sales', headers=login, json=body)
        assert response.status_code == 201 and len(attempts) == 2
        assert ledger(factory, product['id']) == (Decimal('10'), 2, Decimal('0'), Decimal('0'), 1, 2)
        replay = client.post('/api/v1/sales', headers=login, json=body)
        assert replay.status_code == 200 and replay.json()['id'] == response.json()['id']
        assert ledger(factory, product['id'])[4:] == (1, 2)
    finally:
        event.remove(StockMovement, 'before_insert', fail_first_audit)


@pytest.mark.parametrize('code,expected_attempts', [(1213, 3), (2006, 1)])
def test_deadlock_retries_bounded_and_unrelated_database_errors_not_retried(environment, login, monkeypatch, code, expected_attempts):
    from app.services import sales
    monkeypatch.setattr(sales, 'sleep', lambda _: None)
    client, factory = environment
    product, _ = create_product(client, login)
    before = ledger(factory, product['id'])
    attempts = []
    def fail_audit(*_):
        attempts.append(1)
        raise OperationalError(None, None, MySQLError(code, 'Injected database fault'))
    event.listen(StockMovement, 'before_insert', fail_audit)
    try:
        assert client.post('/api/v1/sales', headers=login, json=payload(product)).status_code == 503
        assert len(attempts) == expected_attempts and ledger(factory, product['id']) == before
    finally:
        event.remove(StockMovement, 'before_insert', fail_audit)


@pytest.mark.parametrize('invalid', [
    {'quantity': '0'}, {'quantity': '-1'}, {'quantity': 'NaN'}, {'quantity': 'Infinity'},
    {'quantity': '1.0001'}, {'quantity': '100000000000'}, {'quantity': 'abc'},
    {'unit_price': '-1'}, {'unit_price': 'NaN'}, {'unit_price': '1.001'},
    {'sale_date': 'bad'}, {'sale_date': '2026-02-30T00:00:00Z'},
    {'sale_date': '2026-09-01T10:00:00'}, {'sale_date': '2999-01-01T00:00:00Z'},
    {'sale_date': '123'}, {'inventory_version': 0}, {'inventory_version': '1'},
    {'sale_date': 123}, {'sale_date': '0001-01-01T00:00:00Z'},
    {'product_id': -1}, {'request_key': 'bad'}, {'actor_id': 99},
])
def test_invalid_sale_cannot_change_ledger(environment, login, invalid):
    client, factory = environment
    product, _ = create_product(client, login)
    before = ledger(factory, product['id'])
    assert client.post('/api/v1/sales', headers=login, json=payload(product, **invalid)).status_code == 422
    assert ledger(factory, product['id']) == before


@pytest.mark.parametrize('change,status', [('archived', 404), ('missing', 404), ('insufficient', 409), ('stale', 409)])
def test_sale_conflicts_preserve_stock(environment, login, change, status):
    client, factory = environment
    product, _ = create_product(client, login)
    values = payload(product)
    if change == 'archived': client.delete(f"/api/v1/products/{product['id']}", headers=login)
    if change == 'missing': values['product_id'] = 99999
    if change == 'insufficient': values['quantity'] = '13'
    if change == 'stale': values['inventory_version'] = 2
    before = ledger(factory, product['id'])
    assert client.post('/api/v1/sales', headers=login, json=values).status_code == status
    assert ledger(factory, product['id']) == before


def test_allocated_and_incoming_stock_unavailable_to_sales(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    with factory() as db:
        stock = db.get(Inventory, product['id'])
        stock.allocated, stock.confirmed_in_transit = 12, 100
        db.commit()
    before = ledger(factory, product['id'])
    assert client.post('/api/v1/sales', headers=login, json=payload(product, quantity='1')).status_code == 409
    assert ledger(factory, product['id']) == before


def test_failed_audit_rolls_back_sale_stock_and_version(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    before = ledger(factory, product['id'])
    def fail(mapper, connection, row):
        if row.kind == 'sale': raise IntegrityError('injected audit failure', {}, Exception('failure'))
    event.listen(StockMovement, 'before_insert', fail)
    try:
        assert client.post('/api/v1/sales', headers=login, json=payload(product)).status_code == 409
    finally:
        event.remove(StockMovement, 'before_insert', fail)
    assert ledger(factory, product['id']) == before


def test_request_retry_is_idempotent_and_conflicting_reuse_rejected(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    values = payload(product)
    first = client.post('/api/v1/sales', headers=login, json=values)
    replay = client.post('/api/v1/sales', headers=login, json=values)
    assert first.status_code == 201 and replay.status_code == 200 and first.json()['id'] == replay.json()['id']
    assert client.post('/api/v1/sales', headers=login, json=values | {'quantity': '3'}).status_code == 409
    assert ledger(factory, product['id'])[4:] == (1, 2)


def test_sales_history_pagination_date_product_actor_source_order(environment, login):
    client, _ = environment
    product, _ = create_product(client, login)
    for version, day in enumerate([3, 1, 2], 1):
        assert client.post('/api/v1/sales', headers=login, json=payload(product, inventory_version=version,
            sale_date=f'2026-09-0{day}T00:00:00Z')).status_code == 201
    first = client.get('/api/v1/sales?limit=2', headers=login).json()
    second = client.get('/api/v1/sales?limit=2&offset=2', headers=login).json()
    assert first['total'] == 3 and len(second['items']) == 1
    assert first['items'][0]['sale_date'] > first['items'][1]['sale_date'] > second['items'][0]['sale_date']
    query = f"/api/v1/sales?product_id={product['id']}&actor_id=1&source=operational&date_from=2026-09-02T00:00:00Z&date_to=2026-09-02T00:00:00Z"
    assert client.get(query, headers=login).json()['total'] == 1
    for suffix in ['actor_id=99', 'product_id=999', 'source=historical']:
        assert client.get('/api/v1/sales?' + suffix, headers=login).json()['total'] == 0
    assert client.get('/api/v1/sales?date_from=2026-09-03T00:00:00Z&date_to=2026-09-01T00:00:00Z', headers=login).status_code == 422
    assert client.get('/api/v1/sales?date_from=2026-09-03T00:00:00', headers=login).status_code == 422


def test_csv_preview_confirm_rejections_repeat_file_and_stock_unchanged(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    csv = 'sku,sale_date,quantity,unit_price\nRICE-1,2026-09-01T10:00:00+03:00,3,45.50\nRICE-1,bad,-2,\nMISSING,2026-09-01T00:00:00Z,1,\n'
    before = ledger(factory, product['id'])
    batch = preview(client, login, csv).json()
    assert batch['valid_count'] == 1 and batch['rejected_count'] == 2 and len(batch['rejected_rows']) == 2
    assert ledger(factory, product['id']) == before
    assert confirm(client, login, batch, accept_valid_rows=False).status_code == 422
    done = confirm(client, login, batch)
    assert done.status_code == 200 and done.json()['imported_count'] == 1
    after = ledger(factory, product['id'])
    assert after[:4] == before[:4] and after[5] == before[5] and after[4] == 1
    assert confirm(client, login, batch).json()['imported_count'] == 1
    assert preview(client, login, csv).json()['status'] == 'committed'
    assert ledger(factory, product['id']) == after


@pytest.mark.parametrize('columns,row,reason', [
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z,0', 'quantity'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z,-2', 'quantity'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z,NaN', 'quantity'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z,1.0001', 'quantity'),
    ('sku,sale_date,quantity', 'RICE-1,2026-02-30T00:00:00Z,1', 'sale_date'),
    ('sku,sale_date,quantity', 'RICE-1,2999-09-01T00:00:00Z,1', 'sale_date'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01,1', 'sale_date'),
    ('sku,sale_date,quantity', 'RICE-1,123,1', 'sale_date'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z', 'Column count'),
    ('sku,sale_date,quantity', 'RICE-1,2026-09-01T00:00:00Z,1,extra', 'Column count'),
    ('sku,sale_date,quantity,unit_price', 'RICE-1,2026-09-01T00:00:00Z,1,-1', 'unit_price'),
])
def test_csv_invalid_rows_are_reported_not_silently_discarded(environment, login, columns, row, reason):
    client, factory = environment
    product, _ = create_product(client, login)
    before = ledger(factory, product['id'])
    response = preview(client, login, columns + '\n' + row + '\n')
    assert response.status_code == 200, response.text
    batch = response.json()
    assert batch['valid_count'] == 0 and batch['rejected_count'] == 1
    assert reason in batch['rejected_rows'][0]['reason'] and batch['rejected_rows'][0]['row_number'] == 2
    assert confirm(client, login, batch).status_code == 422
    assert ledger(factory, product['id']) == before


@pytest.mark.parametrize('csv,status', [
    ('sku,quantity\nRICE-1,1\n', 422), ('sku,sale_date,quantity,extra\n', 422),
    ('sku,sku,sale_date,quantity\n', 422), ('sku,sale_date,quantity\n', 422),
    ('sku,sale_date,quantity\n"broken', 422), ('', 413), ('x' * (1024 * 1024 + 1), 413),
    ('sku,sale_date,quantity\n' + 'RICE-1,2026-09-01T00:00:00Z,1\n' * 5001, 413),
], ids=['missing-column', 'extra-column', 'duplicate-header', 'header-only', 'bad-quoting', 'empty', 'oversized', 'too-many-rows'])
def test_csv_schema_and_bounds(environment, login, csv, status):
    assert preview(environment[0], login, csv).status_code == status


def test_csv_encoding_and_content_type(environment, login):
    client, _ = environment
    assert client.post('/api/v1/sales/imports/preview', headers=login | {'Content-Type': 'text/csv'}, content=b'\xff').status_code == 422
    assert client.post('/api/v1/sales/imports/preview', headers=login, json={}).status_code == 415


def test_duplicate_rows_across_files_and_external_ids(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    row = 'RICE-1,2026-09-01T00:00:00Z,2\n'
    batch = preview(client, login, 'sku,sale_date,quantity\n' + row * 2).json()
    assert batch['valid_count'] == 1 and 'Duplicate' in batch['rejected_rows'][0]['reason']
    assert confirm(client, login, batch).status_code == 200
    another = preview(client, login, 'sku,sale_date,quantity\n' + row + row.replace(',2\n', ',3\n')).json()
    assert another['valid_count'] == 1 and 'Already imported' in another['rejected_rows'][0]['reason']
    external = preview(client, login, 'sku,sale_date,quantity,external_id\n' + row.strip() + ',A\n' + row.strip() + ',B\n').json()
    assert external['valid_count'] == 2
    assert confirm(client, login, external).status_code == 200
    conflicting = preview(client, login, 'sku,sale_date,quantity,external_id\nRICE-1,2026-09-01T00:00:00Z,9,A\n').json()
    assert conflicting['valid_count'] == 0 and conflicting['rejected_count'] == 1
    assert ledger(factory, product['id'])[0] == Decimal('12.5')


def test_archived_after_preview_fails_entire_import_and_repreview_rejects(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    csv = 'sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,2\n'
    batch = preview(client, login, csv).json()
    client.delete(f"/api/v1/products/{product['id']}", headers=login)
    assert confirm(client, login, batch).status_code == 409
    refreshed = preview(client, login, csv).json()
    assert refreshed['valid_count'] == 0 and 'archived' in refreshed['rejected_rows'][0]['reason']
    assert ledger(factory, product['id'])[4] == 0


def test_preview_version_and_expiry(environment, login):
    client, factory = environment
    create_product(client, login)
    csv = 'sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,2\n'
    first = preview(client, login, csv).json()
    second = preview(client, login, csv).json()
    assert first['id'] == second['id'] and second['preview_version'] == 2
    assert confirm(client, login, first).status_code == 409
    with factory() as db:
        db.get(SalesImport, first['id']).created_at = utc_now() - timedelta(minutes=31)
        db.commit()
    assert confirm(client, login, second).status_code == 409


def test_preview_confirmation_requires_the_previewing_manager(environment, login):
    client, factory = environment
    create_product(client, login)
    batch = preview(client, login, 'sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,2\n').json()
    with factory() as db:
        db.add(User(name='Other manager', email='other@example.com', password_hash=hash_password('other-manager-password')))
        db.commit()
    token = client.post('/api/v1/auth/login', json={'email': 'other@example.com', 'password': 'other-manager-password'}).json()['access_token']
    assert confirm(client, {'Authorization': 'Bearer ' + token}, batch).status_code == 403


def test_conflicting_import_rolls_back_all_rows_and_batch_status(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    one = 'RICE-1,2026-09-01T00:00:00Z,2\n'
    first = preview(client, login, 'sku,sale_date,quantity\n' + one).json()
    competing = preview(client, login, 'sku,sale_date,quantity\n' + one + one.replace(',2\n', ',3\n')).json()
    assert competing['valid_count'] == 2
    assert confirm(client, login, first).status_code == 200
    assert confirm(client, login, competing).status_code == 409
    with factory() as db:
        assert db.get(SalesImport, competing['id']).status == 'preview'
    assert ledger(factory, product['id'])[4] == 1


def test_researcher_and_anonymous_cannot_write_sales_or_import(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    batch = preview(client, login, 'sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,2\n').json()
    with factory() as db:
        db.add(User(name='Researcher', email='research@example.com', role='researcher', password_hash=hash_password('research-password')))
        db.commit()
    token = client.post('/api/v1/auth/login', json={'email': 'research@example.com', 'password': 'research-password'}).json()['access_token']
    for headers, status in [({}, 401), ({'Authorization': 'Bearer ' + token}, 403)]:
        assert client.post('/api/v1/sales', headers=headers, json=payload(product)).status_code == status
        assert preview(client, headers, 'sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,2\n').status_code == status
        assert confirm(client, headers, batch).status_code == status
    assert client.get('/api/v1/sales', headers={'Authorization': 'Bearer ' + token}).status_code == 200
    assert ledger(factory, product['id'])[4] == 0

from decimal import Decimal

from fastapi import HTTPException

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models import Inventory, Product, StockMovement, User
from app.catalog_schemas import InventoryWrite
from app.services.catalog import adjust_inventory


def create_product(client, headers, **overrides):
    category = client.post('/api/v1/categories', headers=headers, json={'name': 'Groceries'}).json()
    payload = {'sku': 'rice-1', 'name': 'Rice', 'category_id': category['id'], 'initial_stock': '12.500',
               'safety_stock': '3', 'lead_time_days': 5, 'overstock_multiplier': '2.5'} | overrides
    response = client.post('/api/v1/products', headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json(), payload


@pytest.fixture
def researcher(environment):
    client, factory = environment
    with factory() as db:
        db.add(User(name='Researcher', email='researcher@example.com', role='researcher', password_hash=hash_password('researcher-password')))
        db.commit()
    token = client.post('/api/v1/auth/login', json={'email': 'researcher@example.com', 'password': 'researcher-password'}).json()['access_token']
    return {'Authorization': 'Bearer ' + token}


def test_category_crud_archive_and_restore(environment, login):
    client, _ = environment
    created = client.post('/api/v1/categories', headers=login, json={'name': '  Food  '})
    assert created.status_code == 201 and created.json()['name'] == 'Food'
    identifier = created.json()['id']
    assert client.get(f'/api/v1/categories/{identifier}', headers=login).status_code == 200
    assert client.put(f'/api/v1/categories/{identifier}', headers=login, json={'name': 'Staples'}).json()['name'] == 'Staples'
    assert client.delete(f'/api/v1/categories/{identifier}', headers=login).status_code == 204
    assert client.get(f'/api/v1/categories/{identifier}', headers=login).status_code == 404
    assert client.get('/api/v1/categories', headers=login).json() == []
    assert client.get('/api/v1/categories?include_archived=true', headers=login).json()[0]['active'] is False
    assert client.put(f'/api/v1/categories/{identifier}', headers=login, json={'name': 'Staples', 'active': True}).status_code == 200


def test_duplicate_category_case_and_archived_name(environment, login):
    client, _ = environment
    identifier = client.post('/api/v1/categories', headers=login, json={'name': 'Food'}).json()['id']
    assert client.post('/api/v1/categories', headers=login, json={'name': 'food'}).status_code == 409
    client.delete(f'/api/v1/categories/{identifier}', headers=login)
    assert client.post('/api/v1/categories', headers=login, json={'name': 'FOOD'}).status_code == 409


@pytest.mark.parametrize('payload', [{'name': '   '}, {'name': 'x' * 121}, {'name': 'Food', 'unknown': 1}, {}])
def test_category_validation(environment, login, payload):
    assert environment[0].post('/api/v1/categories', headers=login, json=payload).status_code == 422


def test_product_create_with_exact_inventory_and_opening_audit(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    assert product['sku'] == 'RICE-1' and product['lead_time_days'] == 5
    assert Decimal(product['safety_stock']) == 3
    assert Decimal(product['overstock_multiplier']) == Decimal('2.5')
    assert Decimal(product['inventory']['on_hand']) == Decimal('12.500')
    with factory() as db:
        assert len(db.scalars(select(Inventory)).all()) == 1
        movement = db.scalar(select(StockMovement))
        assert movement.kind == 'opening' and movement.actor_id == 1
        assert movement.on_hand_before == 0 and movement.on_hand_after == Decimal('12.5')


def test_product_update_preserves_inventory(environment, login):
    client, _ = environment
    product, payload = create_product(client, login)
    payload.pop('initial_stock')
    payload.update(name='Brown rice', lead_time_days=10, safety_stock='5', overstock_multiplier='3')
    response = client.put(f"/api/v1/products/{product['id']}", headers=login, json=payload)
    assert response.status_code == 200
    assert response.json()['name'] == 'Brown rice'
    assert Decimal(response.json()['inventory']['on_hand']) == Decimal('12.5')


def test_unique_normalized_sku_on_create_and_update(environment, login):
    client, _ = environment
    product, payload = create_product(client, login)
    assert client.post('/api/v1/products', headers=login, json=payload | {'sku': 'RICE-1'}).status_code == 409
    second = client.post('/api/v1/products', headers=login, json=payload | {'sku': 'OTHER'}).json()
    payload.pop('initial_stock')
    assert client.put(f"/api/v1/products/{second['id']}", headers=login, json=payload).status_code == 409
    client.delete(f"/api/v1/products/{product['id']}", headers=login)
    assert client.post('/api/v1/products', headers=login, json=payload).status_code == 409


@pytest.mark.parametrize('changes', [
    {'sku': 'bad sku'}, {'name': ' '}, {'lead_time_days': 0}, {'lead_time_days': 366}, {'lead_time_days': 1.5},
    {'safety_stock': '-1'}, {'initial_stock': '-1'}, {'overstock_multiplier': '1'},
    {'initial_stock': '1.0001'}, {'safety_stock': 'NaN'}, {'unit': ''}, {'category_id': 9999},
])
def test_product_input_validation(environment, login, changes):
    client, _ = environment
    category = client.post('/api/v1/categories', headers=login, json={'name': 'Food'}).json()
    response = client.post('/api/v1/products', headers=login, json={'sku': 'SKU', 'name': 'Rice', 'category_id': category['id']} | changes)
    assert response.status_code == 422
    assert client.get('/api/v1/products', headers=login).json() == []


def test_referenced_category_cannot_archive(environment, login):
    client, _ = environment
    _, payload = create_product(client, login)
    path = f"/api/v1/categories/{payload['category_id']}"
    assert client.delete(path, headers=login).status_code == 409
    assert client.put(path, headers=login, json={'name': 'Food', 'active': False}).status_code == 409


def test_archived_category_rejects_active_product_and_restore(environment, login):
    client, _ = environment
    product, payload = create_product(client, login)
    client.delete(f"/api/v1/products/{product['id']}", headers=login)
    client.delete(f"/api/v1/categories/{payload['category_id']}", headers=login)
    assert client.post('/api/v1/products', headers=login, json=payload | {'sku': 'NEW'}).status_code == 422
    payload.pop('initial_stock')
    assert client.put(f"/api/v1/products/{product['id']}", headers=login, json=payload).status_code == 422


def test_product_archive_preserves_audit_and_stock(environment, login):
    client, factory = environment
    product, payload = create_product(client, login)
    path = f"/api/v1/products/{product['id']}"
    assert client.delete(path, headers=login).status_code == 204
    assert client.get(path, headers=login).status_code == 404
    assert len(client.get(path + '/movements', headers=login).json()) == 1
    assert client.get('/api/v1/products', headers=login).json() == []
    with factory() as db:
        assert db.get(Inventory, product['id']).on_hand == Decimal('12.5')
    payload.pop('initial_stock')
    assert client.put(path, headers=login, json=payload).status_code == 200


def test_inventory_adjustment_records_before_after_actor_and_version(environment, login):
    client, _ = environment
    product, _ = create_product(client, login)
    path = f"/api/v1/products/{product['id']}/inventory"
    response = client.put(path, headers=login, json={'on_hand': '20', 'confirmed_in_transit': '10', 'allocated': '2', 'version': 1, 'reason': 'Physical stock count'})
    assert response.status_code == 200 and response.json()['version'] == 2
    movement = client.get(f"/api/v1/products/{product['id']}/movements", headers=login).json()[0]
    assert movement['kind'] == 'adjustment' and movement['reason'] == 'Physical stock count'
    assert Decimal(movement['on_hand_before']) == Decimal('12.5') and Decimal(movement['on_hand_after']) == 20
    assert Decimal(movement['in_transit_after']) == 10 and Decimal(movement['allocated_after']) == 2


@pytest.mark.parametrize('changes', [{'on_hand': '-1'}, {'allocated': '30'}, {'confirmed_in_transit': '-2'}, {'on_hand': 'Infinity'}, {'reason': ' '}, {'version': 0}])
def test_inventory_validation_does_not_write_audit(environment, login, changes):
    client, _ = environment
    product, _ = create_product(client, login)
    response = client.put(f"/api/v1/products/{product['id']}/inventory", headers=login, json={'on_hand': '10', 'confirmed_in_transit': '1', 'allocated': '0', 'version': 1, 'reason': 'Count correction'} | changes)
    assert response.status_code == 422
    assert len(client.get(f"/api/v1/products/{product['id']}/movements", headers=login).json()) == 1


def test_stale_inventory_version_rejected_without_changes(environment, login):
    client, _ = environment
    product, _ = create_product(client, login)
    path = f"/api/v1/products/{product['id']}/inventory"
    payload = {'on_hand': '10', 'confirmed_in_transit': '0', 'allocated': '0', 'version': 1, 'reason': 'Count correction'}
    assert client.put(path, headers=login, json=payload).status_code == 200
    assert client.put(path, headers=login, json=payload | {'on_hand': '15'}).status_code == 409
    assert Decimal(client.get(path, headers=login).json()['on_hand']) == 10
    assert len(client.get(f"/api/v1/products/{product['id']}/movements", headers=login).json()) == 2


def test_audit_failure_rolls_back_inventory(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    def reject(*_):
        raise IntegrityError('insert stock movement', {}, Exception('simulated integrity failure'))
    event.listen(StockMovement, 'before_insert', reject)
    try:
        response = client.put(f"/api/v1/products/{product['id']}/inventory", headers=login, json={'on_hand': '99', 'confirmed_in_transit': '0', 'allocated': '0', 'version': 1, 'reason': 'Test count'})
        assert response.status_code == 409
    finally:
        event.remove(StockMovement, 'before_insert', reject)
    with factory() as db:
        assert db.get(Inventory, product['id']).on_hand == Decimal('12.5')
        assert db.get(Inventory, product['id']).version == 1


def test_locked_read_refreshes_preloaded_inventory_version(environment, login):
    client, factory = environment
    product, _ = create_product(client, login)
    with factory() as first:
        cached_stock = first.get(Inventory, product['id'])
        assert cached_stock.version == 1
        with factory() as second:
            second.get(Inventory, product['id']).version = 2
            second.commit()
        payload = InventoryWrite(on_hand='99', confirmed_in_transit='0', allocated='0', version=1, reason='Stale editor')
        with pytest.raises(HTTPException) as error:
            adjust_inventory(first, product['id'], payload, first.get(User, 1))
        assert error.value.status_code == 409


def test_researcher_reads_but_cannot_mutate_any_catalog_endpoint(environment, login, researcher):
    client, _ = environment
    product, payload = create_product(client, login)
    assert client.get('/api/v1/products', headers=researcher).status_code == 200
    assert client.get('/api/v1/categories', headers=researcher).status_code == 200
    for method, path in [('post', '/categories'), ('put', f"/categories/{payload['category_id']}"), ('delete', f"/categories/{payload['category_id']}"),
                         ('post', '/products'), ('put', f"/products/{product['id']}"), ('delete', f"/products/{product['id']}"), ('put', f"/products/{product['id']}/inventory")]:
        response = client.delete('/api/v1' + path, headers=researcher) if method == 'delete' else getattr(client, method)('/api/v1' + path, headers=researcher, json={})
        assert response.status_code == 403


def test_anonymous_catalog_access_rejected(environment):
    client, _ = environment
    assert client.get('/api/v1/categories').status_code == 401
    assert client.get('/api/v1/products').status_code == 401
    assert client.post('/api/v1/products', json={}).status_code == 401


def test_missing_record_and_pagination_validation(environment, login):
    client, _ = environment
    for path in ['/categories/9999', '/products/9999', '/products/9999/inventory', '/products/9999/movements']:
        assert client.get('/api/v1' + path, headers=login).status_code == 404
    assert client.get('/api/v1/products?limit=1000', headers=login).status_code == 422

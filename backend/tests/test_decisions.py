from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace as Obj
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import Forecast, ForecastMapping, Inventory, Product, Recommendation, Sale, SalesImport, StockMovement
from app.services import decisions, forecast_runtime as runtime
from test_catalog import create_product, researcher


def objects():
    product = Obj(id=1, sku='TEST', unit='unit', lead_time_days=3, safety_stock=D(4), overstock_multiplier=D(2))
    stock = Obj(on_hand=D(5), confirmed_in_transit=D(3), allocated=D(2), version=1)
    mapping = Obj(id='map', series_sku='20728', source_namespace=runtime.NAMESPACE)
    registry = dict(model_id='mean', model_version='v1', artifact_sha256='digest', feature_version='f1')
    origin = decisions.today() - timedelta(days=1)
    forecast = Obj(id='forecast', product_id=1, product_sku='TEST', unit='unit', mapping_id='map', series_sku='20728',
                   source_namespace=runtime.NAMESPACE, context='operational', forecast_origin=origin, horizon=3,
                   model_id='mean', model_version='v1', artifact_version='sha256:digest', feature_version='f1',
                   points=[Obj(horizon_day=n, forecast_date=origin + timedelta(days=n), predicted_quantity=D(n)) for n in [1, 2, 3]])
    return product, stock, forecast, mapping, registry


def calculate(items): return decisions.calculate(*items, decisions.today(), 'operational')


def test_inventory_position_multi_day_target_and_safety_stock():
    result = calculate(objects())
    assert D(result['inventory_position']) == 6
    assert D(result['predicted_lead_time_demand']) == 6
    assert D(result['target_stock']) == 10 and D(result['overstock_threshold']) == 20
    assert D(result['suggested_reorder']) == 4 and result['suggested_reorder'] == result['suggested_reorder_raw']
    assert result['risk_status'] == 'REPLENISH'


@pytest.mark.parametrize('on_hand,incoming,allocated,risk,reorder', [(10, 0, 0, 'ADEQUATE', 0),
    (20, 0, 0, 'ADEQUATE', 0), (21, 0, 0, 'OVERSTOCK', 0), (0, 0, 0, 'REPLENISH', 10),
    (10, 0, 10, 'REPLENISH', 10), (0, 10, 0, 'ADEQUATE', 0), (5, 3, 2, 'REPLENISH', 4)])
def test_risk_boundaries_allocation_and_incoming(on_hand, incoming, allocated, risk, reorder):
    items = objects(); stock = items[1]
    stock.on_hand, stock.confirmed_in_transit, stock.allocated = D(on_hand), D(incoming), D(allocated)
    result = calculate(items)
    assert result['risk_status'] == risk and D(result['suggested_reorder']) == reorder


@pytest.mark.parametrize('mutation', ['stale', 'product', 'sku', 'unit', 'mapping', 'series', 'namespace',
    'model', 'version', 'artifact', 'feature', 'horizon_short', 'horizon_count', 'step', 'gap', 'negative', 'context'])
def test_invalid_forecast_rejected(mutation):
    items = objects(); forecast = items[2]
    changes = {'stale': ('forecast_origin', forecast.forecast_origin - timedelta(days=1)), 'product': ('product_id', 2),
               'sku': ('product_sku', 'OTHER'), 'unit': ('unit', 'kg'), 'mapping': ('mapping_id', 'other'),
               'series': ('series_sku', 'OTHER'), 'namespace': ('source_namespace', 'other'), 'model': ('model_id', 'other'),
               'version': ('model_version', 'other'), 'artifact': ('artifact_version', 'bad'), 'feature': ('feature_version', 'other'),
               'horizon_short': ('horizon', 2), 'horizon_count': ('horizon', 4), 'context': ('context', 'research_demo')}
    if mutation in changes: setattr(forecast, *changes[mutation])
    if mutation == 'step': forecast.points[0].horizon_day = 2
    if mutation == 'gap': forecast.points[1].forecast_date += timedelta(days=1)
    if mutation == 'negative': forecast.points[1].predicted_quantity = D(-1)
    with pytest.raises(HTTPException) as error: calculate(items)
    assert error.value.status_code == 409


@pytest.mark.parametrize('field,value', [('safety_stock', None), ('safety_stock', D(-1)), ('overstock_multiplier', D(1)),
                                      ('lead_time_days', 0), ('lead_time_days', True)])
def test_missing_or_invalid_replenishment_parameters(field, value):
    items = objects(); setattr(items[0], field, value)
    with pytest.raises(HTTPException) as error: calculate(items)
    assert error.value.status_code == 422


def mapped_product(client, headers, stock='5'):
    item, _ = create_product(client, headers, sku='PHASE5-TEST', unit='unit', initial_stock=stock, lead_time_days=3, safety_stock='4')
    response = client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=headers,
                           json=dict(series_sku='20728', confirm_research_demo=True, reason='Synthetic UK research inventory scenario'))
    assert response.status_code == 201, response.text
    return item


def generate(client, headers, item, **changes):
    payload = dict(request_key=str(uuid4()), forecast_origin='2011-11-10', horizon=28, context='research_demo', confirm_research_demo=True)
    payload.update(changes)
    return client.post(f'/api/v1/forecasts/{item["id"]}/generate', headers=headers, json=payload), payload


def recommend(client, headers, item, forecast_id, **changes):
    payload = dict(request_key=str(uuid4()), forecast_id=forecast_id, context='research_demo', decision_as_of='2011-11-11', confirm_research_demo=True)
    payload.update(changes)
    return client.post(f'/api/v1/recommendations/{item["id"]}/generate', headers=headers, json=payload), payload


def test_actual_artifact_inference_schema_persistence_and_retry(environment, login):
    client, factory = environment; item = mapped_product(client, login)
    response, payload = generate(client, login, item)
    assert response.status_code == 201, response.text
    value = response.json()
    assert len(value['points']) == 28 and value['product_sku'] == item['sku'] and value['series_sku'] == '20728'
    assert value['contract']['sku'] == '20728' and value['model_version'] == 'retail-demand-v1'
    assert value['artifact_version'].startswith('sha256:')
    replay = client.post(f'/api/v1/forecasts/{item["id"]}/generate', headers=login, json=payload)
    assert replay.json()['id'] == value['id']
    payload['horizon'] = 7
    assert client.post(f'/api/v1/forecasts/{item["id"]}/generate', headers=login, json=payload).status_code == 409
    with factory() as db: assert db.scalar(select(func.count(Forecast.id))) == 1


def test_snapshot_history_immutable_and_new_stock_requires_new_request(environment, login):
    client, factory = environment; item = mapped_product(client, login)
    generated, _ = generate(client, login, item)
    response, payload = recommend(client, login, item, generated.json()['id'])
    assert response.status_code == 201, response.text
    original = response.json(); snapshot = original['snapshot']
    assert snapshot['risk_status'] == 'REPLENISH' and snapshot['lead_time_days'] == 3
    assert D(snapshot['target_stock']) == D(snapshot['predicted_lead_time_demand']) + 4
    assert client.put(f'/api/v1/products/{item["id"]}/inventory', headers=login,
                      json=dict(on_hand='999', allocated='2', confirmed_in_transit='3', version=1, reason='Synthetic stock change')).status_code == 200
    assert client.post(f'/api/v1/recommendations/{item["id"]}/generate', headers=login, json=payload).json() == original
    new, _ = recommend(client, login, item, generated.json()['id'])
    assert new.json()['snapshot']['risk_status'] == 'OVERSTOCK' and new.json()['id'] != original['id']
    assert client.get(f'/api/v1/recommendations/{item["id"]}', headers=login).json()[1] == original
    with factory() as db:
        row = db.get(Recommendation, original['id']); row.snapshot = {'corrupted': True}
        with pytest.raises(ValueError, match='append-only'): db.commit()
        db.rollback(); db.delete(db.get(Forecast, generated.json()['id']))
        with pytest.raises(ValueError, match='append-only'): db.commit()


def test_unsupported_sku_even_if_application_sku_matches(environment, login):
    client, _ = environment; item, _ = create_product(client, login, sku='20728', unit='unit')
    assert generate(client, login, item)[0].status_code == 422
    assert client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=login,
                       json=dict(series_sku='UNSEEN', confirm_research_demo=True, reason='Unsupported series test')).status_code == 422


@pytest.mark.parametrize('failure', ['missing', 'incompatible', 'corrupt'])
def test_failure_isolation_preserves_operational_records(environment, login, monkeypatch, failure):
    client, factory = environment; item = mapped_product(client, login)
    def ledger():
        with factory() as db:
            return [db.scalar(select(func.count()).select_from(model)) for model in
                    [Product, Inventory, Sale, StockMovement, SalesImport, Forecast, Recommendation]]
    before = ledger()
    def broken(): raise HTTPException(503, f'Forecast artifact {failure}')
    monkeypatch.setattr(runtime, 'load', broken)
    assert generate(client, login, item)[0].status_code == 503
    assert ledger() == before and client.get('/api/v1/products', headers=login).status_code == 200


@pytest.mark.parametrize('change,expected', [({'forecast_origin': '2026-10-01'}, 409), ({'horizon': 29}, 422),
                                            ({'horizon': True}, 422), ({'context': 'operational'}, 409)])
def test_invalid_forecast_origin_horizon_and_context(environment, login, change, expected):
    client, _ = environment; item = mapped_product(client, login)
    assert generate(client, login, item, **change)[0].status_code == expected


def test_stale_missing_mismatched_and_short_forecast_api(environment, login):
    client, _ = environment; item = mapped_product(client, login)
    short, _ = generate(client, login, item, horizon=2)
    assert recommend(client, login, item, short.json()['id'])[0].status_code == 409
    assert recommend(client, login, item, str(uuid4()))[0].status_code == 404
    full, _ = generate(client, login, item)
    assert recommend(client, login, item, full.json()['id'], decision_as_of='2011-11-12')[0].status_code == 409
    other = client.post('/api/v1/products', headers=login, json=dict(sku='OTHER-DEMO', name='Other synthetic product',
                        category_id=item['category_id'], unit='unit')).json()
    client.post(f'/api/v1/products/{other["id"]}/forecast-mappings', headers=login,
                json=dict(series_sku='20728', confirm_research_demo=True, reason='Other synthetic scenario'))
    assert recommend(client, login, other, full.json()['id'])[0].status_code == 409


def test_read_roles_write_roles_and_authentication(environment, login, researcher):
    client, _ = environment; item = mapped_product(client, login)
    for path in ['/forecast-support', '/research/models', '/dashboard', f'/forecasts/{item["id"]}', f'/recommendations/{item["id"]}']:
        assert client.get('/api/v1' + path, headers=researcher).status_code == 200
        assert client.get('/api/v1' + path).status_code == 401
    assert generate(client, researcher, item)[0].status_code == 403
    assert recommend(client, researcher, item, str(uuid4()))[0].status_code == 403
    assert client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=researcher,
                       json=dict(series_sku='20728', confirm_research_demo=True, reason='Forbidden write')).status_code == 403


def test_dashboard_empty_real_comparison_and_stock_refresh(environment, login):
    client, _ = environment
    assert client.get('/api/v1/dashboard', headers=login).json()['total_active_products'] == 0
    comparison = client.get('/api/v1/research/models', headers=login).json()
    assert comparison['selected'] == 'mean_28'
    mean = next(row for row in comparison['models'] if row['selected'])
    assert mean['validation']['mae'] == pytest.approx(4.7536352040816325)
    assert mean['final_test']['mae'] == pytest.approx(5.3350340136054415)
    item = mapped_product(client, login)
    generated, _ = generate(client, login, item)
    recommend(client, login, item, generated.json()['id'])
    assert client.get('/api/v1/dashboard?context=research_demo', headers=login).json()['status_counts']['REPLENISH'] == 1
    assert client.get('/api/v1/dashboard', headers=login).json()['status_counts']['UNASSESSED'] == 1
    client.put(f'/api/v1/products/{item["id"]}/inventory', headers=login,
               json=dict(on_hand='8', confirmed_in_transit='0', allocated='0', version=1, reason='Synthetic change'))
    assert client.get('/api/v1/dashboard?context=research_demo', headers=login).json()['status_counts']['UNASSESSED'] == 1


@pytest.mark.parametrize('failure', ['missing', 'corrupt', 'incompatible'])
def test_real_loader_refuses_missing_corrupt_or_changed_metadata(tmp_path, monkeypatch, failure):
    import json
    from pathlib import Path
    source = runtime.ROOT
    ref = json.loads(runtime.REFERENCE.read_text())
    for name in ['model-registry.json', 'frozen-selection.json']:
        target = tmp_path / 'docs/research/results' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / 'docs/research/results' / name).read_bytes())
    registry = json.loads((tmp_path / 'docs/research/results/model-registry.json').read_text())
    if failure == 'corrupt':
        target = tmp_path / registry['artifact_path']; target.parent.mkdir(parents=True)
        target.write_bytes(b'corrupt artifact, deliberately isolated test fixture')
    if failure == 'incompatible':
        registry['candidate'] = 'seasonal_naive'
        (tmp_path / 'docs/research/results/model-registry.json').write_text(json.dumps(registry))
    monkeypatch.setattr(runtime, 'ROOT', tmp_path)
    with pytest.raises(HTTPException) as error: runtime.load()
    assert error.value.status_code == 503


def test_changed_mapping_disables_old_forecast_and_keeps_evidence(environment, login):
    client, factory = environment; item = mapped_product(client, login)
    fc, _ = generate(client, login, item)
    response = client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=login,
                          json=dict(series_sku='20728', enabled=False, confirm_research_demo=True, reason='Disable synthetic scenario'))
    assert response.status_code == 201 and response.json()['sequence'] == 2
    assert recommend(client, login, item, fc.json()['id'])[0].status_code == 422
    assert generate(client, login, item)[0].status_code == 422
    with factory() as db:
        assert db.scalar(select(func.count(ForecastMapping.id))) == 2
        assert db.scalar(select(func.count(Forecast.id))) == 1


def test_non_count_units_and_unacknowledged_scenarios_rejected(environment, login):
    client, _ = environment; item, _ = create_product(client, login, unit='kg')
    body = dict(series_sku='20728', confirm_research_demo=True, reason='No implicit unit conversion')
    assert client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=login, json=body).status_code == 422
    body['confirm_research_demo'] = False
    assert client.post(f'/api/v1/products/{item["id"]}/forecast-mappings', headers=login, json=body).status_code == 422

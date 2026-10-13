"""Append-only decisions; raw decimal rules, explicit identities and dated coverage."""
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Forecast, ForecastMapping, ForecastPointRecord, Inventory, Product, Recommendation
from app.services import forecast_runtime as runtime

RULE_VERSION = 'inventory-rules-v1'
PRECISION = Decimal('0.000000001')


def today(): return datetime.now(ZoneInfo('Africa/Nairobi')).date()


def fingerprint(product_id, payload):
    return hashlib.sha256(json.dumps({'product_id': product_id, **payload.model_dump(mode='json', exclude={'request_key'})},
                                    sort_keys=True).encode()).hexdigest()


def locked_product(db, identifier):
    row = db.scalar(select(Product).where(Product.id == identifier).with_for_update().execution_options(populate_existing=True))
    if not row or not row.active: raise HTTPException(404, 'Active product not found')
    return row


def latest_mapping(db, identifier):
    return db.scalar(select(ForecastMapping).where(ForecastMapping.product_id == identifier)
                     .order_by(ForecastMapping.sequence.desc()).limit(1))


def require_mapping(db, product):
    mapping = latest_mapping(db, product.id)
    if not mapping or not mapping.enabled:
        raise HTTPException(422, 'Forecast unavailable — insufficient or unsupported historical series. Explicit manager mapping required.')
    if mapping.product_sku != product.sku or mapping.unit != product.unit or mapping.source_namespace != runtime.NAMESPACE:
        raise HTTPException(409, 'Product/SKU/unit differs from its documented series mapping; remap explicitly')
    return mapping


def append_mapping(db, identifier, payload, actor):
    product = locked_product(db, identifier)
    _, registry = runtime.load()
    if payload.series_sku not in registry['skus']:
        raise HTTPException(422, 'Forecast unavailable — insufficient or unsupported historical series')
    if product.unit != 'unit':
        raise HTTPException(422, 'UK reference series count individual units; mapping requires product unit "unit"')
    previous = latest_mapping(db, identifier)
    row = ForecastMapping(id=str(uuid4()), product_id=identifier, product_sku=product.sku, unit=product.unit,
                          series_sku=payload.series_sku, source_namespace=runtime.NAMESPACE, enabled=payload.enabled,
                          sequence=previous.sequence + 1 if previous else 1, reason=payload.reason, actor_id=actor.id)
    db.add(row); db.commit()
    return row


def retry(db, model, key, actor, digest):
    row = db.scalar(select(model).where(model.request_key == str(key)))
    if row:
        if row.actor_id != actor.id or row.request_fingerprint != digest:
            raise HTTPException(409, 'Request key belongs to a different actor or request; use a new key')
        return row


def commit_evidence(db, row, model, payload, actor, digest):
    try:
        db.add(row); db.commit()
    except IntegrityError:
        db.rollback()
        existing = retry(db, model, payload.request_key, actor, digest)
        if existing: return existing
        raise HTTPException(409, 'Concurrent evidence conflict; retry with the same request key') from None
    return row


def generate_forecast(db, identifier, payload, actor):
    product = locked_product(db, identifier)
    mapping = require_mapping(db, product)
    digest = fingerprint(identifier, payload)
    existing = retry(db, Forecast, payload.request_key, actor, digest)
    if existing: return existing
    if payload.context != 'research_demo' or not payload.confirm_research_demo:
        raise HTTPException(409, 'UK reference mappings support acknowledged historical research demonstrations only; current operational history is unavailable')
    output, registry = runtime.infer(mapping.series_sku, payload.forecast_origin, payload.horizon)
    row = Forecast(id=str(uuid4()), product_id=identifier, product_sku=product.sku, unit=product.unit, mapping_id=mapping.id,
                   series_sku=mapping.series_sku, source_namespace=runtime.NAMESPACE, context=payload.context,
                   forecast_origin=output.forecast_origin, horizon=output.horizon_days, model_id=registry['model_id'],
                   model_version=registry['model_version'], artifact_version='sha256:' + registry['artifact_sha256'],
                   feature_version=registry['feature_version'], actor_id=actor.id, request_key=str(payload.request_key),
                   request_fingerprint=digest, contract=output.model_dump(mode='json'))
    row.points = [ForecastPointRecord(horizon_day=point.horizon_day, forecast_date=point.forecast_date,
                     predicted_quantity=Decimal(str(point.predicted_demand)).quantize(PRECISION, rounding=ROUND_HALF_UP)) for point in output.points]
    return commit_evidence(db, row, Forecast, payload, actor, digest)


def calculate(product, stock, forecast, mapping, registry, as_of, context):
    if forecast.product_id != product.id or forecast.product_sku != product.sku or forecast.unit != product.unit:
        raise HTTPException(409, 'Forecast product/SKU/unit mismatch')
    if forecast.mapping_id != mapping.id or forecast.series_sku != mapping.series_sku or forecast.source_namespace != mapping.source_namespace:
        raise HTTPException(409, 'Forecast series mapping changed; request a new forecast')
    if (forecast.model_id != registry['model_id'] or forecast.model_version != registry['model_version']
            or forecast.artifact_version != 'sha256:' + registry['artifact_sha256'] or forecast.feature_version != registry['feature_version']):
        raise HTTPException(409, 'Incompatible forecast model or artifact version')
    if forecast.context != context: raise HTTPException(409, 'Forecast context mismatch')
    if forecast.forecast_origin != as_of - timedelta(days=1): raise HTTPException(409, 'Stale forecast: origin must be the day before the decision date')
    if context == 'operational' and as_of != today(): raise HTTPException(409, 'Operational decisions require the current Nairobi date')
    if context == 'research_demo' and as_of.isoformat() != runtime.DEMO_DAY:
        raise HTTPException(409, 'Historical research decisions require explicit as-of 2011-11-11')
    try:
        lead = product.lead_time_days
        safety, multiplier = Decimal(product.safety_stock), Decimal(product.overstock_multiplier)
        on_hand, incoming, allocated = [Decimal(getattr(stock, field)) for field in ['on_hand', 'confirmed_in_transit', 'allocated']]
        values = [safety, multiplier, on_hand, incoming, allocated]
        if not all(value.is_finite() for value in values) or min(safety, on_hand, incoming, allocated) < 0 or allocated > on_hand or multiplier <= 1:
            raise ValueError()
        if not isinstance(lead, int) or isinstance(lead, bool) or not 1 <= lead <= 365: raise ValueError()
    except (TypeError, ValueError, ArithmeticError):
        raise HTTPException(422, 'Required valid inventory/replenishment parameters are missing') from None
    points = sorted(forecast.points, key=lambda point: point.horizon_day)
    if forecast.horizon < lead or forecast.horizon > 28 or len(points) != forecast.horizon:
        raise HTTPException(409, 'Insufficient or mismatched forecast horizon; no extrapolation allowed')
    for step, point in enumerate(points, 1):
        if point.horizon_day != step or point.forecast_date != forecast.forecast_origin + timedelta(days=step):
            raise HTTPException(409, 'Forecast date/horizon coverage mismatch')
        if not Decimal(point.predicted_quantity).is_finite() or point.predicted_quantity < 0:
            raise HTTPException(409, 'Invalid stored forecast quantity')
    demand = sum((point.predicted_quantity for point in points[:lead]), Decimal(0))
    position = on_hand + incoming - allocated
    target = demand + safety
    shortage = max(Decimal(0), target - position)
    threshold = target * multiplier
    state = 'REPLENISH' if shortage > 0 else 'OVERSTOCK' if position > threshold else 'ADEQUATE'
    quantity_values = dict(predicted_lead_time_demand=demand, on_hand=on_hand, confirmed_in_transit=incoming, allocated=allocated,
                           inventory_position=position, safety_stock=safety, target_stock=target, shortage=shortage,
                           overstock_multiplier=multiplier, overstock_threshold=threshold,
                           suggested_reorder_raw=shortage, suggested_reorder=shortage)
    return {**{name: str(value) for name, value in quantity_values.items()}, 'product_id': product.id,
            'product_sku': product.sku, 'unit': product.unit, 'series_sku': mapping.series_sku, 'mapping_id': mapping.id,
            'source_namespace': mapping.source_namespace, 'forecast_id': forecast.id,
            'forecast_origin': forecast.forecast_origin.isoformat(), 'forecast_horizon': forecast.horizon,
            'model_id': forecast.model_id, 'model_version': forecast.model_version, 'artifact_version': forecast.artifact_version,
            'feature_version': forecast.feature_version,
            'lead_time_days': lead, 'decision_as_of': as_of.isoformat(), 'inventory_version': stock.version,
            'context': context, 'risk_status': state, 'assumptions_version': RULE_VERSION,
            'assumptions': ['All confirmed incoming stock assumed to arrive during lead time; no ETA is recorded.',
                'Allocated stock is excluded from usable inventory.', 'Forecast dates must cover every lead-time day.',
                'No pack-size or procurement rounding; raw shortage equals suggested quantity.',
                'Stored daily predictions use nine decimal places; original forecast-v1 values are preserved.',
                'Deterministic stock-risk rule, not a calibrated probability. Human review; no purchase execution.',
                'UK historical forecasts and present test stock form a research scenario, not measured 2011 inventory or Kenyan performance.' if context == 'research_demo' else 'Current operational inventory snapshot.']}


def generate_recommendation(db, identifier, payload, actor):
    product = locked_product(db, identifier)
    digest = fingerprint(identifier, payload)
    existing = retry(db, Recommendation, payload.request_key, actor, digest)
    if existing: return existing
    mapping = require_mapping(db, product)
    forecast = db.get(Forecast, str(payload.forecast_id))
    if forecast is None: raise HTTPException(404, 'Forecast not found')
    if payload.context == 'research_demo' and not payload.confirm_research_demo:
        raise HTTPException(422, 'Explicit research-demo acknowledgement required')
    _, registry = runtime.load()
    stock = db.scalar(select(Inventory).where(Inventory.product_id == identifier).with_for_update().execution_options(populate_existing=True))
    if stock is None: raise HTTPException(422, 'Inventory record missing')
    as_of = payload.decision_as_of or today()
    snapshot = calculate(product, stock, forecast, mapping, registry, as_of, payload.context)
    row = Recommendation(id=str(uuid4()), product_id=identifier, product_sku=product.sku, forecast_id=forecast.id,
                         context=payload.context, decision_as_of=as_of, inventory_version=stock.version,
                         risk_status=snapshot['risk_status'], assumptions_version=RULE_VERSION, snapshot=snapshot,
                         actor_id=actor.id, request_key=str(payload.request_key), request_fingerprint=digest)
    return commit_evidence(db, row, Recommendation, payload, actor, digest)

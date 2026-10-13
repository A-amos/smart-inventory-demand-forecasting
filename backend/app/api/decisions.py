from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user, manager_user
from app.database import get_db
from app.decision_schemas import ForecastGenerate, ForecastRead, MappingRead, MappingWrite, RecommendationGenerate, RecommendationRead
from app.models import Forecast, ForecastMapping, Product, Recommendation
from app.services import decisions, forecast_runtime
from app.services.catalog import product

router = APIRouter(prefix='/api/v1', tags=['Forecasts and decision support'], dependencies=[Depends(current_user)])


@router.get('/forecast-support')
def support():
    _, registry = forecast_runtime.load()
    return {'source_namespace': forecast_runtime.NAMESPACE, 'supported_series': registry['skus'],
            'available_origin': forecast_runtime.DEMO_ORIGIN, 'research_decision_as_of': forecast_runtime.DEMO_DAY,
            'maximum_horizon': 28, 'model_id': registry['model_id'], 'model_version': registry['model_version'],
            'artifact_version': 'sha256:' + registry['artifact_sha256'], 'selected': 'mean_28',
            'operational_forecasts_available': False,
            'limitation': 'UK historical research demonstration only. No current compatible history; not validated for Kenyan retail.'}


@router.get('/products/{identifier}/forecast-mappings', response_model=list[MappingRead])
def mappings(identifier: int, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    product(db, identifier, include_archived=True)
    return db.scalars(select(ForecastMapping).where(ForecastMapping.product_id == identifier)
                      .order_by(ForecastMapping.sequence.desc()).offset(offset).limit(limit)).all()


@router.post('/products/{identifier}/forecast-mappings', response_model=MappingRead, status_code=201)
def map_series(identifier: int, payload: MappingWrite, actor=Depends(manager_user), db: Session = Depends(get_db)):
    return decisions.append_mapping(db, identifier, payload, actor)


@router.get('/forecasts/{identifier}', response_model=list[ForecastRead])
def forecasts(identifier: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    product(db, identifier, include_archived=True)
    return db.scalars(select(Forecast).where(Forecast.product_id == identifier)
                      .order_by(Forecast.created_at.desc(), Forecast.id.desc()).offset(offset).limit(limit)).all()


@router.post('/forecasts/{identifier}/generate', response_model=ForecastRead, status_code=201)
def generate_forecast(identifier: int, payload: ForecastGenerate, actor=Depends(manager_user), db: Session = Depends(get_db)):
    return decisions.generate_forecast(db, identifier, payload, actor)


@router.get('/recommendations/{identifier}', response_model=list[RecommendationRead])
def recommendations(identifier: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    product(db, identifier, include_archived=True)
    return db.scalars(select(Recommendation).where(Recommendation.product_id == identifier)
                      .order_by(Recommendation.created_at.desc(), Recommendation.id.desc()).offset(offset).limit(limit)).all()


@router.post('/recommendations/{identifier}/generate', response_model=RecommendationRead, status_code=201)
def generate_recommendation(identifier: int, payload: RecommendationGenerate, actor=Depends(manager_user), db: Session = Depends(get_db)):
    return decisions.generate_recommendation(db, identifier, payload, actor)


@router.get('/research/models')
def research_models(): return forecast_runtime.comparison()


@router.get('/forecasts/{identifier}/{forecast_id}/history')
def forecast_history(identifier: int, forecast_id: str, db: Session = Depends(get_db)):
    product(db, identifier, include_archived=True)
    row = db.get(Forecast, forecast_id)
    if row is None or row.product_id != identifier: raise HTTPException(404, 'Forecast not found for this product')
    # This historical chart does not invent current operational demand.
    try:
        import pandas as pd
        from ml.data import load_daily
        from ml.common import sha256
        metadata = forecast_runtime.checked_json('preprocessing.json')
        if sha256(forecast_runtime.ROOT / 'data/processed/phase4/development.csv') != metadata['processed_files']['development.csv']:
            raise ValueError('Changed historical source')
        data = load_daily()
        history = data[data.sku.eq(row.series_sku) & data.date.le(pd.Timestamp(row.forecast_origin))].tail(56)
        return {'source_namespace': row.source_namespace, 'series_sku': row.series_sku,
                'points': [{'date': item.date.date().isoformat(), 'quantity': float(item.demand)} for item in history.itertuples()]}
    except (ValueError, OSError, ImportError, KeyError):
        raise HTTPException(503, 'Verified historical demand unavailable') from None


@router.get('/dashboard')
def dashboard(context: str = Query('operational', pattern='^(operational|research_demo)$'), db: Session = Depends(get_db)):
    products = db.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.name, Product.id)).all()
    # A single query, then per-product lookup; overview excludes stale stock/config snapshots.
    all_recs = db.scalars(select(Recommendation).where(Recommendation.context == context)
                         .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())).all()
    latest = {}
    for rec in all_recs: latest.setdefault(rec.product_id, rec)
    counts = {'ADEQUATE': 0, 'REPLENISH': 0, 'OVERSTOCK': 0, 'UNASSESSED': 0}
    rows = []
    for item in products:
        stock, rec = item.inventory, latest.get(item.id)
        mapping = decisions.latest_mapping(db, item.id)
        mapped = bool(mapping and mapping.enabled and mapping.product_sku == item.sku and mapping.unit == item.unit
                      and mapping.source_namespace == forecast_runtime.NAMESPACE)
        valid = bool(rec and mapped and rec.product_sku == item.sku
                     and mapping.id == rec.snapshot['mapping_id'] and mapping.unit == item.unit
                     and rec.inventory_version == stock.version and rec.snapshot['lead_time_days'] == item.lead_time_days
                     and Decimal(rec.snapshot['safety_stock']) == item.safety_stock
                     and Decimal(rec.snapshot['overstock_multiplier']) == item.overstock_multiplier
                     and rec.decision_as_of == (date.fromisoformat(forecast_runtime.DEMO_DAY) if context == 'research_demo' else decisions.today()))
        status = rec.risk_status if valid else 'UNASSESSED'
        counts[status] += 1
        rows.append({'product_id': item.id, 'sku': item.sku, 'name': item.name, 'unit': item.unit,
                     'on_hand': str(stock.on_hand), 'confirmed_in_transit': str(stock.confirmed_in_transit),
                     'allocated': str(stock.allocated), 'inventory_position': str(stock.on_hand + stock.confirmed_in_transit - stock.allocated),
                     'risk_status': status, 'recommendation_id': rec.id if valid else None,
                     'forecastability': 'Mapped UK research series' if mapped else 'Forecast unavailable — insufficient or unsupported historical series'})
    return {'context': context, 'decision_as_of': forecast_runtime.DEMO_DAY if context == 'research_demo' else decisions.today().isoformat(),
            'total_active_products': len(products), 'status_counts': counts, 'products': rows,
            'limitation': 'Historical UK forecast + current illustrative stock scenario; not Kenyan operational validation.' if context == 'research_demo'
             else 'Current inventory. Historical UK forecasts cannot establish present-day stock risk; unassessed is not safe.'}

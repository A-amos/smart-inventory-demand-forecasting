"""Read-only verification of the actual Phase 6 browser-created MySQL records."""
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal as D
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.database import SessionLocal
from app.models import Forecast, ForecastMapping, Inventory, Product, Recommendation, Sale, StockMovement


def main():
    checks=[]
    def check(name, valid, actual):
        checks.append({'check':name,'passed':bool(valid),'actual':actual})
        assert valid, name
    try:
        with SessionLocal() as db:
            product=db.scalar(select(Product).where(Product.sku=='P6-BROWSER-20261001'))
            check('Exact labelled browser demonstration product persisted',product is not None and product.active and product.name=='Phase 6 demonstration product',product.id if product else None)
            stock=db.get(Inventory,product.id)
            check('Current stock and version match browser after sale/import',stock.on_hand==17 and stock.confirmed_in_transit==3 and stock.allocated==2 and stock.version==3,{'on_hand':str(stock.on_hand),'incoming':str(stock.confirmed_in_transit),'allocated':str(stock.allocated),'version':stock.version})
            sales=db.scalars(select(Sale).where(Sale.product_id==product.id).order_by(Sale.id)).all()
            check('One operational and one historical sale persisted',len(sales)==2 and sales[0].id==100 and sales[0].source=='operational' and sales[0].quantity==3 and sales[0].unit_price==D('120.50') and sales[1].id==101 and sales[1].source=='historical' and sales[1].quantity==50,[{'id':s.id,'source':s.source,'quantity':str(s.quantity),'actor_id':s.actor_id,'sale_date':s.sale_date.isoformat()} for s in sales])
            movements=db.scalars(select(StockMovement).where(StockMovement.product_id==product.id).order_by(StockMovement.id)).all()
            check('Historical import generated no stock movement',len(movements)==3 and [m.kind for m in movements]==['opening','adjustment','sale'] and movements[-1].sale_id==100 and movements[-1].on_hand_before==20 and movements[-1].on_hand_after==17,[{'kind':m.kind,'sale_id':m.sale_id,'on_hand_after':str(m.on_hand_after)} for m in movements])
            mappings=db.scalars(select(ForecastMapping).where(ForecastMapping.product_id==product.id)).all()
            check('Explicit historical UK mapping persisted',len(mappings)==1 and mappings[0].series_sku=='20728' and mappings[0].reason.startswith('Synthetic Phase 6'),mappings[0].reason)
            forecasts=db.scalars(select(Forecast).where(Forecast.product_id==product.id)).all()
            check('Real historical frozen forecast and 28 points persisted',len(forecasts)==1 and forecasts[0].id=='4a1f9161-32f8-4559-b724-62f80907e944' and forecasts[0].context=='research_demo' and str(forecasts[0].forecast_origin)=='2011-11-10' and len(forecasts[0].points)==28,{'id':forecasts[0].id,'context':forecasts[0].context,'origin':str(forecasts[0].forecast_origin),'points':len(forecasts[0].points)})
            recs=db.scalars(select(Recommendation).where(Recommendation.product_id==product.id)).all()
            check('Explainable original recommendation persisted',len(recs)==1 and recs[0].id=='af82e6f7-3339-4455-bc8b-45d51b85c509' and recs[0].risk_status=='REPLENISH' and recs[0].inventory_version==3 and D(recs[0].snapshot['inventory_position'])==18 and D(recs[0].snapshot['suggested_reorder'])==D('69.571428571'),recs[0].snapshot)
        print(f'{len(checks)} read-only browser/MySQL persistence checks passed.')
    finally:
        (ROOT/'docs/test-results/phase6-browser-persistence.json').write_text(json.dumps({'executed_at_utc':datetime.now(UTC).isoformat(),'synthetic_stock':True,'checks':checks},indent=2),encoding='utf-8')


if __name__=='__main__':main()

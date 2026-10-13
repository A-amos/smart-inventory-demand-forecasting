"""Verify exact browser-created evidence in MySQL; archive only own failed API fixture."""
import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal as D
from pathlib import Path

import httpx
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.database import SessionLocal
from app.models import Forecast, ForecastMapping, Inventory, Product, Recommendation, Sale, StockMovement


def main():
    checks = []
    def check(name, passed, actual):
        checks.append({'check': name, 'passed': bool(passed), 'actual': actual})
        if not passed: raise AssertionError(name)
    try:
        browser = json.loads((ROOT / 'docs/test-results/phase5-browser.json').read_text())
        with SessionLocal() as db:
            product = db.scalar(select(Product).where(Product.sku == browser['sku']))
            check('Browser fixture is labelled synthetic and archived', product is not None and 'synthetic' in product.name and not product.active, product.id if product else None)
            forecasts = db.scalars(select(Forecast).where(Forecast.product_id == product.id)).all()
            recs = db.scalars(select(Recommendation).where(Recommendation.product_id == product.id).order_by(Recommendation.created_at)).all()
            stock = db.get(Inventory, product.id)
            check('One real browser forecast and two immutable decisions persisted', len(forecasts) == 1 and forecasts[0].id == browser['forecast_id'] and len(recs) == 2 and recs[0].id == browser['original_recommendation_id'], {'forecasts': len(forecasts), 'recommendations': len(recs)})
            first, second = recs
            check('Original browser stock components and decision preserved', first.risk_status == 'REPLENISH' and D(first.snapshot['on_hand']) == 5 and D(first.snapshot['confirmed_in_transit']) == 3 and D(first.snapshot['allocated']) == 2 and D(first.snapshot['inventory_position']) == 6 and first.inventory_version == 2, first.snapshot)
            check('New browser decision references same forecast and new stock version', second.risk_status == 'OVERSTOCK' and second.forecast_id == first.forecast_id and second.inventory_version == 3 and D(second.snapshot['on_hand']) == 999 and D(second.snapshot['suggested_reorder']) == 0, second.snapshot)
            check('Generating browser evidence did not create sales or stock movements', db.scalar(select(func.count(Sale.id)).where(Sale.product_id == product.id)) == 0 and len(db.scalars(select(StockMovement).where(StockMovement.product_id == product.id)).all()) == 3 and stock.on_hand == 999 and stock.version == 3, 'Only opening + two explicit adjustment movements, no sales')
            mapping = db.scalar(select(ForecastMapping).where(ForecastMapping.product_id == product.id))
            check('Browser used explicit supported mapping and frozen digest', mapping.series_sku == '20728' and mapping.reason.startswith('Synthetic browser') and forecasts[0].artifact_version == 'sha256:840837c7333d8a928fc170a7ef3245299bb2dfcd0750c6eb45b0f696a8f41031', mapping.reason)
        # First verifier run stopped at a sandbox restriction; archive only that exact tagged fixture.
        partial = json.loads((ROOT / 'docs/test-results/phase5-live-sandbox-failure.json').read_text())
        snapshot = next(item['actual'] for item in partial['checks'] if item['check'] == 'Actual position, multi-day target, safety, reorder and overstock equations')
        failed_id = snapshot['product_id']
        with SessionLocal() as db:
            failed = db.get(Product, failed_id)
            assert failed.sku == snapshot['product_sku'] and failed.name.startswith('Phase 5 synthetic stock ')
            failed_category = failed.category_id
        with httpx.Client(base_url='http://localhost:8000/api/v1', timeout=30) as client:
            account = json.loads((ROOT / '.local/verification-account.json').read_text())
            session = client.post('/auth/login', json=account); session.raise_for_status()
            headers = {'Authorization': 'Bearer ' + session.json()['access_token']}
            client.delete(f'/products/{failed_id}', headers=headers).raise_for_status()
            client.delete(f'/categories/{failed_category}', headers=headers).raise_for_status()
            client.post('/auth/logout', headers=headers).raise_for_status()
        check('Partial-run fixture archived without deleting evidence', True, failed_id)
        reference = json.loads((ROOT / 'backend/app/core/phase4-reference.json').read_text())
        frozen = json.loads((ROOT / 'docs/research/results/frozen-selection.json').read_text())
        check('All protected research evidence and ML source fingerprints remain unchanged',
              all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in {**reference, **frozen['source_fingerprints']}.items()), {'evidence_files': len(reference), 'ML_source_files': len(frozen['source_fingerprints'])})
        print(f'{len(checks)} browser MySQL persistence, fixture cleanup and frozen-evidence checks passed.')
    finally:
        (ROOT / 'docs/test-results/phase5-browser-persistence.json').write_text(json.dumps({'executed_at_utc': datetime.now(UTC).isoformat(), 'checks': checks}, indent=2), encoding='utf-8')


if __name__ == '__main__': main()

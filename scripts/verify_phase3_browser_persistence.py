"""Verify the actual browser-created fixture remains persisted in real MySQL."""
import csv
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from sqlalchemy import select

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.database import SessionLocal
from app.models import Inventory, Product, Sale, StockMovement


def main():
    with (root / 'docs/test-results/phase3-browser-upload.csv').open(newline='') as file:
        sku = next(csv.DictReader(file))['sku']
    with SessionLocal() as db:
        product = db.scalar(select(Product).where(Product.sku == sku))
        assert product is not None and not product.active
        stock = db.get(Inventory, product.id)
        sales = db.scalars(select(Sale).where(Sale.product_id == product.id)).all()
        movements = db.scalars(select(StockMovement).where(StockMovement.product_id == product.id)).all()
        assert stock.on_hand == Decimal('17') and stock.version == 2
        assert len(sales) == 2 and {row.source for row in sales} == {'operational', 'historical'}
        assert [row.quantity for row in sales if row.source == 'operational'] == [Decimal('3')]
        assert [row.quantity for row in sales if row.source == 'historical'] == [Decimal('50')]
        assert len(movements) == 2 and {row.kind for row in movements} == {'opening', 'sale'}
        assert all(row.actor_id for row in sales)
        result = {'executed_at_utc': datetime.now(UTC).isoformat(), 'passed': True, 'sku': sku,
                  'archived': True, 'on_hand': str(stock.on_hand), 'version': stock.version,
                  'sales': [{'id': row.id, 'source': row.source, 'quantity': str(row.quantity)} for row in sales],
                  'movement_kinds': [row.kind for row in movements]}
    (root / 'docs/test-results/phase3-browser-persistence.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Actual browser fixture verified in MySQL: 17 kg, version 2, two sales, opening/sale movements only; archived with history retained')


if __name__ == '__main__':
    main()

"""Transactional sales and bounded, independently confirmed historical imports."""
import csv
import hashlib
import io
import json
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
from time import sleep

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models import Inventory, Product, Sale, SalesImport, StockMovement, utc_now
from app.sales_schemas import SaleValues

MAX_FILE_BYTES = 1024 * 1024
MAX_ROWS = 5000
REQUIRED_COLUMNS = {'sku', 'sale_date', 'quantity'}
OPTIONAL_COLUMNS = {'unit_price', 'external_id'}


def same_sale(row, payload, actor):
    return (row.actor_id == actor.id and row.product_id == payload.product_id
            and row.sale_date == payload.sale_date.replace(tzinfo=None)
            and row.quantity == payload.quantity and row.unit_price == payload.unit_price)


def record_sale(db, payload, actor):
    """Retry only a MySQL deadlock victim after the entire transaction rolled back.

    Missing unique request keys can acquire overlapping gap locks even for
    different products. Each retry rechecks stock/version and uses the same
    request key, preserving idempotency and preventing a partial/double sale.
    """
    for attempt in range(3):
        try:
            return _record_sale_once(db, payload, actor)
        except OperationalError as error:
            code = getattr(error.orig, 'args', (None,))[0]
            if code != 1213 or attempt == 2:
                raise
            sleep(0.01 * (attempt + 1))


def _record_sale_once(db, payload, actor):
    """The caller's session also serves authentication; commit only after all writes."""
    try:
        # Match catalog lock order. Fresh locked reads avoid MySQL repeatable-read snapshots.
        product = db.scalar(select(Product).where(Product.id == payload.product_id)
                            .with_for_update().execution_options(populate_existing=True))
        if not product or not product.active:
            raise HTTPException(404, 'Active product not found')
        replay = db.scalar(select(Sale).where(Sale.request_key == str(payload.request_key)).with_for_update())
        if replay:
            if not same_sale(replay, payload, actor):
                raise HTTPException(409, 'Request key already used for a different sale')
            db.rollback()  # release read locks; replay never changes stock
            return replay, True
        stock = db.scalar(select(Inventory).where(Inventory.product_id == product.id)
                          .with_for_update().execution_options(populate_existing=True))
        if not stock:
            raise HTTPException(409, 'Inventory record missing')
        if stock.version != payload.inventory_version:
            raise HTTPException(409, 'Stock changed. Reload inventory before recording this sale.')
        if payload.quantity > stock.on_hand - stock.allocated:
            raise HTTPException(409, 'Insufficient unallocated on-hand stock')
        sale = Sale(product_id=product.id, sku_snapshot=product.sku, actor_id=actor.id,
                    quantity=payload.quantity, unit_price=payload.unit_price,
                    sale_date=payload.sale_date.replace(tzinfo=None), source='operational',
                    request_key=str(payload.request_key))
        db.add(sale)
        db.flush()
        db.add(StockMovement(product_id=product.id, actor_id=actor.id, sale_id=sale.id,
                            kind='sale', reason=f'Operational sale #{sale.id}',
                            on_hand_before=stock.on_hand, on_hand_after=stock.on_hand - payload.quantity,
                            in_transit_before=stock.confirmed_in_transit, in_transit_after=stock.confirmed_in_transit,
                            allocated_before=stock.allocated, allocated_after=stock.allocated))
        stock.on_hand -= payload.quantity
        stock.version += 1
        db.commit()
        return sale, False
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Conflicting sale or audit record. Reload before retrying.') from None
    except Exception:
        db.rollback()
        raise


def identity(product_id, values, external_id):
    # Distinct identical transactions need distinct external_id values.
    content = [product_id, values.sale_date.isoformat(), str(values.quantity.normalize()),
               str(values.unit_price.normalize()) if values.unit_price is not None else None]
    parts = ['external', product_id, external_id] if external_id else ['content', *content]
    return hashlib.sha256(json.dumps(parts, separators=(',', ':')).encode()).hexdigest()


def batch_view(batch):
    return {'id': batch.id, 'filename': batch.filename, 'status': batch.status,
            'preview_version': batch.version, 'valid_count': len(batch.accepted_rows),
            'rejected_count': len(batch.rejected_rows), 'accepted_preview': batch.accepted_rows[:100],
            'preview_truncated': len(batch.accepted_rows) > 100,
            'rejected_rows': batch.rejected_rows,
            'imported_count': len(batch.accepted_rows) if batch.status == 'committed' else 0}


def preview_import(db, content, filename, actor):
    if not content or len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, 'CSV must contain 1 byte to 1 MiB')
    digest = hashlib.sha256(content).hexdigest()
    batch = db.scalar(select(SalesImport).where(SalesImport.file_hash == digest).with_for_update())
    if batch and batch.status == 'committed':
        return batch_view(batch)
    try:
        decoded = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded, newline=''), strict=True)
        fields = reader.fieldnames or []
        if (len(fields) != len(set(fields)) or not REQUIRED_COLUMNS <= set(fields)
                or set(fields) - REQUIRED_COLUMNS - OPTIONAL_COLUMNS):
            raise HTTPException(422, 'Required columns: sku,sale_date,quantity. Optional: unit_price,external_id. Headers must be unique; no extra columns.')
        raw_rows = []
        for row in reader:
            if len(raw_rows) >= MAX_ROWS:
                raise HTTPException(413, 'CSV exceeds 5000 data rows')
            raw_rows.append(row)
    except (UnicodeDecodeError, csv.Error):
        raise HTTPException(422, 'Upload a valid UTF-8 CSV with correctly quoted fields') from None
    if not raw_rows:
        raise HTTPException(422, 'CSV contains no data rows')
    products = {p.sku: p for p in db.scalars(select(Product)).all()}
    valid, rejected, seen = [], [], set()
    # One indexed lookup per valid row keeps memory bounded by the upload limit.
    for line, raw in enumerate(raw_rows, 2):
        try:
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError('Column count does not match the header')
            sku = raw['sku'].strip().upper()
            product = products.get(sku)
            if not product or not product.active:
                raise ValueError('Unknown or archived product SKU')
            values = SaleValues.model_validate({'sale_date': raw['sale_date'], 'quantity': raw['quantity'],
                                              'unit_price': raw.get('unit_price', '').strip() or None})
            external_id = raw.get('external_id', '').strip() or None
            if external_id and len(external_id) > 120:
                raise ValueError('external_id exceeds 120 characters')
            key = identity(product.id, values, external_id)
            if key in seen:
                raise ValueError('Duplicate identity within this file')
            seen.add(key)
            if db.scalar(select(Sale.id).where(Sale.import_identity == key)):
                raise ValueError('Already imported identity (including conflicting reuse of external_id)')
            valid.append({'row_number': line, 'product_id': product.id, 'sku': sku,
                          **values.model_dump(mode='json'), 'external_id': external_id, 'identity': key})
        except (ValueError, ValidationError) as exc:
            reason = '; '.join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors()) if isinstance(exc, ValidationError) else str(exc)
            rejected.append({'row_number': line, 'values': raw, 'reason': reason})
    if batch is None:
        batch = SalesImport(id=str(uuid4()), file_hash=digest, filename=filename.replace('\\', '/').split('/')[-1][:120],
                            actor_id=actor.id, accepted_rows=valid, rejected_rows=rejected)
        db.add(batch)
    else:
        batch.accepted_rows, batch.rejected_rows = valid, rejected
        batch.created_at, batch.actor_id = utc_now(), actor.id
        batch.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'File is being previewed concurrently. Retry preview.') from None
    return batch_view(batch)


def confirm_import(db, identifier, payload, actor):
    try:
        batch = db.scalar(select(SalesImport).where(SalesImport.id == identifier)
                          .with_for_update().execution_options(populate_existing=True))
        if not batch:
            raise HTTPException(404, 'Import preview not found')
        if batch.status == 'committed':
            result = batch_view(batch)
            db.rollback()
            return result
        if batch.actor_id != actor.id:
            raise HTTPException(403, 'Preview this file with your account before confirming')
        if batch.version != payload.preview_version:
            raise HTTPException(409, 'Preview changed. Preview the file again.')
        if batch.created_at < utc_now() - timedelta(minutes=30):
            raise HTTPException(409, 'Preview expired after 30 minutes. Preview the file again.')
        if not payload.accept_valid_rows or not batch.accepted_rows:
            raise HTTPException(422, 'Explicitly accept the valid rows; at least one valid row is required')
        ids = sorted({row['product_id'] for row in batch.accepted_rows})
        # Lock products in stable order, sharing catalog/archive locking. Never lock/write inventory.
        products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.id)
                    .with_for_update().execution_options(populate_existing=True)).all()}
        for row in batch.accepted_rows:
            product = products.get(row['product_id'])
            if not product or not product.active or product.sku != row['sku']:
                raise HTTPException(409, 'Product changed or archived after preview. Preview the file again.')
            values = SaleValues.model_validate({key: row[key] for key in ('sale_date', 'quantity', 'unit_price')})
            db.add(Sale(product_id=product.id, sku_snapshot=row['sku'], actor_id=actor.id,
                        sale_date=values.sale_date.replace(tzinfo=None), quantity=values.quantity,
                        unit_price=values.unit_price, source='historical', import_batch_id=batch.id,
                        import_identity=row['identity'], external_id=row['external_id']))
        batch.status, batch.committed_at = 'committed', utc_now()
        db.commit()
        return batch_view(batch)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'An identity was imported concurrently. Preview again; no rows from this confirmation were saved.') from None
    except Exception:
        db.rollback()
        raise

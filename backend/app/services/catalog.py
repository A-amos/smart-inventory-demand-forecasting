from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Category, Inventory, Product, StockMovement


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Duplicate identifier or conflicting record') from None


def category(db, identifier, *, include_archived=False):
    row = db.get(Category, identifier)
    if not row or (not row.active and not include_archived):
        raise HTTPException(404, 'Category not found')
    return row


def product(db, identifier, *, include_archived=False):
    row = db.get(Product, identifier)
    if not row or (not row.active and not include_archived):
        raise HTTPException(404, 'Product not found')
    return row


def write_category(db, payload, identifier=None):
    row = category(db, identifier, include_archived=True) if identifier else Category()
    duplicate = db.scalar(select(Category).where(func.lower(Category.name) == payload.name.lower(), Category.id != (identifier or 0)))
    if duplicate:
        raise HTTPException(409, 'Category name already exists, including archived categories')
    if not payload.active and identifier:
        guard_category_archive(db, identifier)
    row.name, row.active = payload.name, payload.active
    db.add(row)
    commit(db)
    return row


def guard_category_archive(db, identifier):
    # Category row lock serializes category archive against product creation/update.
    db.scalar(select(Category).where(Category.id == identifier).with_for_update())
    if db.scalar(select(Product.id).where(Product.category_id == identifier, Product.active.is_(True)).limit(1).with_for_update()):
        raise HTTPException(409, 'Archive or move active products before archiving their category')


def write_product(db, payload, actor, identifier=None):
    selected_category = db.scalar(select(Category).where(Category.id == payload.category_id).with_for_update())
    if not selected_category or (payload.active and not selected_category.active):
        raise HTTPException(422, 'An active category is required')
    if db.scalar(select(Product.id).where(Product.sku == payload.sku, Product.id != (identifier or 0))):
        raise HTTPException(409, 'SKU already exists, including archived products')
    row = product(db, identifier, include_archived=True) if identifier else Product()
    for key, value in payload.model_dump(exclude={'initial_stock'}).items():
        setattr(row, key, value)
    db.add(row)
    try:
        db.flush()
        if identifier is None:
            row.inventory = Inventory(on_hand=payload.initial_stock, confirmed_in_transit=0, allocated=0)
            db.add(StockMovement(product_id=row.id, actor_id=actor.id, kind='opening', reason='Opening stock on product creation',
                                 on_hand_before=0, on_hand_after=payload.initial_stock, in_transit_before=0,
                                 in_transit_after=0, allocated_before=0, allocated_after=0))
        commit(db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Duplicate identifier or conflicting record') from None
    db.refresh(row)
    return row


def adjust_inventory(db, identifier, payload, actor):
    row_product = db.scalar(select(Product).where(Product.id == identifier).with_for_update())
    if not row_product or not row_product.active:
        raise HTTPException(404, 'Product not found')
    # Product's eager-loaded inventory may originate from an earlier transaction
    # snapshot. Refresh the identity-map instance from this current locked read.
    stock = db.scalar(select(Inventory).where(Inventory.product_id == identifier).with_for_update().execution_options(populate_existing=True))
    if stock.version != payload.version:
        raise HTTPException(409, 'Stock changed since you opened this form. Reload before saving.')
    db.add(StockMovement(product_id=identifier, actor_id=actor.id, kind='adjustment', reason=payload.reason,
                         on_hand_before=stock.on_hand, on_hand_after=payload.on_hand,
                         in_transit_before=stock.confirmed_in_transit, in_transit_after=payload.confirmed_in_transit,
                         allocated_before=stock.allocated, allocated_after=payload.allocated))
    stock.on_hand, stock.confirmed_in_transit, stock.allocated = payload.on_hand, payload.confirmed_in_transit, payload.allocated
    stock.version += 1
    commit(db)
    return stock

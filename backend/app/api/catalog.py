from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user, manager_user
from app.catalog_schemas import CategoryRead, CategoryWrite, InventoryRead, InventoryWrite, MovementRead, ProductCreate, ProductRead, ProductWrite
from app.database import get_db
from app.models import Category, Product, StockMovement
from app.services import catalog

router = APIRouter(prefix='/api/v1', tags=['Catalog and inventory'], dependencies=[Depends(current_user)])


@router.get('/categories', response_model=list[CategoryRead])
def categories(include_archived: bool = False, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    query = select(Category).order_by(Category.name, Category.id).offset(offset).limit(limit)
    if not include_archived:
        query = query.where(Category.active.is_(True))
    return db.scalars(query).all()


@router.post('/categories', response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryWrite, user=Depends(manager_user), db: Session = Depends(get_db)):
    return catalog.write_category(db, payload)


@router.get('/categories/{identifier}', response_model=CategoryRead)
def get_category(identifier: int, db: Session = Depends(get_db)):
    return catalog.category(db, identifier)


@router.put('/categories/{identifier}', response_model=CategoryRead)
def update_category(identifier: int, payload: CategoryWrite, user=Depends(manager_user), db: Session = Depends(get_db)):
    return catalog.write_category(db, payload, identifier)


@router.delete('/categories/{identifier}', status_code=204)
def archive_category(identifier: int, user=Depends(manager_user), db: Session = Depends(get_db)):
    row = catalog.category(db, identifier)
    catalog.guard_category_archive(db, identifier)
    row.active = False
    catalog.commit(db)


@router.get('/products', response_model=list[ProductRead])
def products(include_archived: bool = False, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    query = select(Product).order_by(Product.name, Product.id).offset(offset).limit(limit)
    if not include_archived:
        query = query.where(Product.active.is_(True))
    return db.scalars(query).all()


@router.post('/products', response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, user=Depends(manager_user), db: Session = Depends(get_db)):
    return catalog.write_product(db, payload, user)


@router.get('/products/{identifier}', response_model=ProductRead)
def get_product(identifier: int, db: Session = Depends(get_db)):
    return catalog.product(db, identifier)


@router.put('/products/{identifier}', response_model=ProductRead)
def update_product(identifier: int, payload: ProductWrite, user=Depends(manager_user), db: Session = Depends(get_db)):
    return catalog.write_product(db, payload, user, identifier)


@router.delete('/products/{identifier}', status_code=204)
def archive_product(identifier: int, user=Depends(manager_user), db: Session = Depends(get_db)):
    row = db.scalar(select(Product).where(Product.id == identifier).with_for_update())
    if not row or not row.active:
        raise HTTPException(404, 'Product not found')
    row.active = False
    catalog.commit(db)


@router.get('/products/{identifier}/inventory', response_model=InventoryRead)
def inventory(identifier: int, db: Session = Depends(get_db)):
    return catalog.product(db, identifier).inventory


@router.put('/products/{identifier}/inventory', response_model=InventoryRead)
def update_inventory(identifier: int, payload: InventoryWrite, user=Depends(manager_user), db: Session = Depends(get_db)):
    return catalog.adjust_inventory(db, identifier, payload, user)


@router.get('/products/{identifier}/movements', response_model=list[MovementRead])
def movements(identifier: int, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    catalog.product(db, identifier, include_archived=True)
    return db.scalars(select(StockMovement).where(StockMovement.product_id == identifier)
                      .order_by(StockMovement.id.desc()).offset(offset).limit(limit)).all()

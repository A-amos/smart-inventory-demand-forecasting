from pydantic import AwareDatetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.auth import current_user, manager_user
from app.database import get_db
from app.models import Sale
from app.sales_schemas import ImportConfirm, SaleCreate, SaleRead, SalesPage
from app.services import sales

router = APIRouter(prefix='/api/v1/sales', tags=['Sales'])


@router.post('', response_model=SaleRead, status_code=201)
def create_sale(payload: SaleCreate, response: Response, user=Depends(manager_user), db: Session = Depends(get_db)):
    row, replay = sales.record_sale(db, payload, user)
    if replay:
        response.status_code = 200
    return row


@router.get('', response_model=SalesPage)
def history(product_id: int | None = Query(None, gt=0), actor_id: int | None = Query(None, gt=0),
            date_from: AwareDatetime | None = None, date_to: AwareDatetime | None = None,
            source: str | None = Query(None, pattern='^(operational|historical)$'),
            offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
            user=Depends(current_user), db: Session = Depends(get_db)):
    from datetime import UTC
    start = date_from.astimezone(UTC).replace(tzinfo=None) if date_from else None
    end = date_to.astimezone(UTC).replace(tzinfo=None) if date_to else None
    if start and end and start > end:
        raise HTTPException(422, 'Start date must be before the end date')
    conditions = []
    if product_id: conditions.append(Sale.product_id == product_id)
    if actor_id: conditions.append(Sale.actor_id == actor_id)
    if source: conditions.append(Sale.source == source)
    if start: conditions.append(Sale.sale_date >= start)
    if end: conditions.append(Sale.sale_date <= end)
    return {'items': db.scalars(select(Sale).where(*conditions).order_by(Sale.sale_date.desc(), Sale.id.desc())
                               .offset(offset).limit(limit)).all(),
            'total': db.scalar(select(func.count(Sale.id)).where(*conditions)), 'offset': offset, 'limit': limit}


@router.post('/imports/preview')
async def preview(request: Request, filename: str = Query('sales.csv', min_length=1, max_length=120),
                  user=Depends(manager_user), db: Session = Depends(get_db)):
    """Upload the raw CSV body (text/csv); enforce the limit while streaming."""
    if request.headers.get('content-type', '').split(';')[0].lower() != 'text/csv':
        raise HTTPException(415, 'Send the CSV body with Content-Type: text/csv')
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > sales.MAX_FILE_BYTES:
            raise HTTPException(413, 'CSV exceeds 1 MiB')
        content.extend(chunk)
    return await run_in_threadpool(sales.preview_import, db, bytes(content), filename, user)


@router.post('/imports/{identifier}/confirm')
def confirm(identifier: str, payload: ImportConfirm, user=Depends(manager_user), db: Session = Depends(get_db)):
    return sales.confirm_import(db, identifier, payload, user)

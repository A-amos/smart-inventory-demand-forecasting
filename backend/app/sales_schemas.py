from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_serializer, field_validator

SaleQuantity = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3, allow_inf_nan=False)]
Price = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2, allow_inf_nan=False)]


class SaleValues(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    sale_date: AwareDatetime
    quantity: SaleQuantity
    unit_price: Price | None = None

    @field_validator('sale_date', mode='before')
    @classmethod
    def iso_date(cls, value):
        if not isinstance(value, (str, datetime)):
            raise ValueError('Sale date must be an ISO 8601 timestamp')
        if isinstance(value, str) and ('T' not in value or len(value) < 20):
            raise ValueError('Use an ISO 8601 date/time with a timezone, e.g. 2026-09-01T10:00:00+03:00')
        return value

    @field_validator('sale_date')
    @classmethod
    def past_date(cls, value):
        if value.year < 1000:
            raise ValueError('Sale date is outside the MySQL DATETIME range (year 1000 or later)')
        if value > datetime.now(UTC):
            raise ValueError('Sale date cannot be in the future')
        return value.astimezone(UTC)


class SaleCreate(SaleValues):
    product_id: int = Field(gt=0, strict=True)
    inventory_version: int = Field(ge=1, strict=True)
    request_key: UUID


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    sku_snapshot: str | None
    quantity: Decimal
    unit_price: Decimal | None
    sale_date: datetime
    source: Literal['operational', 'historical']
    actor_id: int | None
    import_batch_id: str | None
    created_at: datetime

    @field_serializer('sale_date', 'created_at')
    def utc_string(self, value):
        return value.replace(tzinfo=UTC).isoformat().replace('+00:00', 'Z')


class SalesPage(BaseModel):
    items: list[SaleRead]
    total: int
    offset: int
    limit: int


class ImportConfirm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    preview_version: int = Field(ge=1, strict=True)
    accept_valid_rows: bool = Field(strict=True)

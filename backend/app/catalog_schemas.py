from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Quantity = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3, allow_inf_nan=False)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class CategoryWrite(Input):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True


class CategoryRead(CategoryWrite):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductWrite(Input):
    sku: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
    name: str = Field(min_length=1, max_length=160)
    category_id: int = Field(gt=0)
    unit: str = Field(default='unit', min_length=1, max_length=30)
    lead_time_days: int = Field(default=7, ge=1, le=365, strict=True)
    safety_stock: Quantity = Decimal('0')
    overstock_multiplier: Decimal = Field(default=Decimal('2'), gt=1, le=100, max_digits=8, decimal_places=3, allow_inf_nan=False)
    active: bool = True

    @field_validator('sku')
    @classmethod
    def normalize_sku(cls, value):
        return value.upper()


class ProductCreate(ProductWrite):
    initial_stock: Quantity = Decimal('0')


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    on_hand: Decimal
    confirmed_in_transit: Decimal
    allocated: Decimal
    version: int
    updated_at: datetime


class ProductRead(ProductWrite):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory: InventoryRead


class InventoryWrite(Input):
    on_hand: Quantity
    confirmed_in_transit: Quantity
    allocated: Quantity
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=3, max_length=240)

    @model_validator(mode='after')
    def allocations_available(self):
        if self.allocated > self.on_hand:
            raise ValueError('Allocated stock cannot exceed on-hand stock')
        return self


class MovementRead(BaseModel):
    sale_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    actor_id: int
    kind: str
    reason: str
    on_hand_before: Decimal
    on_hand_after: Decimal
    in_transit_before: Decimal
    in_transit_after: Decimal
    allocated_before: Decimal
    allocated_after: Decimal
    created_at: datetime

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.catalog_schemas import Input


class MappingWrite(Input):
    series_sku: str = Field(min_length=1, max_length=64)
    enabled: bool = True
    confirm_research_demo: Literal[True]
    reason: str = Field(min_length=3, max_length=240)

    @field_validator('series_sku')
    @classmethod
    def normalize(cls, value): return value.upper()


class MappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: int
    product_sku: str
    unit: str
    series_sku: str
    source_namespace: str
    enabled: bool
    sequence: int
    reason: str
    actor_id: int
    created_at: datetime


class ForecastGenerate(Input):
    request_key: UUID
    forecast_origin: date
    horizon: int = Field(default=28, ge=1, le=28, strict=True)
    context: Literal['operational', 'research_demo'] = 'operational'
    confirm_research_demo: bool = False


class RecommendationGenerate(Input):
    request_key: UUID
    forecast_id: UUID
    context: Literal['operational', 'research_demo'] = 'operational'
    decision_as_of: date | None = None
    confirm_research_demo: bool = False


class PointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    forecast_id: str
    forecast_date: date
    horizon_day: int = Field(ge=1, le=28)
    predicted_quantity: Decimal = Field(ge=0, allow_inf_nan=False)


class ForecastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: int
    product_sku: str
    unit: str
    mapping_id: str
    series_sku: str
    source_namespace: str
    context: Literal['operational', 'research_demo']
    forecast_origin: date
    horizon: int
    model_id: str
    model_version: str
    artifact_version: str
    feature_version: str
    actor_id: int
    created_at: datetime
    contract: dict
    points: list[PointRead]


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: int
    product_sku: str
    forecast_id: str
    context: Literal['operational', 'research_demo']
    decision_as_of: date
    inventory_version: int
    risk_status: Literal['ADEQUATE', 'REPLENISH', 'OVERSTOCK']
    assumptions_version: str
    snapshot: dict
    actor_id: int
    created_at: datetime

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, event
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now():
    # All database timestamps are naive UTC; presentation converts to local time.
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="manager")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_logins: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (CheckConstraint("role IN ('manager', 'researcher')", name="ck_user_role"),)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1')


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    unit: Mapped[str] = mapped_column(String(30), default="unit")
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    overstock_multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=2)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1')
    inventory: Mapped['Inventory'] = relationship(uselist=False, lazy='selectin')
    __table_args__ = (
        CheckConstraint("lead_time_days > 0", name="ck_product_lead_time"),
        CheckConstraint("safety_stock >= 0", name="ck_product_safety"),
        CheckConstraint("overstock_multiplier > 1", name="ck_product_overstock"),
    )


class Inventory(Base):
    __tablename__ = "inventory"
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    confirmed_in_transit: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    allocated: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    __table_args__ = (
        CheckConstraint("on_hand >= 0", name="ck_inventory_on_hand"),
        CheckConstraint("version > 0", name="ck_inventory_version"),
        CheckConstraint("confirmed_in_transit >= 0", name="ck_inventory_transit"),
        CheckConstraint("allocated >= 0 AND allocated <= on_hand", name="ck_inventory_allocated"),
    )


class StockMovement(Base):
    __tablename__ = 'stock_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    sale_id: Mapped[int | None] = mapped_column(ForeignKey('sales.id'), unique=True)
    kind: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(String(240))
    on_hand_before: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    on_hand_after: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    in_transit_before: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    in_transit_after: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    allocated_before: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    allocated_after: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    __table_args__ = (
        CheckConstraint("kind IN ('opening', 'adjustment', 'sale')", name='ck_movement_kind'),
        CheckConstraint('on_hand_before >= 0 AND on_hand_after >= 0 AND in_transit_before >= 0 AND in_transit_after >= 0 AND allocated_before >= 0 AND allocated_after >= 0 AND allocated_before <= on_hand_before AND allocated_after <= on_hand_after', name='ck_movement_quantities'),
    )


class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="operational")
    # Nullable actor/snapshot columns preserve pre-Phase-3 records without inventing authors.
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), index=True)
    sku_snapshot: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, server_default='1970-01-01 00:00:00')
    request_key: Mapped[str | None] = mapped_column(String(36), unique=True)
    import_batch_id: Mapped[str | None] = mapped_column(ForeignKey('sales_imports.id'), index=True)
    import_identity: Mapped[str | None] = mapped_column(String(64), unique=True)
    external_id: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_sale_price"),
        CheckConstraint("source IN ('operational', 'historical')", name="ck_sale_source"),
    )


class SalesImport(Base):
    __tablename__ = 'sales_imports'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    filename: Mapped[str] = mapped_column(String(120))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(20), default='preview')
    version: Mapped[int] = mapped_column(Integer, default=1)
    accepted_rows: Mapped[list] = mapped_column(JSON)
    rejected_rows: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime)
    __table_args__ = (CheckConstraint("status IN ('preview', 'committed')", name='ck_import_status'),
                      CheckConstraint('version > 0', name='ck_import_version'))


class ForecastMapping(Base):
    __tablename__ = 'forecast_mappings'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    product_sku: Mapped[str] = mapped_column(String(64))
    unit: Mapped[str] = mapped_column(String(30))
    series_sku: Mapped[str] = mapped_column(String(64))
    source_namespace: Mapped[str] = mapped_column(String(40))
    enabled: Mapped[bool] = mapped_column(Boolean)
    sequence: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(240))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime().with_variant(DATETIME(fsp=6), 'mysql'), default=utc_now, index=True)
    __table_args__ = (UniqueConstraint('product_id', 'sequence', name='uq_mapping_sequence'),
                     CheckConstraint('sequence > 0', name='ck_mapping_sequence'))


class Forecast(Base):
    __tablename__ = 'forecasts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    product_sku: Mapped[str] = mapped_column(String(64))
    unit: Mapped[str] = mapped_column(String(30))
    mapping_id: Mapped[str] = mapped_column(ForeignKey('forecast_mappings.id'))
    series_sku: Mapped[str] = mapped_column(String(64))
    source_namespace: Mapped[str] = mapped_column(String(40))
    context: Mapped[str] = mapped_column(String(20))
    forecast_origin: Mapped[date] = mapped_column(Date)
    horizon: Mapped[int] = mapped_column(Integer)
    model_id: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(40))
    artifact_version: Mapped[str] = mapped_column(String(80))
    feature_version: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    request_key: Mapped[str] = mapped_column(String(36), unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    contract: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime().with_variant(DATETIME(fsp=6), 'mysql'), default=utc_now, index=True)
    points: Mapped[list['ForecastPointRecord']] = relationship(lazy='selectin', order_by='ForecastPointRecord.horizon_day', passive_deletes='all')
    __table_args__ = (CheckConstraint('horizon BETWEEN 1 AND 28', name='ck_forecast_horizon'),
                     CheckConstraint("context IN ('operational', 'research_demo')", name='ck_forecast_context'))


class ForecastPointRecord(Base):
    __tablename__ = 'forecast_points'
    forecast_id: Mapped[str] = mapped_column(ForeignKey('forecasts.id'), primary_key=True)
    horizon_day: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_date: Mapped[date] = mapped_column(Date)
    predicted_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 9))
    __table_args__ = (CheckConstraint('horizon_day BETWEEN 1 AND 28', name='ck_forecast_point_horizon'),
                     CheckConstraint('predicted_quantity >= 0', name='ck_forecast_point_quantity'))


class Recommendation(Base):
    __tablename__ = 'recommendations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    forecast_id: Mapped[str] = mapped_column(ForeignKey('forecasts.id'), index=True)
    product_sku: Mapped[str] = mapped_column(String(64))
    context: Mapped[str] = mapped_column(String(20))
    decision_as_of: Mapped[date] = mapped_column(Date)
    inventory_version: Mapped[int] = mapped_column(Integer)
    risk_status: Mapped[str] = mapped_column(String(20))
    assumptions_version: Mapped[str] = mapped_column(String(40))
    snapshot: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    request_key: Mapped[str] = mapped_column(String(36), unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime().with_variant(DATETIME(fsp=6), 'mysql'), default=utc_now, index=True)
    __table_args__ = (CheckConstraint("risk_status IN ('ADEQUATE', 'REPLENISH', 'OVERSTOCK')", name='ck_recommendation_risk'),
                     CheckConstraint('inventory_version > 0', name='ck_recommendation_inventory_version'),
                     CheckConstraint("context IN ('operational', 'research_demo')", name='ck_recommendation_context'))


def immutable_evidence(mapper, connection, target):
    raise ValueError('Forecast mappings, forecasts and recommendations are append-only evidence')


for evidence_model in [ForecastMapping, Forecast, ForecastPointRecord, Recommendation]:
    event.listen(evidence_model, 'before_update', immutable_evidence)
    event.listen(evidence_model, 'before_delete', immutable_evidence)

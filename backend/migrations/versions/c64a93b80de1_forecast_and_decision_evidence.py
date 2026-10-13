"""Append-only mapped forecasts and decision snapshots.

Revision ID: c64a93b80de1
Revises: 7cf0674f24d9
"""
from alembic import op
from app.models import ForecastMapping, Forecast, ForecastPointRecord, Recommendation
from sqlalchemy import text

revision = 'c64a93b80de1'
down_revision = '7cf0674f24d9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for model in [ForecastMapping, Forecast, ForecastPointRecord, Recommendation]:
        # MySQL DDL commits implicitly; resume after a trigger/privilege startup failure.
        model.__table__.create(bind, checkfirst=True)
        table = model.__tablename__
        for operation in ['UPDATE', 'DELETE']:
            name = f'protect_{table}_{operation.lower()}'
            if bind.dialect.name == 'mysql':
                exists = bind.scalar(text('SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND TRIGGER_NAME=:name'), {'name': name})
                if not exists:
                    op.execute(text(f"CREATE TRIGGER {name} BEFORE {operation} ON {table} FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Append-only decision evidence'"))
            elif bind.dialect.name == 'sqlite':
                op.execute(text(f"CREATE TRIGGER IF NOT EXISTS {name} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'Append-only decision evidence'); END"))


def downgrade():
    raise RuntimeError('Decision evidence is append-only. Destructive downgrade requires an explicitly reviewed recovery plan.')

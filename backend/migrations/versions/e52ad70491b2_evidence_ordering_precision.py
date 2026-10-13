"""Preserve subsecond evidence ordering on MySQL; support the first Phase 5 build.

Revision ID: e52ad70491b2
Revises: c64a93b80de1
"""
from alembic import op
from sqlalchemy import DateTime, inspect
from sqlalchemy.dialects.mysql import DATETIME

revision = 'e52ad70491b2'
down_revision = 'c64a93b80de1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not any(row['name'] == 'uq_mapping_sequence' for row in inspector.get_unique_constraints('forecast_mappings')):
        op.create_unique_constraint('uq_mapping_sequence', 'forecast_mappings', ['product_id', 'sequence'])
    if not any(row['name'] == 'ck_mapping_sequence' for row in inspector.get_check_constraints('forecast_mappings')):
        op.create_check_constraint('ck_mapping_sequence', 'forecast_mappings', 'sequence > 0')
    if bind.dialect.name == 'mysql':
        for table in ['forecast_mappings', 'forecasts', 'recommendations']:
            column = next(row for row in inspector.get_columns(table) if row['name'] == 'created_at')
            if getattr(column['type'], 'fsp', 0) != 6:
                op.alter_column(table, 'created_at', type_=DATETIME(fsp=6), existing_type=DateTime(), existing_nullable=False)


def downgrade():
    raise RuntimeError('Evidence precision and ordering must be preserved; downgrade requires reviewed recovery.')

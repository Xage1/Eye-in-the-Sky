"""Add astronomer_quotes and solar_events tables

Revision ID: b3e9f2a1c8d5
Revises: a2f8c1d3e9b7
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = 'b3e9f2a1c8d5'
down_revision = 'a2f8c1d3e9b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'astronomer_quotes',
        sa.Column('id',          sa.Integer(),     primary_key=True),
        sa.Column('quote',       sa.Text(),         nullable=False),
        sa.Column('astronomer',  sa.String(150),    nullable=False),
        sa.Column('birth_year',  sa.Integer(),      nullable=True),
        sa.Column('death_year',  sa.Integer(),      nullable=True),
        sa.Column('nationality', sa.String(100),    nullable=True),
        sa.Column('context',     sa.Text(),         nullable=True),
        sa.Column('category',    sa.String(80),     nullable=True),
        sa.Column('featured',    sa.Boolean(),      server_default='false'),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_astronomer_quotes_astronomer', 'astronomer_quotes', ['astronomer'])
    op.create_index('ix_astronomer_quotes_category',   'astronomer_quotes', ['category'])

    op.create_table(
        'solar_events',
        sa.Column('id',              sa.Integer(),  primary_key=True),
        sa.Column('name',            sa.String(200), nullable=False),
        sa.Column('event_type',      sa.String(80),  nullable=False),
        sa.Column('description',     sa.Text(),      nullable=True),
        sa.Column('start_time',      sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time',        sa.DateTime(timezone=True), nullable=True),
        sa.Column('peak_time',       sa.DateTime(timezone=True), nullable=True),
        sa.Column('visible_regions', sa.Text(),      nullable=True),
        sa.Column('min_latitude',    sa.Float(),     nullable=True),
        sa.Column('max_latitude',    sa.Float(),     nullable=True),
        sa.Column('zhr',             sa.Integer(),   nullable=True),
        sa.Column('radiant_ra',      sa.Float(),     nullable=True),
        sa.Column('radiant_dec',     sa.Float(),     nullable=True),
        sa.Column('parent_body',     sa.String(100), nullable=True),
        sa.Column('eclipse_type',    sa.String(50),  nullable=True),
        sa.Column('magnitude',       sa.Float(),     nullable=True),
        sa.Column('source',          sa.String(100), nullable=True),
        sa.Column('is_upcoming',     sa.Boolean(),   server_default='true'),
        sa.Column('is_notable',      sa.Boolean(),   server_default='false'),
        sa.Column('created_at',      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_solar_events_event_type',  'solar_events', ['event_type'])
    op.create_index('ix_solar_events_start_time',  'solar_events', ['start_time'])
    op.create_index('ix_solar_events_is_upcoming', 'solar_events', ['is_upcoming'])


def downgrade() -> None:
    op.drop_table('solar_events')
    op.drop_table('astronomer_quotes')
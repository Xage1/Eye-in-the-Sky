"""add visibility score and created_at to location_entries

Revision ID: f2a7b9c1d834
Revises: a1f3c9d2e766
Create Date: 2026-10-13 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a7b9c1d834"
down_revision: Union[str, Sequence[str], None] = "a1f3c9d2e766"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("location_entries", sa.Column("visibility_score", sa.Integer(), nullable=True))
    op.add_column("location_entries", sa.Column("visibility_updated_at", sa.DateTime(), nullable=True))
    op.add_column("location_entries", sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("location_entries", "created_at")
    op.drop_column("location_entries", "visibility_updated_at")
    op.drop_column("location_entries", "visibility_score")

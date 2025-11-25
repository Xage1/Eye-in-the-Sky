# alembic/versions/<timestamp>_create_lessons_table.py
from alembic import op
import sqlalchemy as sa

revision = 'create_lessons_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('lessons')
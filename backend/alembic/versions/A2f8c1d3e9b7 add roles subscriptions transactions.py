"""Add role, profile fields to users; add user_subscriptions and transactions tables

Revision ID: a2f8c1d3e9b7
Revises: create_lessons_table
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a2f8c1d3e9b7'
down_revision = 'create_lessons_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users: add new columns ────────────────────────────────────────────────
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(80), nullable=True, server_default='UTC'))
    op.add_column('users', sa.Column('language', sa.String(20), nullable=True, server_default='en'))
    op.add_column('users', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('occupation', sa.String(150), nullable=True))
    op.add_column('users', sa.Column('astronomy_level', sa.String(50), nullable=True, server_default='beginner'))
    op.add_column('users', sa.Column('twitter_handle', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('instagram_handle', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('website_url', sa.String(300), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))

    # ── user_subscriptions ────────────────────────────────────────────────────
    op.create_table(
        'user_subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('interval', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('provider', sa.String(20), nullable=True),
        sa.Column('paystack_customer_id', sa.String(100), nullable=True),
        sa.Column('paystack_reference', sa.String(100), nullable=True),
        
        sa.Column('mpesa_phone', sa.String(20), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_user_subscriptions_user_id', 'user_subscriptions', ['user_id'])
    op.create_index('ix_user_subscriptions_paystack_customer_id', 'user_subscriptions', ['paystack_customer_id'])

    # ── transactions ──────────────────────────────────────────────────────────
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('plan', sa.String(20), nullable=False),
        sa.Column('interval', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='KES'),
        sa.Column('mpesa_checkout_request_id', sa.String(100), nullable=True),
        sa.Column('mpesa_merchant_request_id', sa.String(100), nullable=True),
        sa.Column('mpesa_receipt_number', sa.String(50), nullable=True),
        sa.Column('mpesa_phone', sa.String(20), nullable=True),
        sa.Column('paystack_reference', sa.String(100), nullable=True),
        sa.Column('paystack_channel', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_mpesa_checkout_request_id', 'transactions', ['mpesa_checkout_request_id'])
    op.create_index('ix_transactions_paystack_reference', 'transactions', ['paystack_reference'])


def downgrade() -> None:
    op.drop_table('transactions')
    op.drop_table('user_subscriptions')
    for col in [
        'role', 'is_active', 'is_verified', 'avatar_url', 'bio', 'location',
        'country', 'timezone', 'language', 'date_of_birth', 'occupation',
        'astronomy_level', 'twitter_handle', 'instagram_handle', 'website_url',
        'created_at', 'updated_at', 'last_login',
    ]:
        op.drop_column('users', col)
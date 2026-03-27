"""
Subscription and Transaction models for Eye in the Sky.

Plans:
  free     — default, limited features
  pro      — KES 299/mo, full AR + satellites + history
  premium  — KES 599/mo, everything + push alerts + leaderboard

Payment providers:
  mpesa    — M-Pesa Daraja STK push (direct)
  paystack — Paystack hosted checkout (M-Pesa + cards + Apple Pay)
"""

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PlanTier(str, enum.Enum):
    free    = "free"
    pro     = "pro"
    premium = "premium"


class PlanInterval(str, enum.Enum):
    monthly = "monthly"
    yearly  = "yearly"


class SubscriptionStatus(str, enum.Enum):
    active    = "active"
    cancelled = "cancelled"
    expired   = "expired"
    trial     = "trial"
    paused    = "paused"


class PaymentProvider(str, enum.Enum):
    mpesa    = "mpesa"
    paystack = "paystack"


class PaymentStatus(str, enum.Enum):
    pending   = "pending"
    completed = "completed"
    failed    = "failed"
    refunded  = "refunded"
    cancelled = "cancelled"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    plan     = Column(Enum(PlanTier), default=PlanTier.free, nullable=False)
    status   = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active)
    interval = Column(Enum(PlanInterval), default=PlanInterval.monthly)
    provider = Column(Enum(PaymentProvider), nullable=True)

    # M-Pesa fields
    mpesa_phone = Column(String(20), nullable=True)

    # Paystack fields
    paystack_customer_id = Column(String(100), nullable=True, index=True)
    paystack_reference   = Column(String(100), nullable=True, index=True)

    # Dates
    started_at           = Column(DateTime(timezone=True), server_default=func.now())
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end   = Column(DateTime(timezone=True), nullable=True)
    cancelled_at         = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at        = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscription")


class Transaction(Base):
    __tablename__ = "transactions"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    status   = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    plan     = Column(Enum(PlanTier), nullable=False)
    interval = Column(Enum(PlanInterval), default=PlanInterval.monthly)

    # Amounts
    amount   = Column(Float, nullable=False)
    currency = Column(String(10), default="KES", nullable=False)

    # M-Pesa (Daraja direct)
    mpesa_checkout_request_id = Column(String(100), nullable=True, index=True)
    mpesa_merchant_request_id = Column(String(100), nullable=True)
    mpesa_receipt_number      = Column(String(50),  nullable=True)
    mpesa_phone               = Column(String(20),  nullable=True)

    # Paystack
    paystack_reference = Column(String(100), nullable=True, index=True)
    paystack_channel   = Column(String(50),  nullable=True)

    # Meta
    description    = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    completed_at   = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="transactions")
"""
app/schemas/subscription.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.subscription import (
    PlanTier, PlanInterval, SubscriptionStatus,
    PaymentProvider, PaymentStatus
)


class SubscriptionOut(BaseModel):
    id:                   int
    user_id:              int
    plan:                 PlanTier
    status:               SubscriptionStatus
    interval:             PlanInterval
    provider:             Optional[PaymentProvider] = None
    started_at:           Optional[datetime]        = None
    current_period_start: Optional[datetime]        = None
    current_period_end:   Optional[datetime]        = None
    cancelled_at:         Optional[datetime]        = None
    trial_ends_at:        Optional[datetime]        = None

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id:              int
    user_id:         int
    provider:        PaymentProvider
    status:          PaymentStatus
    plan:            PlanTier
    amount:          float
    currency:        str
    description:     Optional[str]     = None
    failure_reason:  Optional[str]     = None
    created_at:      Optional[datetime] = None
    completed_at:    Optional[datetime] = None

    # M-Pesa
    mpesa_receipt_number: Optional[str] = None
    mpesa_phone:          Optional[str] = None

    # Paystack
    paystack_reference: Optional[str] = None
    paystack_channel:   Optional[str] = None

    model_config = {"from_attributes": True}


# ── M-Pesa STK push request ───────────────────────────────────────────────────
class MpesaSTKRequest(BaseModel):
    phone:    str
    plan:     PlanTier
    interval: PlanInterval = PlanInterval.monthly
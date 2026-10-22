"""
Payments router for Eye in the Sky - Kenya.

Providers:
  Paystack - M-Pesa, Visa, Mastercard, Apple Pay (hosted checkout)
  Daraja   - Direct M-Pesa STK push (optional, lower fees at scale)

Endpoints:
  GET  /payments/plans                      All plans + pricing
  POST /payments/checkout                   Paystack hosted checkout
  POST /payments/verify                     Verify a Paystack payment by reference
  POST /payments/webhook                    Paystack webhook (signature required)
  POST /payments/mpesa/stk-push             Direct Daraja STK push
  POST /payments/mpesa/status               Re-check an STK push with Safaricom
  POST /payments/mpesa/callback/{secret}    Daraja callback (secret in the URL)
  GET  /payments/subscription               Current user's subscription
  GET  /payments/transactions               User's payment history
  POST /payments/cancel                     Cancel subscription

Security model
  * A Transaction row is created server-side before any money moves. It is the only
    source of truth for who is paying, for which plan and how much. Nothing about the
    plan, user or amount is ever taken from a request body or a webhook payload.
  * Paystack: the reference must match a pending Transaction. /verify also requires the
    transaction to belong to the caller; the webhook requires a valid HMAC signature.
    Either way Paystack itself is asked to confirm the payment (status, amount, currency,
    owner, plan) before anything is credited.
  * M-Pesa: the callback URL carries a secret and the callback is only a trigger - the
    outcome is confirmed with Safaricom's STK Push Query. Fails closed when
    MPESA_CALLBACK_SECRET is not set.
  * A transaction moves pending -> completed/failed exactly once (row lock + status
    check), so replayed or concurrent notifications are harmless.
"""

import hmac
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.subscription import (
    UserSubscription, Transaction,
    PlanTier, PlanInterval, SubscriptionStatus,
    PaymentProvider, PaymentStatus,
)
from app.schemas.subscription import SubscriptionOut, TransactionOut, MpesaSTKRequest
from app.services.paystack_service import (
    initialize_transaction,
    verify_transaction as paystack_verify,
    verify_webhook_signature,
    parse_webhook,
)
from app.services.mpesa_services import initiate_stk_push, parse_stk_callback, query_stk_status
from app.utils.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

MPESA_CALLBACK_SECRET = os.getenv("MPESA_CALLBACK_SECRET", "")
_PERIOD_DAYS = {PlanInterval.monthly: 30, PlanInterval.yearly: 365}


def _ack() -> dict:
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


class CheckoutRequest(BaseModel):
    plan:     PlanTier
    interval: PlanInterval = PlanInterval.monthly
    phone:    Optional[str] = None


class VerifyRequest(BaseModel):
    reference: str = Field(min_length=6, max_length=100)


class MpesaStatusRequest(BaseModel):
    checkout_request_id: str = Field(min_length=6, max_length=100)


PLANS = {
    "free": {
        "name":      "Free",
        "price_kes": 0,
        "interval":  "forever",
        "features": [
            "AR star map - basic (magnitude limit 4.0)",
            "20 constellations",
            "5 quiz questions per day",
            "Upcoming solar events only",
            "3 astronomer quotes per day",
        ],
    },
    "pro": {
        "name":              "Pro",
        "price_kes_monthly": 299,
        "price_kes_yearly":  2990,
        "features": [
            "Full AR star map - all stars to magnitude 6.5",
            "All 88 constellations with mythology",
            "Live satellite tracking - top 10 visible",
            "Unlimited quizzes",
            "Solar event history + upcoming",
            "Unlimited astronomer quotes",
            "ISS live position + flyover alerts",
            "Moon phase calendar",
        ],
    },
    "premium": {
        "name":              "Premium",
        "price_kes_monthly": 599,
        "price_kes_yearly":  5990,
        "features": [
            "Everything in Pro",
            "All visible satellites + full orbital details",
            "Push notification alerts (events + ISS passes)",
            "Quiz leaderboard + achievements",
            "Constellation mythology deep-dives",
            "Night sky watch - full event history",
            "Early access to new features",
            "Priority support",
        ],
    },
}


# ---------------------------------------------------------------- helpers

async def _tx_by_reference(db: AsyncSession, reference: str) -> Optional[Transaction]:
    res = await db.execute(
        select(Transaction)
        .where(Transaction.paystack_reference == reference)
        .execution_options(populate_existing=True)
    )
    return res.scalars().first()


async def _tx_by_checkout(db: AsyncSession, checkout_id: str) -> Optional[Transaction]:
    res = await db.execute(
        select(Transaction)
        .where(Transaction.mpesa_checkout_request_id == checkout_id)
        .execution_options(populate_existing=True)
    )
    return res.scalars().first()


async def _apply_subscription(tx: Transaction, phone: Optional[str], db: AsyncSession) -> None:
    """Create or update the subscription for a confirmed payment and set the paid period."""
    now = datetime.now(timezone.utc)
    res = await db.execute(select(UserSubscription).where(UserSubscription.user_id == tx.user_id))
    sub = res.scalars().first()

    days = _PERIOD_DAYS.get(tx.interval, 30)
    start = now
    if (sub is not None and sub.status == SubscriptionStatus.active and sub.plan == tx.plan
            and sub.current_period_end is not None and sub.current_period_end > now):
        start = sub.current_period_end  # renewal: extend the period that is already paid for
    end = start + timedelta(days=days)

    if sub is None:
        sub = UserSubscription(user_id=tx.user_id)
        db.add(sub)
    sub.plan = tx.plan
    sub.status = SubscriptionStatus.active
    sub.interval = tx.interval
    sub.provider = tx.provider
    sub.current_period_start = start
    sub.current_period_end = end
    sub.cancelled_at = None
    if phone:
        sub.mpesa_phone = str(phone)[:20]
    if tx.paystack_reference:
        sub.paystack_reference = tx.paystack_reference


async def _complete_once(db: AsyncSession, tx_id: int, *, phone: Optional[str] = None,
                         channel: Optional[str] = None, receipt: Optional[str] = None) -> Optional[dict]:
    """
    Lock the transaction row and move it pending -> completed. Returns a summary if THIS call
    completed it, or None if it was not pending (already processed / unknown).
    """
    res = await db.execute(select(Transaction).where(Transaction.id == tx_id).with_for_update())
    tx = res.scalars().first()
    if tx is None or tx.status != PaymentStatus.pending:
        await db.rollback()  # release the lock
        return None
    tx.status = PaymentStatus.completed
    tx.completed_at = datetime.now(timezone.utc)
    if channel:
        tx.paystack_channel = str(channel)[:50]
    if receipt:
        tx.mpesa_receipt_number = str(receipt)[:50]
    await _apply_subscription(tx, phone, db)
    info = {
        "plan": tx.plan.value,
        "interval": tx.interval.value if tx.interval else "monthly",
        "amount": tx.amount,
    }
    await db.commit()
    return info


async def _fail_once(db: AsyncSession, tx_id: int, reason: Optional[str]) -> bool:
    res = await db.execute(select(Transaction).where(Transaction.id == tx_id).with_for_update())
    tx = res.scalars().first()
    if tx is None or tx.status != PaymentStatus.pending:
        await db.rollback()
        return False
    tx.status = PaymentStatus.failed
    tx.failure_reason = (reason or "Payment failed")[:500]
    await db.commit()
    return True


def _paystack_mismatch(tx: Transaction, verified: dict) -> Optional[str]:
    """Compare what Paystack says was paid with what OUR transaction row expects."""
    if verified.get("reference") != tx.paystack_reference:
        return "reference mismatch"
    if str(verified.get("user_id")) != str(tx.user_id):
        return "owner mismatch"
    if (verified.get("currency") or "").upper() != (tx.currency or "KES").upper():
        return "currency mismatch"
    if float(verified.get("amount_kes") or 0) + 1e-6 < float(tx.amount):
        return "amount too low"
    interval = tx.interval.value if tx.interval else "monthly"
    if (verified.get("plan"), verified.get("interval")) != (tx.plan.value, interval):
        return "plan mismatch"
    return None


def _valid_signature(payload: bytes, signature: Optional[str]) -> bool:
    if not signature:
        return False
    try:
        return bool(verify_webhook_signature(payload, signature))
    except Exception:
        return False


async def _settle_mpesa(db: AsyncSession, tx_id: int, checkout_id: str,
                        phone: Optional[str] = None, receipt: Optional[str] = None) -> str:
    """Ask Safaricom for the real outcome, then complete/fail the transaction exactly once."""
    try:
        q = await query_stk_status(checkout_id)
    except Exception as exc:
        logger.warning("STK query inconclusive | checkout=%s error=%s", checkout_id, exc)
        return "unknown"
    if q.get("result_code") is None:
        return "unknown"
    if q.get("confirmed"):
        done = await _complete_once(db, tx_id, phone=phone, receipt=receipt)
        return "completed" if done else "already_processed"
    await _fail_once(db, tx_id, q.get("result_desc"))
    return "failed"


# ---------------------------------------------------------------- plans / reads

@router.get("/plans")
async def get_plans():
    """All subscription plans with KES pricing and feature lists."""
    return {"plans": PLANS}


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    return sub


@router.get("/transactions", response_model=list[TransactionOut])
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


# ---------------------------------------------------------------- Paystack

@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def paystack_checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initialize a Paystack payment. Returns authorization_url - redirect the user there.
    The transaction row (with its reference) is the record /verify and the webhook match against.
    """
    try:
        result = await initialize_transaction(
            user_id=current_user.id,
            email=current_user.email,
            plan=payload.plan.value,
            interval=payload.interval.value,
            phone=payload.phone,
        )
    except (ValueError, EnvironmentError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Paystack checkout error | user=%s error=%s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="Payment service error - please try again")

    tx = Transaction(
        user_id=current_user.id,
        provider=PaymentProvider.paystack,
        status=PaymentStatus.pending,
        plan=payload.plan,
        interval=payload.interval,
        amount=result["amount_kes"],
        currency="KES",
        paystack_reference=result["reference"],
        mpesa_phone=payload.phone,
        description=f"Eye in the Sky {payload.plan.value.title()} {payload.interval.value}",
    )
    db.add(tx)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error("Could not record Paystack transaction | user=%s ref=%s error=%s",
                     current_user.id, result["reference"], exc)
        raise HTTPException(status_code=500, detail="Could not record the payment - please try again")

    return {
        "authorization_url": result["authorization_url"],
        "reference":         result["reference"],
        "amount_kes":        result["amount_kes"],
        "currency":          "KES",
        "message":           "Redirect user to authorization_url to complete payment",
    }


@router.post("/verify")
async def verify_payment(
    payload: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify a Paystack payment by reference (call when the user returns from checkout).
    The reference must belong to the caller's own pending transaction; Paystack confirms
    the payment; the transaction can only be completed once.
    """
    ref = payload.reference.strip()
    tx = await _tx_by_reference(db, ref)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Unknown payment reference")

    plan_val = tx.plan.value
    amount_val = tx.amount
    if tx.status == PaymentStatus.completed:
        return {"verified": True, "already_processed": True, "plan": plan_val, "amount": amount_val,
                "message": f"{plan_val.title()} subscription is already active."}
    if tx.status != PaymentStatus.pending:
        raise HTTPException(status_code=409, detail=f"Payment is {tx.status.value}")

    try:
        verified = await paystack_verify(ref)
    except Exception as exc:
        logger.error("Paystack verify failed | ref=%s error=%s", ref, exc)
        raise HTTPException(status_code=502, detail="Could not verify the payment with Paystack")

    if not verified.get("verified"):
        raise HTTPException(status_code=402, detail=f"Payment not confirmed. Status: {verified.get('status')}")

    problem = _paystack_mismatch(tx, verified)
    if problem:
        logger.warning("Paystack verify mismatch | ref=%s user=%s problem=%s", ref, current_user.id, problem)
        raise HTTPException(status_code=409, detail="Payment does not match this order")

    done = await _complete_once(db, tx.id, phone=verified.get("customer_phone"),
                                channel=verified.get("channel"))
    return {
        "verified": True,
        "already_processed": done is None,  # the webhook got there first
        "plan": plan_val,
        "channel": verified.get("channel"),
        "amount": verified.get("amount_kes"),
        "message": f"Payment confirmed. {plan_val.title()} subscription active.",
    }


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Paystack webhook. The HMAC signature is MANDATORY. The event only identifies a reference;
    the user, plan and amount come from our own transaction row, confirmed with Paystack.
    """
    payload_bytes = await request.body()
    if not _valid_signature(payload_bytes, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        data = parse_webhook(json.loads(payload_bytes))
    except Exception as exc:
        logger.error("Paystack webhook parse error: %s", exc)
        return {"status": "ok"}

    ref = data.get("reference")
    if not data.get("success") or not ref:
        return {"status": "ok"}

    tx = await _tx_by_reference(db, ref)
    if tx is None:
        logger.warning("Webhook for unknown reference | ref=%s", ref)
        return {"status": "ok"}
    if tx.status != PaymentStatus.pending:
        return {"status": "ok"}  # replay / already processed

    try:
        verified = await paystack_verify(ref)
    except Exception as exc:
        logger.error("Webhook re-verify error | ref=%s error=%s", ref, exc)
        raise HTTPException(status_code=503, detail="Temporarily unable to verify")  # Paystack will retry

    if not verified.get("verified"):
        return {"status": "ok"}
    problem = _paystack_mismatch(tx, verified)
    if problem:
        logger.warning("Webhook mismatch | ref=%s problem=%s", ref, problem)
        return {"status": "ok"}

    await _complete_once(db, tx.id, phone=verified.get("customer_phone"), channel=verified.get("channel"))
    return {"status": "ok"}


# ---------------------------------------------------------------- Daraja (M-Pesa direct)

@router.post("/mpesa/stk-push", status_code=status.HTTP_202_ACCEPTED)
async def mpesa_daraja_stk(
    payload: MpesaSTKRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Direct M-Pesa STK push. The result arrives via the callback and can be re-checked via /mpesa/status."""
    try:
        result = await initiate_stk_push(
            phone=payload.phone,
            plan=payload.plan.value,
            interval=payload.interval.value,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Daraja STK push failed | user=%s error=%s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="M-Pesa service error - try again")

    tx = Transaction(
        user_id=current_user.id,
        provider=PaymentProvider.mpesa,
        status=PaymentStatus.pending,
        plan=payload.plan,
        interval=payload.interval,
        amount=result["amount"],
        currency="KES",
        mpesa_checkout_request_id=result["checkout_request_id"],
        mpesa_merchant_request_id=result["merchant_request_id"],
        mpesa_phone=result["phone"],
        description=f"Eye in the Sky {payload.plan.value.title()} - M-Pesa",
    )
    db.add(tx)
    await db.commit()

    return {
        "message":             "Payment prompt sent. Enter your M-Pesa PIN to confirm.",
        "checkout_request_id": result["checkout_request_id"],
        "amount":              result["amount"],
        "currency":            "KES",
        "phone":               result["phone"],
    }


@router.post("/mpesa/status")
async def mpesa_payment_status(
    payload: MpesaStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-check an STK push with Safaricom (use when the callback never arrived)."""
    tx = await _tx_by_checkout(db, payload.checkout_request_id)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Unknown checkout request")

    tx_id, checkout_id = tx.id, tx.mpesa_checkout_request_id
    if tx.status == PaymentStatus.pending:
        await _settle_mpesa(db, tx_id, checkout_id)
        tx = await _tx_by_checkout(db, checkout_id)

    state = tx.status.value
    return {
        "checkout_request_id": checkout_id,
        "status": state,
        "plan": tx.plan.value,
        "message": {
            "completed": "Payment confirmed.",
            "failed": tx.failure_reason or "Payment failed.",
            "pending": "Still waiting for the M-Pesa confirmation.",
        }.get(state, state),
    }


@router.post("/mpesa/callback/{secret}", status_code=status.HTTP_200_OK)
async def mpesa_daraja_callback(
    secret: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Safaricom Daraja callback. Set MPESA_CALLBACK_URL to .../payments/mpesa/callback/<MPESA_CALLBACK_SECRET>.
    The body is only a trigger: the outcome is confirmed with Safaricom before anything is credited.
    """
    if not MPESA_CALLBACK_SECRET or not hmac.compare_digest(secret.encode(), MPESA_CALLBACK_SECRET.encode()):
        raise HTTPException(status_code=404, detail="Not found")

    try:
        body = await request.json()
        data = parse_stk_callback(body)
    except Exception as exc:
        logger.error("Daraja callback parse error: %s", exc)
        return _ack()

    checkout_id = data.get("checkout_request_id")
    if not checkout_id:
        return _ack()
    tx = await _tx_by_checkout(db, str(checkout_id))
    if tx is None or tx.status != PaymentStatus.pending:
        return _ack()

    try:
        if (data.get("merchant_request_id") and tx.mpesa_merchant_request_id
                and data["merchant_request_id"] != tx.mpesa_merchant_request_id):
            logger.warning("Daraja callback merchant id mismatch | checkout=%s", checkout_id)
            return _ack()
        if data.get("amount") is not None and float(data["amount"]) + 1e-6 < float(tx.amount):
            logger.warning("Daraja callback amount too low | checkout=%s", checkout_id)
            return _ack()
    except Exception:
        return _ack()

    outcome = await _settle_mpesa(db, tx.id, tx.mpesa_checkout_request_id,
                                  phone=data.get("phone"), receipt=data.get("receipt_number"))
    logger.info("Daraja callback settled | checkout=%s outcome=%s", checkout_id, outcome)
    return _ack()


# ---------------------------------------------------------------- cancel

@router.post("/cancel")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel active subscription and revert to Free plan."""
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    )
    sub = result.scalars().first()
    if not sub or sub.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    sub.status       = SubscriptionStatus.cancelled
    sub.plan         = PlanTier.free
    sub.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Subscription cancelled. You are now on the Free plan."}
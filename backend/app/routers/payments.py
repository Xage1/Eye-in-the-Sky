"""
Payments router for Eye in the Sky — Kenya.

Providers:
  Paystack — M-Pesa, Visa, Mastercard, Apple Pay (hosted checkout)
  Daraja   — Direct M-Pesa STK push (optional, lower fees at scale)

Endpoints:
  GET  /payments/plans                  — All plans + pricing
  POST /payments/checkout               — Paystack hosted checkout
  POST /payments/verify                 — Verify payment by reference
  POST /payments/webhook                — Paystack webhook handler
  POST /payments/mpesa/stk-push         — Direct Daraja STK push
  POST /payments/mpesa/callback         — Daraja callback
  GET  /payments/subscription           — Current user's subscription
  GET  /payments/transactions           — User's payment history
  POST /payments/cancel                 — Cancel subscription
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
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
from app.services.mpesa_service import initiate_stk_push, parse_stk_callback
from app.utils.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


# ── Schemas ────────────────────────────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    plan:     PlanTier
    interval: PlanInterval = PlanInterval.monthly
    phone:    Optional[str] = None


class VerifyRequest(BaseModel):
    reference: str


# ── Plan catalogue ─────────────────────────────────────────────────────────────
PLANS = {
    "free": {
        "name":      "Free",
        "price_kes": 0,
        "interval":  "forever",
        "features": [
            "AR star map — basic (magnitude limit 4.0)",
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
            "Full AR star map — all stars to magnitude 6.5",
            "All 88 constellations with mythology",
            "Live satellite tracking — top 10 visible",
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
            "Night sky watch — full event history",
            "Early access to new features",
            "Priority support",
        ],
    },
}


# ── GET /payments/plans ────────────────────────────────────────────────────────
@router.get("/plans")
async def get_plans():
    """All subscription plans with KES pricing and feature lists."""
    return {"plans": PLANS}


# ── GET /payments/subscription ────────────────────────────────────────────────
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


# ── GET /payments/transactions ────────────────────────────────────────────────
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


# ── POST /payments/checkout ────────────────────────────────────────────────────
@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def paystack_checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initialize a Paystack payment.
    Returns authorization_url — redirect the user here to complete payment.
    Supports M-Pesa, Visa, Mastercard, Apple Pay in one checkout page.
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
        raise HTTPException(status_code=502, detail="Payment service error — please try again")

    # Record pending transaction
    tx = Transaction(
        user_id=current_user.id,
        provider=PaymentProvider.mpesa,
        status=PaymentStatus.pending,
        plan=payload.plan,
        interval=payload.interval,
        amount=result["amount_kes"],
        currency="KES",
        mpesa_phone=payload.phone,
        description=f"Eye in the Sky {payload.plan.value.title()} {payload.interval.value}",
    )
    db.add(tx)
    await db.commit()

    return {
        "authorization_url": result["authorization_url"],
        "reference":         result["reference"],
        "amount_kes":        result["amount_kes"],
        "currency":          "KES",
        "message":           "Redirect user to authorization_url to complete payment",
    }


# ── POST /payments/verify ──────────────────────────────────────────────────────
@router.post("/verify")
async def verify_payment(
    payload: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify a Paystack payment by reference.
    Call this when the user returns from the hosted checkout page.
    The reference is appended to your PAYSTACK_CALLBACK_URL as ?reference=xxx
    """
    try:
        verified = await paystack_verify(payload.reference)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Verification failed: {exc}")

    if verified["verified"]:
        plan_str     = verified.get("plan", "pro")
        interval_str = verified.get("interval", "monthly")

        # Find and update the pending transaction
        result = await db.execute(
            select(Transaction).where(
                Transaction.user_id == current_user.id,
                Transaction.status == PaymentStatus.pending,
            ).order_by(Transaction.created_at.desc())
        )
        tx = result.scalars().first()
        if tx:
            tx.status       = PaymentStatus.completed
            tx.completed_at = datetime.now(timezone.utc)
            tx.plan         = PlanTier(plan_str)
            tx.amount       = verified["amount_kes"]
            await _upgrade_subscription(
                tx,
                verified.get("customer_phone"),
                PaymentProvider.mpesa,
                db,
            )
            await db.commit()

        return {
            "verified": True,
            "plan":     plan_str,
            "channel":  verified.get("channel"),
            "amount":   verified.get("amount_kes"),
            "message":  f"Payment confirmed. {plan_str.title()} subscription activated.",
        }

    raise HTTPException(
        status_code=402,
        detail=f"Payment not confirmed. Status: {verified.get('status')}",
    )


# ── POST /payments/webhook ─────────────────────────────────────────────────────
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Paystack webhook handler.
    Configure in Paystack Dashboard → Settings → API Keys & Webhooks.
    Webhook URL: https://your-ngrok-url/payments/webhook
    """
    payload_bytes = await request.body()

    # Always verify webhook signature
    if x_paystack_signature:
        if not verify_webhook_signature(payload_bytes, x_paystack_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = await request.json()
        data = parse_webhook(body)
    except Exception as exc:
        logger.error("Paystack webhook parse error: %s", exc)
        return {"status": "ok"}

    logger.info(
        "Paystack webhook | event=%s success=%s ref=%s user=%s",
        data["event"], data["success"], data["reference"], data["user_id"],
    )

    if data["success"]:
        user_id = int(data["user_id"]) if data.get("user_id") else None
        if not user_id:
            return {"status": "ok"}

        plan_str     = data.get("plan", "pro")
        interval_str = data.get("interval", "monthly")

        # Verify with Paystack before acting
        try:
            confirmed = await paystack_verify(data["reference"])
            if not confirmed["verified"]:
                logger.warning("Webhook verification failed | ref=%s", data["reference"])
                return {"status": "ok"}
        except Exception as exc:
            logger.error("Webhook re-verify error: %s", exc)
            return {"status": "ok"}

        # Update most recent pending transaction for this user
        result = await db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.status == PaymentStatus.pending,
            ).order_by(Transaction.created_at.desc())
        )
        tx = result.scalars().first()
        if tx:
            tx.status       = PaymentStatus.completed
            tx.completed_at = datetime.now(timezone.utc)
            tx.plan         = PlanTier(plan_str)
            tx.amount       = confirmed["amount_kes"]
            await _upgrade_subscription(
                tx,
                data.get("customer_phone"),
                PaymentProvider.mpesa,
                db,
            )
            await db.commit()

    return {"status": "ok"}


# ── POST /payments/mpesa/stk-push (Daraja direct) ─────────────────────────────
@router.post("/mpesa/stk-push", status_code=status.HTTP_202_ACCEPTED)
async def mpesa_daraja_stk(
    payload: MpesaSTKRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Direct M-Pesa STK push via Safaricom Daraja.
    Lower fees than Paystack at high volume.
    Result delivered via /mpesa/callback webhook.
    """
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
        raise HTTPException(status_code=502, detail="M-Pesa service error — try again")

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
        description=f"Eye in the Sky {payload.plan.value.title()} — M-Pesa",
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


# ── POST /payments/mpesa/callback ─────────────────────────────────────────────
@router.post("/mpesa/callback", status_code=status.HTTP_200_OK)
async def mpesa_daraja_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Safaricom Daraja payment callback — must be publicly accessible via ngrok."""
    try:
        body = await request.json()
        data = parse_stk_callback(body)
    except Exception as exc:
        logger.error("Daraja callback parse error: %s", exc)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    result = await db.execute(
        select(Transaction).where(
            Transaction.mpesa_checkout_request_id == data["checkout_request_id"]
        )
    )
    tx = result.scalars().first()
    if not tx:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    if data["success"]:
        tx.status               = PaymentStatus.completed
        tx.mpesa_receipt_number = data["receipt_number"]
        tx.completed_at         = datetime.now(timezone.utc)
        await _upgrade_subscription(tx, data.get("phone"), PaymentProvider.mpesa, db)
    else:
        tx.status         = PaymentStatus.failed
        tx.failure_reason = data["result_desc"]

    await db.commit()
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


# ── POST /payments/cancel ─────────────────────────────────────────────────────
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


# ── Internal helper ────────────────────────────────────────────────────────────
async def _upgrade_subscription(
    tx: Transaction,
    phone: Optional[str],
    provider: PaymentProvider,
    db: AsyncSession,
) -> None:
    """Upgrade or create a subscription after confirmed payment."""
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == tx.user_id)
    )
    sub = result.scalars().first()
    if sub:
        sub.plan     = tx.plan
        sub.status   = SubscriptionStatus.active
        sub.provider = provider
        if phone:
            sub.mpesa_phone = phone
    else:
        db.add(UserSubscription(
            user_id=tx.user_id,
            plan=tx.plan,
            status=SubscriptionStatus.active,
            provider=provider,
            mpesa_phone=phone,
        ))
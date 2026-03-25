"""
Payments router for Eye in the Sky.

Endpoints:
  GET  /payments/plans                    — List all subscription plans + pricing
  POST /payments/mpesa/stk-push           — Initiate M-Pesa STK push
  POST /payments/mpesa/callback           — Safaricom callback (webhook)
  POST /payments/stripe/checkout          — Create Stripe checkout session
  POST /payments/stripe/webhook           — Stripe webhook handler
  GET  /payments/stripe/portal            — Stripe customer portal URL
  GET  /payments/subscription             — Current user's subscription
  GET  /payments/transactions             — Current user's transaction history
  POST /payments/cancel                   — Cancel active subscription
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter, Depends, HTTPException, Header,
    Request, status
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import stripe

from app.models.user import User
from app.models.subscription import (
    UserSubscription, Transaction,
    PlanTier, PlanInterval, SubscriptionStatus,
    PaymentProvider, PaymentStatus,
)
from app.schemas.subscription import (
    SubscriptionOut, TransactionOut,
    MpesaSTKRequest, StripeCheckoutRequest, StripeCheckoutOut,
)
from app.services.mpesa_service import initiate_stk_push, parse_stk_callback
from app.services.stripe_service import (
    create_checkout_session, construct_webhook_event,
    parse_webhook_event, cancel_subscription,
    get_customer_portal_url,
)
from app.utils.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


# ── Plan catalogue ─────────────────────────────────────────────────────────────
PLANS = {
    "free": {
        "name":        "Free",
        "price_kes":   0,
        "price_usd":   0,
        "interval":    "forever",
        "features": [
            "AR star map — basic",
            "20 constellations",
            "5 quiz questions per day",
            "Upcoming solar events only",
            "3 astronomer quotes per day",
        ],
    },
    "pro": {
        "name":          "Pro",
        "price_kes_monthly": 299,
        "price_kes_yearly":  2990,
        "price_usd_monthly": 2.99,
        "price_usd_yearly":  29.90,
        "features": [
            "Full AR star map + all 88 constellations",
            "Live satellite tracking (top 10 visible)",
            "Unlimited quizzes",
            "Solar event history + upcoming",
            "Unlimited astronomer quotes",
            "ISS live position + flyover alerts",
            "Moon phase calendar",
        ],
    },
    "premium": {
        "name":          "Premium",
        "price_kes_monthly": 599,
        "price_kes_yearly":  5990,
        "price_usd_monthly": 4.99,
        "price_usd_yearly":  49.90,
        "features": [
            "Everything in Pro",
            "All satellites visible + full details",
            "Push notification alerts (events + ISS)",
            "Quiz leaderboard + achievements",
            "Constellation mythology deep-dives",
            "Early access to new features",
            "Priority support",
        ],
    },
}


# ── GET /payments/plans ────────────────────────────────────────────────────────
@router.get("/plans")
async def get_plans():
    """Return all available subscription plans with pricing and features."""
    return {"plans": PLANS}


# ── GET /payments/subscription ────────────────────────────────────────────────
@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's active subscription."""
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
    """Return the current user's payment transaction history."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


# ── POST /payments/mpesa/stk-push ─────────────────────────────────────────────
@router.post("/mpesa/stk-push", status_code=status.HTTP_202_ACCEPTED)
async def mpesa_stk_push(
    payload: MpesaSTKRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiate an M-Pesa STK push payment.
    The user's phone will receive a payment prompt immediately.
    Payment result is delivered via the /mpesa/callback webhook.
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
        logger.error("M-Pesa STK push failed | user=%s error=%s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="M-Pesa service error — try again")

    # Record pending transaction
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
        description=f"Eye in the Sky {payload.plan.value.title()} {payload.interval.value}",
    )
    db.add(tx)
    await db.commit()

    return {
        "message":             "Payment prompt sent to your phone. Enter your M-Pesa PIN to confirm.",
        "checkout_request_id": result["checkout_request_id"],
        "amount":              result["amount"],
        "currency":            "KES",
        "phone":               result["phone"],
    }


# ── POST /payments/mpesa/callback ─────────────────────────────────────────────
@router.post("/mpesa/callback", status_code=status.HTTP_200_OK)
async def mpesa_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Safaricom Daraja callback endpoint.
    Called by Safaricom servers after the user confirms or cancels payment.
    This URL must be publicly accessible — use ngrok in development.
    """
    try:
        body = await request.json()
        data = parse_stk_callback(body)
    except Exception as exc:
        logger.error("M-Pesa callback parse error: %s", exc)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    logger.info(
        "M-Pesa callback | success=%s checkout_id=%s receipt=%s",
        data["success"], data["checkout_request_id"], data["receipt_number"],
    )

    # Find the pending transaction
    result = await db.execute(
        select(Transaction).where(
            Transaction.mpesa_checkout_request_id == data["checkout_request_id"]
        )
    )
    tx = result.scalars().first()
    if not tx:
        logger.warning("No transaction found for checkout_id=%s", data["checkout_request_id"])
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    if data["success"]:
        tx.status               = PaymentStatus.completed
        tx.mpesa_receipt_number = data["receipt_number"]
        tx.completed_at         = datetime.now(timezone.utc)

        # Upgrade the user's subscription
        sub_result = await db.execute(
            select(UserSubscription).where(UserSubscription.user_id == tx.user_id)
        )
        sub = sub_result.scalars().first()
        if sub:
            sub.plan     = tx.plan
            sub.status   = SubscriptionStatus.active
            sub.provider = PaymentProvider.mpesa
            sub.mpesa_phone = data["phone"]
        else:
            db.add(UserSubscription(
                user_id=tx.user_id,
                plan=tx.plan,
                status=SubscriptionStatus.active,
                provider=PaymentProvider.mpesa,
                mpesa_phone=data["phone"],
            ))
    else:
        tx.status         = PaymentStatus.failed
        tx.failure_reason = data["result_desc"]

    await db.commit()
    # Safaricom requires this exact response to acknowledge receipt
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


# ── POST /payments/stripe/checkout ────────────────────────────────────────────
@router.post("/stripe/checkout", response_model=StripeCheckoutOut)
async def stripe_checkout(
    payload: StripeCheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout Session.
    Returns a URL to redirect the user to Stripe's hosted payment page.
    """
    try:
        result = create_checkout_session(
            user_id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            plan=payload.plan.value,
            interval=payload.interval.value,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except stripe.error.StripeError as exc:
        logger.error("Stripe checkout error | user=%s error=%s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="Stripe service error — try again")

    # Record pending transaction
    tx = Transaction(
        user_id=current_user.id,
        provider=PaymentProvider.stripe,
        status=PaymentStatus.pending,
        plan=payload.plan,
        interval=payload.interval,
        amount=0,
        currency="USD",
        description=f"Eye in the Sky {payload.plan.value.title()} {payload.interval.value}",
    )
    db.add(tx)
    await db.commit()

    return {
        "checkout_url": result["checkout_url"],
        "session_id":   result["session_id"],
    }


# ── POST /payments/stripe/webhook ─────────────────────────────────────────────
@router.post("/stripe/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Stripe webhook handler.
    Stripe signs all webhook payloads — we verify the signature before processing.
    Configure your webhook in Stripe Dashboard → Developers → Webhooks.
    Add endpoint: https://your-domain/payments/stripe/webhook
    Listen for: checkout.session.completed, customer.subscription.updated,
                customer.subscription.deleted, invoice.payment_failed
    """
    payload = await request.body()

    try:
        event = construct_webhook_event(payload, stripe_signature or "")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature")

    data = parse_webhook_event(event)
    event_type = data["event_type"]
    logger.info("Stripe webhook | type=%s user=%s", event_type, data.get("user_id"))

    if event_type == "checkout.session.completed":
        user_id = int(data["user_id"]) if data["user_id"] else None
        if not user_id:
            return {"received": True}

        plan     = PlanTier(data["plan"])
        interval = PlanInterval(data["interval"])

        # Update pending transaction
        result = await db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.provider == PaymentProvider.stripe,
                Transaction.status == PaymentStatus.pending,
            )
        )
        tx = result.scalars().first()
        if tx:
            tx.status                  = PaymentStatus.completed
            tx.plan                    = plan
            tx.interval                = interval
            tx.stripe_payment_intent_id = data.get("payment_intent_id")
            tx.completed_at            = datetime.now(timezone.utc)

        # Update subscription
        sub_result = await db.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        sub = sub_result.scalars().first()
        if sub:
            sub.plan                  = plan
            sub.status                = SubscriptionStatus.active
            sub.provider              = PaymentProvider.stripe
            sub.stripe_customer_id    = data.get("customer_id")
            sub.stripe_subscription_id= data.get("subscription_id")
        else:
            db.add(UserSubscription(
                user_id=user_id,
                plan=plan,
                status=SubscriptionStatus.active,
                provider=PaymentProvider.stripe,
                stripe_customer_id=data.get("customer_id"),
                stripe_subscription_id=data.get("subscription_id"),
            ))

        await db.commit()

    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("subscription_id")
        if stripe_sub_id:
            result = await db.execute(
                select(UserSubscription).where(
                    UserSubscription.stripe_subscription_id == stripe_sub_id
                )
            )
            sub = result.scalars().first()
            if sub:
                sub.status       = SubscriptionStatus.cancelled
                sub.plan         = PlanTier.free
                sub.cancelled_at = datetime.now(timezone.utc)
                await db.commit()

    elif event_type == "invoice.payment_failed":
        stripe_sub_id = data.get("subscription_id")
        if stripe_sub_id:
            result = await db.execute(
                select(UserSubscription).where(
                    UserSubscription.stripe_subscription_id == stripe_sub_id
                )
            )
            sub = result.scalars().first()
            if sub:
                sub.status = SubscriptionStatus.paused
                await db.commit()

    return {"received": True}


# ── GET /payments/stripe/portal ───────────────────────────────────────────────
@router.get("/stripe/portal")
async def stripe_portal(
    return_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a Stripe Customer Portal URL where the user can manage
    their subscription, update payment method, view invoices, or cancel.
    """
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    )
    sub = result.scalars().first()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=404,
            detail="No Stripe subscription found. Use Stripe checkout to subscribe first.",
        )

    url = get_customer_portal_url(sub.stripe_customer_id, return_url)
    return {"portal_url": url}


# ── POST /payments/cancel ─────────────────────────────────────────────────────
@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_user_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel the current user's active subscription.
    Stripe subscriptions are cancelled via the API.
    M-Pesa subscriptions are marked cancelled (manual renewal).
    """
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    )
    sub = result.scalars().first()

    if not sub or sub.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    if sub.provider == PaymentProvider.stripe and sub.stripe_subscription_id:
        try:
            cancel_subscription(sub.stripe_subscription_id)
        except stripe.error.StripeError as exc:
            raise HTTPException(status_code=502, detail=f"Stripe cancellation failed: {exc}")

    sub.status       = SubscriptionStatus.cancelled
    sub.plan         = PlanTier.free
    sub.cancelled_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Subscription cancelled. You have been moved to the Free plan."}
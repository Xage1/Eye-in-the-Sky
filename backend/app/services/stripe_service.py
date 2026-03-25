"""
Stripe integration for Eye in the Sky — card payments and subscriptions.

Implements:
  - Checkout Session creation (hosted Stripe payment page)
  - Webhook event handling (payment success, subscription updates, cancellation)
  - Subscription status sync

Price IDs must be created in your Stripe dashboard and set in .env.
Use test mode price IDs (price_test_...) for development.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import stripe

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# ── Price IDs — create these in your Stripe dashboard ─────────────────────────
# Dashboard → Products → Add Product → Add Price → copy price ID
STRIPE_PRICE_IDS: dict[tuple[str, str], str] = {
    ("pro",     "monthly"): os.getenv("STRIPE_PRICE_PRO_MONTHLY",     ""),
    ("pro",     "yearly"):  os.getenv("STRIPE_PRICE_PRO_YEARLY",      ""),
    ("premium", "monthly"): os.getenv("STRIPE_PRICE_PREMIUM_MONTHLY", ""),
    ("premium", "yearly"):  os.getenv("STRIPE_PRICE_PREMIUM_YEARLY",  ""),
}

# ── Plan amounts in USD cents (for display/logging) ───────────────────────────
PLAN_AMOUNTS_USD = {
    ("pro",     "monthly"): 299,
    ("pro",     "yearly"):  2990,
    ("premium", "monthly"): 499,
    ("premium", "yearly"):  4990,
}


def _get_or_create_customer(user_id: int, email: str, name: str) -> str:
    """
    Find existing Stripe customer by metadata or create a new one.
    Returns the Stripe customer ID.
    """
    existing = stripe.Customer.search(
        query=f'metadata["user_id"]:"{user_id}"'
    )
    if existing.data:
        return existing.data[0].id

    customer = stripe.Customer.create(
        email=email,
        name=name,
        metadata={"user_id": str(user_id)},
    )
    return customer.id


def create_checkout_session(
    user_id: int,
    email: str,
    name: str,
    plan: str,
    interval: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """
    Create a Stripe Checkout Session for subscription.

    Returns checkout URL and session ID.
    The user is redirected to Stripe's hosted payment page.
    On success, Stripe redirects to success_url and fires a webhook.
    """
    price_id = STRIPE_PRICE_IDS.get((plan, interval))
    if not price_id:
        raise ValueError(
            f"No Stripe price ID configured for plan={plan} interval={interval}. "
            "Set STRIPE_PRICE_PRO_MONTHLY etc. in your .env"
        )

    customer_id = _get_or_create_customer(user_id, email, name)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={
            "user_id": str(user_id),
            "plan":    plan,
            "interval": interval,
        },
        subscription_data={
            "metadata": {
                "user_id":  str(user_id),
                "plan":     plan,
                "interval": interval,
            }
        },
        allow_promotion_codes=True,
    )

    logger.info(
        "Stripe checkout created | user=%s plan=%s interval=%s session=%s",
        user_id, plan, interval, session.id,
    )
    return {
        "checkout_url": session.url,
        "session_id":   session.id,
        "customer_id":  customer_id,
    }


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify and construct a Stripe webhook event.
    Raises stripe.error.SignatureVerificationError if invalid.
    """
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)


def parse_webhook_event(event: stripe.Event) -> dict:
    """
    Extract normalised data from a Stripe webhook event.

    Handled event types:
      checkout.session.completed      — one-time payment or subscription start
      customer.subscription.updated   — plan change, renewal
      customer.subscription.deleted   — cancellation
      invoice.payment_failed          — payment failure
    """
    event_type = event["type"]
    data_obj   = event["data"]["object"]

    result = {
        "event_type":       event_type,
        "stripe_event_id":  event["id"],
        "user_id":          None,
        "plan":             None,
        "interval":         None,
        "customer_id":      None,
        "subscription_id":  None,
        "payment_intent_id":None,
        "invoice_id":       None,
        "status":           None,
        "amount":           None,
        "currency":         None,
        "period_start":     None,
        "period_end":       None,
    }

    if event_type == "checkout.session.completed":
        meta = data_obj.get("metadata", {})
        result.update({
            "user_id":          meta.get("user_id"),
            "plan":             meta.get("plan"),
            "interval":         meta.get("interval"),
            "customer_id":      data_obj.get("customer"),
            "subscription_id":  data_obj.get("subscription"),
            "payment_intent_id":data_obj.get("payment_intent"),
            "status":           "completed",
            "amount":           data_obj.get("amount_total"),
            "currency":         data_obj.get("currency"),
        })

    elif event_type in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        meta = data_obj.get("metadata", {})
        result.update({
            "user_id":         meta.get("user_id"),
            "plan":            meta.get("plan"),
            "interval":        meta.get("interval"),
            "customer_id":     data_obj.get("customer"),
            "subscription_id": data_obj.get("id"),
            "status":          data_obj.get("status"),
            "period_start":    data_obj.get("current_period_start"),
            "period_end":      data_obj.get("current_period_end"),
        })

    elif event_type == "invoice.payment_failed":
        result.update({
            "customer_id":      data_obj.get("customer"),
            "subscription_id":  data_obj.get("subscription"),
            "invoice_id":       data_obj.get("id"),
            "amount":           data_obj.get("amount_due"),
            "currency":         data_obj.get("currency"),
            "status":           "failed",
        })

    return result


def cancel_subscription(stripe_subscription_id: str) -> dict:
    """Cancel a Stripe subscription immediately."""
    sub = stripe.Subscription.delete(stripe_subscription_id)
    return {"status": sub.status, "cancelled_at": sub.canceled_at}


def get_customer_portal_url(
    stripe_customer_id: str,
    return_url: str,
) -> str:
    """
    Create a Stripe Customer Portal session URL.
    Lets the user manage their subscription, update payment method, cancel, etc.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url
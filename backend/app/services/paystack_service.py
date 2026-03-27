"""
Paystack payment integration for Eye in the Sky — Kenya.

Supports:
  - Initialize transaction (hosted checkout — M-Pesa, cards, Apple Pay)
  - Verify transaction  (always verify before upgrading subscription)
  - Webhook signature verification and parsing
  - Subscription plan management
  - Charge authorization (recurring payments)

Paystack API docs : https://paystack.com/docs/api
Test cards        : https://paystack.com/docs/payments/test-payments

Environment variables:
  PAYSTACK_SECRET_KEY  — sk_test_xxx (test) or sk_live_xxx (live)
  PAYSTACK_PUBLIC_KEY  — pk_test_xxx (test) or pk_live_xxx (live)
  PAYSTACK_CALLBACK_URL — redirect after hosted checkout
  PAYSTACK_WEBHOOK_URL  — webhook endpoint (ngrok in dev)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
SECRET_KEY    = os.getenv("PAYSTACK_SECRET_KEY", "")
PUBLIC_KEY    = os.getenv("PAYSTACK_PUBLIC_KEY", "")
CALLBACK_URL  = os.getenv("PAYSTACK_CALLBACK_URL", "")
BASE_URL      = "https://api.paystack.co"

# ── Plan pricing in KES (kobo = KES × 100 for Paystack) ──────────────────────
PLAN_PRICES: dict[tuple[str, str], dict] = {
    ("pro",     "monthly"): {"amount_kobo": 29900,  "currency": "KES", "label": "Pro Monthly"},
    ("pro",     "yearly"):  {"amount_kobo": 299000, "currency": "KES", "label": "Pro Yearly"},
    ("premium", "monthly"): {"amount_kobo": 59900,  "currency": "KES", "label": "Premium Monthly"},
    ("premium", "yearly"):  {"amount_kobo": 599000, "currency": "KES", "label": "Premium Yearly"},
}


def _headers() -> dict:
    if not SECRET_KEY:
        raise EnvironmentError("PAYSTACK_SECRET_KEY is not set in .env")
    return {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type":  "application/json",
    }


def _ref(user_id: int, plan: str) -> str:
    """Generate a unique Paystack transaction reference."""
    import uuid
    uid = str(uuid.uuid4()).replace("-", "")[:12].upper()
    return f"EYESKY-{plan.upper()}-{user_id}-{uid}"


# ═════════════════════════════════════════════════════════════════════════════
#  Initialize transaction — hosted checkout
# ═════════════════════════════════════════════════════════════════════════════

async def initialize_transaction(
    user_id: int,
    email: str,
    plan: str,
    interval: str,
    phone: Optional[str] = None,
) -> dict:
    """
    Initialize a Paystack transaction.

    Returns an authorization_url to redirect the user to Paystack's
    hosted checkout page where they can pay with M-Pesa, card, or Apple Pay.

    After payment Paystack redirects to PAYSTACK_CALLBACK_URL with a
    ?reference=xxx query param which you use to verify the transaction.

    Returns:
      authorization_url — redirect the user here
      reference         — store this to verify payment
      access_code       — for Paystack inline JS (optional)
      amount_kes        — human-readable amount in KES
    """
    pricing = PLAN_PRICES.get((plan, interval))
    if not pricing:
        raise ValueError(f"No price configured for plan={plan} interval={interval}")

    reference = _ref(user_id, plan)

    payload: dict = {
        "email":        email,
        "amount":       pricing["amount_kobo"],
        "currency":     pricing["currency"],
        "reference":    reference,
        "callback_url": CALLBACK_URL,
        "metadata": {
            "user_id":    str(user_id),
            "plan":       plan,
            "interval":   interval,
            "cancel_action": CALLBACK_URL + "?cancelled=true",
        },
        "channels": ["card", "mobile_money", "apple_pay"],
    }

    if phone:
        payload["metadata"]["phone"] = phone

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{BASE_URL}/transaction/initialize",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("status"):
        raise RuntimeError(f"Paystack error: {data.get('message')}")

    tx_data = data["data"]
    logger.info(
        "Paystack transaction initialized | user=%s plan=%s ref=%s",
        user_id, plan, reference,
    )

    return {
        "authorization_url": tx_data["authorization_url"],
        "reference":         tx_data["reference"],
        "access_code":       tx_data["access_code"],
        "amount_kes":        pricing["amount_kobo"] // 100,
        "currency":          pricing["currency"],
        "plan":              plan,
        "interval":          interval,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Verify transaction — ALWAYS call this before upgrading subscription
# ═════════════════════════════════════════════════════════════════════════════

async def verify_transaction(reference: str) -> dict:
    """
    Verify a Paystack transaction by its reference.

    Call this:
      1. When the user returns from the hosted checkout (redirect flow)
      2. After receiving a webhook event

    Never trust the redirect URL or webhook payload alone — always verify.

    Returns:
      verified       — True if payment succeeded
      status         — "success" | "failed" | "abandoned" | "pending"
      amount_kes     — amount paid in KES
      channel        — "mobile_money" | "card" | "apple_pay"
      customer_email — payer's email
      customer_phone — payer's phone (if M-Pesa)
      paid_at        — ISO timestamp
      plan           — from metadata
      interval       — from metadata
      user_id        — from metadata
      reference      — transaction reference
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/transaction/verify/{reference}",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("status"):
        raise RuntimeError(f"Paystack verification error: {data.get('message')}")

    tx = data["data"]
    meta = tx.get("metadata", {})

    return {
        "verified":       tx.get("status") == "success",
        "status":         tx.get("status"),
        "amount_kes":     tx.get("amount", 0) // 100,
        "currency":       tx.get("currency"),
        "channel":        tx.get("channel"),
        "reference":      tx.get("reference"),
        "paid_at":        tx.get("paid_at"),
        "customer_email": tx.get("customer", {}).get("email"),
        "customer_phone": tx.get("customer", {}).get("phone"),
        "user_id":        meta.get("user_id"),
        "plan":           meta.get("plan"),
        "interval":       meta.get("interval"),
        "gateway_response": tx.get("gateway_response"),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Webhook verification and parsing
# ═════════════════════════════════════════════════════════════════════════════

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Paystack webhook signature using HMAC-SHA512.
    Paystack sends the signature in the x-paystack-signature header.
    """
    if not SECRET_KEY:
        return False
    expected = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_webhook(body: dict) -> dict:
    """
    Parse a Paystack webhook event.

    Key events for Eye in the Sky:
      charge.success          — payment completed successfully
      subscription.create     — new subscription created
      subscription.not_renew  — subscription cancelled/not renewing
      invoice.payment_failed  — recurring payment failed

    Returns normalised dict with event type and transaction data.
    """
    event   = body.get("event", "")
    tx_data = body.get("data", {})
    meta    = tx_data.get("metadata", {})

    return {
        "event":          event,
        "success":        event == "charge.success",
        "status":         tx_data.get("status"),
        "reference":      tx_data.get("reference"),
        "amount_kes":     tx_data.get("amount", 0) // 100,
        "currency":       tx_data.get("currency"),
        "channel":        tx_data.get("channel"),
        "paid_at":        tx_data.get("paid_at"),
        "customer_email": tx_data.get("customer", {}).get("email"),
        "customer_phone": tx_data.get("customer", {}).get("phone"),
        "user_id":        meta.get("user_id"),
        "plan":           meta.get("plan"),
        "interval":       meta.get("interval"),
        "gateway_response": tx_data.get("gateway_response"),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  List transactions (admin utility)
# ═════════════════════════════════════════════════════════════════════════════

async def list_transactions(page: int = 1, per_page: int = 50) -> dict:
    """Fetch transactions from Paystack dashboard (admin use)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/transaction",
            headers=_headers(),
            params={"page": page, "perPage": per_page},
        )
        resp.raise_for_status()
        return resp.json()
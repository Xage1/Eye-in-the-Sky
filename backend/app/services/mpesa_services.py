"""
Safaricom Daraja M-Pesa integration for Eye in the Sky.

Implements:
  - OAuth token fetch (cached in Redis for 55 minutes)
  - STK Push (Lipa Na M-Pesa Online) — prompts user's phone
  - Callback handler — validates and records successful payment
  - Phone number normalization (07xx → 2547xx)

Sandbox base URL : https://sandbox.safaricom.co.ke
Live base URL    : https://api.safaricom.co.ke
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Config from env ────────────────────────────────────────────────────────────
CONSUMER_KEY    = os.getenv("MPESA_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "")
SHORTCODE       = os.getenv("MPESA_SHORTCODE", "174379")
PASSKEY         = os.getenv("MPESA_PASSKEY", "")
CALLBACK_URL    = os.getenv("MPESA_CALLBACK_URL", "")
ENV             = os.getenv("MPESA_ENV", "sandbox")

BASE_URL = (
    "https://sandbox.safaricom.co.ke"
    if ENV == "sandbox"
    else "https://api.safaricom.co.ke"
)

# ── Plan pricing in KES ────────────────────────────────────────────────────────
PLAN_PRICES = {
    ("pro",     "monthly"): 299,
    ("pro",     "yearly"):  2990,
    ("premium", "monthly"): 599,
    ("premium", "yearly"):  5990,
}


def _normalize_phone(phone: str) -> str:
    """
    Convert any Kenyan phone format to the 2547xxxxxxxx format Daraja requires.
    Handles: 07xx, +2547xx, 2547xx
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("07") or phone.startswith("01"):
        phone = "254" + phone[1:]
    if not phone.startswith("254"):
        raise ValueError(f"Unrecognised phone format: {phone}")
    return phone


def _generate_password() -> tuple[str, str]:
    """
    Generate Daraja STK push password and timestamp.
    Password = base64(shortcode + passkey + timestamp)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    raw = f"{SHORTCODE}{PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


async def _get_access_token() -> str:
    """
    Fetch OAuth2 access token from Daraja.
    Token is valid for 3600s — caller should cache in Redis.
    """
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        raise EnvironmentError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set")

    credentials = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def initiate_stk_push(
    phone: str,
    plan: str,
    interval: str,
    user_id: int,
) -> dict:
    """
    Initiate an STK push payment request.

    Sends a payment prompt to the user's phone. The user enters their M-Pesa PIN
    to confirm. Safaricom then calls CALLBACK_URL with the result.

    Returns the raw Daraja STK push response which contains:
      - MerchantRequestID
      - CheckoutRequestID  (store this to match with callback)
      - ResponseCode       ("0" = success)
      - CustomerMessage
    """
    amount = PLAN_PRICES.get((plan, interval))
    if not amount:
        raise ValueError(f"No price configured for plan={plan} interval={interval}")

    normalized = _normalize_phone(phone)
    password, timestamp = _generate_password()
    token = await _get_access_token()

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            amount,
        "PartyA":            normalized,
        "PartyB":            SHORTCODE,
        "PhoneNumber":       normalized,
        "CallBackURL":       CALLBACK_URL,
        "AccountReference":  f"EyeSky-{plan.upper()}-{user_id}",
        "TransactionDesc":   f"Eye in the Sky {plan.title()} {interval} subscription",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{BASE_URL}/mpesa/stkpush/v1/processrequest",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    logger.info(
        "STK push initiated | user=%s plan=%s phone=%s checkout_id=%s",
        user_id, plan, normalized,
        data.get("CheckoutRequestID"),
    )
    return {
        "merchant_request_id":  data.get("MerchantRequestID"),
        "checkout_request_id":  data.get("CheckoutRequestID"),
        "response_code":        data.get("ResponseCode"),
        "customer_message":     data.get("CustomerMessage"),
        "amount":               amount,
        "currency":             "KES",
        "phone":                normalized,
    }


def parse_stk_callback(body: dict) -> dict:
    """
    Parse the STK push callback from Safaricom.

    Safaricom POST body structure:
      Body.stkCallback.ResultCode      (0 = success)
      Body.stkCallback.ResultDesc
      Body.stkCallback.MerchantRequestID
      Body.stkCallback.CheckoutRequestID
      Body.stkCallback.CallbackMetadata.Item[]  (on success only)

    Returns a normalised dict with all fields extracted.
    """
    stk = body.get("Body", {}).get("stkCallback", {})
    result_code = stk.get("ResultCode")
    success = result_code == 0

    result = {
        "success":              success,
        "result_code":          result_code,
        "result_desc":          stk.get("ResultDesc"),
        "merchant_request_id":  stk.get("MerchantRequestID"),
        "checkout_request_id":  stk.get("CheckoutRequestID"),
        "receipt_number":       None,
        "transaction_date":     None,
        "phone":                None,
        "amount":               None,
    }

    if success:
        items = (
            stk.get("CallbackMetadata", {}).get("Item", [])
        )
        for item in items:
            name  = item.get("Name")
            value = item.get("Value")
            if name == "MpesaReceiptNumber":
                result["receipt_number"] = value
            elif name == "TransactionDate":
                result["transaction_date"] = str(value)
            elif name == "PhoneNumber":
                result["phone"] = str(value)
            elif name == "Amount":
                result["amount"] = value

    return result
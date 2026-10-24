import json
from contextvars import ContextVar
from typing import Any

from langchain.tools import tool
from app.database import SessionLocal
from app.orders import (
    get_order_details,
    check_cancellation_eligibility,
    check_return_eligibility,
    check_damaged_reporting_eligibility,
    get_shipping_and_cod_policy,
)

# Context variable to hold authenticated customer context for the active agent invocation
active_customer_id: ContextVar[int | None] = ContextVar("active_customer_id", default=None)


def set_active_customer(customer_id: int | None) -> Any:
    """Set the authenticated customer ID for the active agent invocation."""
    return active_customer_id.set(customer_id)


def reset_active_customer(token: Any) -> None:
    """Reset the customer context after invocation."""
    active_customer_id.reset(token)


@tool
def lookup_customer_order(order_id: str) -> str:
    """Look up a customer's order by order ID.

    Use this tool when a customer asks about order status,
    product details, amount, courier tracking number, or delivery estimates.
    Enforces that customers can only view their own orders when authenticated.
    """
    if not order_id or not order_id.strip():
        return json.dumps({"success": False, "error": "Please provide your order ID, for example ORD-101."})

    try:
        cid = active_customer_id.get()
        with SessionLocal() as db:
            result = get_order_details(order_id, db, customer_id=cid)

        return json.dumps(result, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {"success": False, "error": "Order lookup is temporarily unavailable."}
        )


@tool
def check_cancellation_eligibility_tool(order_id: str) -> str:
    """Check if an order is eligible for cancellation according to Aura Skincare policy.

    Policy:
    - Cancellation is allowed only while the order status is Processing.
    - Shipped and Out for Delivery orders cannot be cancelled; customers may refuse delivery at the doorstep.
    - Delivered orders cannot be cancelled (return policy applies instead).
    - NEVER claim an order was cancelled unless confirmed.
    """
    if not order_id or not order_id.strip():
        return json.dumps({"success": False, "eligible": False, "error": "Please provide your order ID, for example ORD-103."})

    try:
        cid = active_customer_id.get()
        with SessionLocal() as db:
            result = check_cancellation_eligibility(order_id, db, customer_id=cid)

        return json.dumps(result, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {"success": False, "eligible": False, "error": "Cancellation check is temporarily unavailable."}
        )


@tool
def check_return_eligibility_tool(
    order_id: str,
    is_opened: bool | None = None,
    is_used: bool | None = None,
    in_original_packaging: bool | None = None,
    delivered_days_ago: int | None = None,
) -> str:
    """Check if an order is eligible for return according to Aura Skincare policy.

    Policy:
    - Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.
    - Orders not yet delivered cannot be returned.
    - If opened, used, or missing original packaging, returns are not accepted.
    - If product condition is unknown, ask the customer before making a final determination.
    """
    if not order_id or not order_id.strip():
        return json.dumps({"success": False, "eligible": False, "error": "Please provide your order ID, for example ORD-102."})

    try:
        cid = active_customer_id.get()
        with SessionLocal() as db:
            result = check_return_eligibility(
                order_id=order_id,
                db=db,
                customer_id=cid,
                is_opened=is_opened,
                is_used=is_used,
                in_original_packaging=in_original_packaging,
                delivered_days_ago=delivered_days_ago,
            )

        return json.dumps(result, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {"success": False, "eligible": False, "error": "Return eligibility check is temporarily unavailable."}
        )


@tool
def check_damaged_reporting_eligibility_tool(
    order_id: str,
    has_photos: bool | None = None,
    delivered_days_ago: int | None = None,
    delivered_hours_ago: float | None = None,
) -> str:
    """Check if a damaged or defective product is eligible for replacement.

    Policy:
    - Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.
    - If reported after 48 hours, replacement is not eligible under this policy.
    - Photos of the damaged/defective product and packaging are required. If not yet provided, ask the customer.
    """
    if not order_id or not order_id.strip():
        return json.dumps({"success": False, "eligible": False, "error": "Please provide your order ID, for example ORD-106."})

    try:
        cid = active_customer_id.get()
        with SessionLocal() as db:
            result = check_damaged_reporting_eligibility(
                order_id=order_id,
                db=db,
                customer_id=cid,
                has_photos=has_photos,
                delivered_days_ago=delivered_days_ago,
                delivered_hours_ago=delivered_hours_ago,
            )

        return json.dumps(result, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {"success": False, "eligible": False, "error": "Damaged product check is temporarily unavailable."}
        )


@tool
def get_shipping_and_cod_policy_tool(
    order_amount: float | None = None,
    order_id: str | None = None,
) -> str:
    """Get Aura Skincare's exact shipping fee, delivery timeline, and COD availability policies.

    Policy:
    - Free shipping for orders above ₹499.
    - Orders below ₹499 have a ₹50 shipping fee.
    - Standard delivery takes 3–5 business days.
    - Cash on Delivery (COD) is available for orders up to ₹2,500, payable by cash or UPI.
    - Orders exceeding ₹2,500 are not eligible for COD.
    """
    try:
        cid = active_customer_id.get()
        with SessionLocal() as db:
            result = get_shipping_and_cod_policy(
                order_amount=order_amount,
                order_id=order_id,
                db=db,
                customer_id=cid,
            )

        return json.dumps(result, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {"success": False, "error": "Shipping and payment policy is temporarily unavailable."}
        )

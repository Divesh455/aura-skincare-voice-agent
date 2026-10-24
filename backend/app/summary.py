import re
from typing import Any


def classify_and_summarize_call(
    messages: list[dict[str, Any]], customer_name: str
) -> dict[str, Any]:
    """
    Produce a structured call summary and determine whether the interaction
    meets the importance criteria for PostgreSQL database persistence.

    Rules-based evaluation avoids unnecessary LLM latency while guaranteeing
    that complaints, damaged goods, cancellations, and order issues are never lost.
    Customer intent is extracted from what the customer actually communicated,
    preventing assistant greetings or boilerplate offers of help from causing false positives.
    """
    customer_messages = [m["content"] for m in messages if m.get("role") == "user"]
    assistant_messages = [
        m["content"] for m in messages if m.get("role") == "assistant"
    ]

    all_customer_text = " ".join(customer_messages).lower().strip()
    all_combined_text = " ".join([m.get("content", "") for m in messages]).lower()

    # 1. Order ID Detection (check customer messages first, then combined)
    order_match = re.search(r"\bORD-\d+\b", " ".join(customer_messages), re.IGNORECASE)
    if not order_match:
        order_match = re.search(r"\bORD-\d+\b", " ".join([m.get("content", "") for m in messages]), re.IGNORECASE)
    order_id = order_match.group(0).upper() if order_match else None

    # Fallback: numeric reference when preceded by order keyword
    if not order_id:
        num_match = re.search(r"(?:order|order id|ord)\s*(?:#|no\.?)?\s*(\d{3,})", all_customer_text)
        if num_match:
            order_id = f"ORD-{num_match.group(1)}"

    # 2. Intent and Importance Classification (Evaluated from Customer Speech)
    is_important = False
    requires_human_support = False
    customer_intent = "General Skincare Inquiry"
    important_details = "Customer discussed skincare advice or routine guidance."

    # A. Damaged or Defective Items
    if any(
        kw in all_customer_text
        for kw in ["damaged", "broken", "leaking", "leak", "spilled", "defective", "spoiled", "bad product", "wrong item"]
    ):
        is_important = True
        requires_human_support = True
        customer_intent = "Damaged or Defective Product Report"
        important_details = (
            f"Customer reported damaged or defective item related to order {order_id or 'unspecified'}."
        )

    # B. Cancellation Requests
    elif any(
        kw in all_customer_text
        for kw in ["cancel", "cancellation", "stop my order", "dont want order", "don't want order"]
    ):
        is_important = True
        customer_intent = "Order Cancellation Request"
        important_details = f"Request to cancel order {order_id or 'unspecified'}."

    # C. Return or Refund Requests
    elif any(
        kw in all_customer_text
        for kw in ["return", "refund", "exchange", "money back"]
    ):
        is_important = True
        customer_intent = "Return or Refund Request"
        important_details = f"Customer initiated inquiry regarding returns or refund for order {order_id or 'unspecified'}."

    # D. Complaints & Human Escalation
    elif any(
        kw in all_customer_text
        for kw in [
            "complaint",
            "angry",
            "terrible",
            "horrible",
            "frustrated",
            "unhappy",
            "bad service",
            "speak to human",
            "speak to an agent",
            "talk to a person",
            "representative",
            "manager",
            "callback",
            "call me back",
            "human assistance",
        ]
    ):
        is_important = True
        requires_human_support = True
        customer_intent = "Customer Complaint / Escalation"
        important_details = "Customer requested human support or escalated an unresolved complaint."

    # E. Delivery Delays or Tracking Issues
    elif any(
        kw in all_customer_text
        for kw in ["delayed", "delay", "late", "not delivered", "lost package", "tracking issue", "courier issue"]
    ):
        is_important = True
        customer_intent = "Delivery Inquiries / Tracking Issue"
        important_details = f"Inquiry regarding shipment delivery delay or courier tracking for order {order_id or 'unspecified'}."

    # F. Specific Order Status Inquiry
    elif order_id or any(kw in all_customer_text for kw in ["my order", "check order", "order status", "track order", "track my", "where is"]):
        is_important = True
        customer_intent = "Order Status Inquiry"
        important_details = f"Inquiry regarding status and details of order {order_id or 'unspecified'}."

    # G. Routine Pleasantries / General Skincare (Excluded from DB persistence)
    else:
        is_important = False
        customer_intent = "Routine Greeting / General Skincare Advice"
        important_details = "Routine pleasantries or product guidance; no escalation or order tracking required."

    # 3. Resolution Status
    latest_reply = assistant_messages[-1].lower() if assistant_messages else ""

    if requires_human_support:
        resolution_status = "unresolved"
    elif any(
        kw in latest_reply
        for kw in [
            "couldn't find",
            "could not find",
            "does not belong",
            "at capacity",
            "high demand",
            "momentarily",
            "temporarily unavailable",
        ]
    ):
        resolution_status = "unresolved"
        # If Aria couldn't resolve an order inquiry, mark important to prevent lost support cases
        if order_id:
            is_important = True
            requires_human_support = True
    elif any(
        kw in latest_reply
        for kw in ["out for delivery", "delivered", "processing", "arriving", "tracked", "policy"]
    ):
        resolution_status = "resolved"
    else:
        resolution_status = "resolved" if not is_important else "unresolved"

    # 4. Synthesize Concise Summary
    first_query = customer_messages[0] if customer_messages else "No customer request recorded"
    summary_text = (
        f"Customer {customer_name} inquired about: '{first_query}'. "
        f"Resolution: {resolution_status}. "
        f"{'Human support required.' if requires_human_support else 'Handled automatically by Aria.'}"
    )

    return {
        "is_important": is_important,
        "customer_intent": customer_intent,
        "order_id": order_id,
        "resolution_status": resolution_status,
        "call_summary": summary_text,
        "important_details": important_details,
        "requires_human_support": requires_human_support,
    }

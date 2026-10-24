from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Order
from app.auth import hash_password


def get_customer_orders(customer_id: int, db: Session) -> list[dict]:
    """
    Retrieve all orders belonging to a specific authenticated customer.
    Guarantees isolation so customers only see their own orders.
    """
    statement = (
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.id.asc())
    )
    orders = db.scalars(statement).all()
    return [
        {
            "order_id": o.order_id,
            "product_name": o.product_name,
            "amount": o.amount,
            "status": o.status,
            "courier": o.courier,
            "tracking_number": o.tracking_number,
            "expected_delivery": o.expected_delivery,
            "ordered_at": o.ordered_at.isoformat() if o.ordered_at else None,
            "delivered_days_ago": o.delivered_days_ago,
            "items_summary": o.items_summary,
        }
        for o in orders
    ]


def _format_account_mismatch_error(normalized_id: str, customer_id: int, db: Session) -> dict:
    """Format a secure, helpful account mismatch response providing the customer's own orders."""
    own_orders = db.scalars(
        select(Order.order_id).where(Order.customer_id == customer_id)
    ).all()
    orders_text = ", ".join(own_orders) if own_orders else "none"
    return {
        "success": False,
        "eligible": False,
        "is_account_mismatch": True,
        "error": f"Order {normalized_id} does not belong to your account.",
        "message": (
            f"For customer privacy and account security, order {normalized_id} does not belong to your account. "
            f"Your registered order(s) under this account are: {orders_text}. "
            f"Please verify your order ID, or check if you placed the order with a different email/phone."
        ),
        "customer_orders": own_orders,
        "order_id": normalized_id,
    }


def get_order_details(order_id: str, db: Session, customer_id: int | None = None) -> dict:
    """
    Look up an order by its order ID.
    If customer_id is provided, enforces that the order belongs to this customer.

    Returns a dictionary suitable for the API and LangChain agent.
    """
    if not order_id or not order_id.strip():
        return {
            "success": False,
            "error": "Please provide your order ID, for example ORD-101.",
        }

    normalized_id = order_id.strip().upper()

    statement = select(Order).where(Order.order_id == normalized_id)
    order = db.scalar(statement)

    if order is None:
        return {
            "success": False,
            "error": (
                f"I couldn't find order {normalized_id}. "
                "Please check the order ID and try again."
            ),
        }

    # If customer_id is supplied, verify ownership to prevent IDOR attacks
    if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
        return _format_account_mismatch_error(normalized_id, customer_id, db)

    return {
        "success": True,
        "order": {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "customer_name": order.customer_name,
            "product_name": order.product_name,
            "amount": order.amount,
            "status": order.status,
            "courier": order.courier,
            "tracking_number": order.tracking_number,
            "expected_delivery": order.expected_delivery,
            "ordered_at": (
                order.ordered_at.isoformat() if order.ordered_at else None
            ),
            "delivered_days_ago": order.delivered_days_ago,
            "items_summary": order.items_summary,
        },
    }


def check_cancellation_eligibility(
    order_id: str,
    db: Session,
    customer_id: int | None = None,
) -> dict:
    """
    Deterministically evaluates whether an order can be cancelled based on Aura Skincare policy:
    - Cancellation is allowed only while the order status is Processing.
    - Shipped and Out for Delivery orders cannot be cancelled; customers may refuse delivery at the doorstep.
    """
    if not order_id or not str(order_id).strip():
        return {
            "success": False,
            "eligible": False,
            "error": "Please provide your order ID, for example ORD-103.",
            "order_id": None,
        }

    normalized_id = str(order_id).strip().upper()
    order = db.scalar(select(Order).where(Order.order_id == normalized_id))

    if order is None:
        return {
            "success": False,
            "eligible": False,
            "error": f"I couldn't find order {normalized_id}. Please check the order ID and try again.",
            "order_id": normalized_id,
        }

    if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
        return _format_account_mismatch_error(normalized_id, customer_id, db)

    status = (order.status or "").strip()
    status_lower = status.lower()

    if status_lower == "processing":
        return {
            "success": True,
            "eligible": True,
            "order_id": order.order_id,
            "status": status,
            "message": f"Order {order.order_id} is currently Processing and is eligible for cancellation.",
            "policy_note": "Cancellation is allowed only while the order status is Processing.",
        }

    if status_lower in ["shipped", "out for delivery", "in transit"]:
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "reason": f"Order {order.order_id} is {status} and cannot be cancelled once dispatched.",
            "doorstep_refusal_allowed": True,
            "message": (
                f"Order {order.order_id} is currently {status} and cannot be cancelled. "
                "However, you may refuse delivery at the doorstep when the courier arrives."
            ),
            "policy_note": "Shipped and Out for Delivery orders cannot be cancelled; customers may refuse delivery at the doorstep.",
        }

    if status_lower == "delivered":
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "reason": f"Order {order.order_id} has already been delivered and cannot be cancelled.",
            "message": f"Order {order.order_id} has already been delivered and cannot be cancelled. You may check return eligibility instead.",
            "policy_note": "Cancellation is allowed only while the order status is Processing.",
        }

    if status_lower == "cancelled":
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "reason": f"Order {order.order_id} has already been cancelled.",
            "message": f"Order {order.order_id} has already been cancelled.",
            "policy_note": "Cancellation is allowed only while the order status is Processing.",
        }

    return {
        "success": True,
        "eligible": False,
        "order_id": order.order_id,
        "status": status,
        "reason": f"Order {order.order_id} status is '{status}'. Cancellation is allowed only while the order status is Processing.",
        "message": f"Order {order.order_id} cannot be cancelled because its status is '{status}'.",
        "policy_note": "Cancellation is allowed only while the order status is Processing.",
    }


def check_return_eligibility(
    order_id: str,
    db: Session,
    customer_id: int | None = None,
    is_opened: bool | None = None,
    is_used: bool | None = None,
    in_original_packaging: bool | None = None,
    delivered_days_ago: int | None = None,
) -> dict:
    """
    Deterministically evaluates whether an order can be returned based on Aura Skincare policy:
    - Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.
    """
    if not order_id or not str(order_id).strip():
        return {
            "success": False,
            "eligible": False,
            "error": "Please provide your order ID, for example ORD-102.",
            "order_id": None,
        }

    normalized_id = str(order_id).strip().upper()
    order = db.scalar(select(Order).where(Order.order_id == normalized_id))

    if order is None:
        return {
            "success": False,
            "eligible": False,
            "error": f"I couldn't find order {normalized_id}. Please check the order ID and try again.",
            "order_id": normalized_id,
        }

    if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
        return _format_account_mismatch_error(normalized_id, customer_id, db)

    status = (order.status or "").strip()
    if status.lower() != "delivered":
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "reason": f"Order {order.order_id} has not been delivered yet (current status: {status}). Returns are only accepted after delivery.",
            "message": f"Order {order.order_id} is currently {status}. Returns can only be requested after the order has been delivered.",
            "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
        }

    # Delivery time window evaluation (7 days)
    days_ago = delivered_days_ago if delivered_days_ago is not None else order.delivered_days_ago

    if days_ago is None:
        return {
            "success": True,
            "eligible": None,
            "missing_info": ["delivered_days_ago"],
            "order_id": order.order_id,
            "status": status,
            "message": f"Order {order.order_id} is marked Delivered, but the delivery date is not recorded. Could you please confirm how many days ago it was delivered?",
            "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
        }

    if days_ago > 7:
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "delivered_days_ago": days_ago,
            "reason": f"Order was delivered {days_ago} days ago, exceeding the 7-day return window.",
            "message": f"Order {order.order_id} is not eligible for return because it was delivered {days_ago} days ago, which exceeds our 7-day return window.",
            "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
        }

    # Within 7 days window: check product condition
    violations = []
    if is_opened is True:
        violations.append("opened")
    if is_used is True:
        violations.append("used")
    if in_original_packaging is False:
        violations.append("not in original packaging")

    if violations:
        violation_str = ", ".join(violations)
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "delivered_days_ago": days_ago,
            "reason": f"Product is {violation_str}. Returns are accepted only for unopened, unused products in original packaging.",
            "message": f"Order {order.order_id} cannot be returned because returns are accepted only for unopened, unused products in their original packaging.",
            "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
        }

    # If condition is explicitly verified as meeting policy
    if is_opened is False and is_used is False and in_original_packaging is True:
        return {
            "success": True,
            "eligible": True,
            "order_id": order.order_id,
            "status": status,
            "delivered_days_ago": days_ago,
            "message": f"Order {order.order_id} is eligible for return. It was delivered {days_ago} days ago and is unopened, unused, and in its original packaging.",
            "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
        }

    # Missing condition information: ask customer to verify
    missing_fields = []
    if is_opened is None:
        missing_fields.append("is_opened")
    if is_used is None:
        missing_fields.append("is_used")
    if in_original_packaging is None:
        missing_fields.append("in_original_packaging")

    return {
        "success": True,
        "eligible": None,
        "missing_info": missing_fields,
        "order_id": order.order_id,
        "status": status,
        "delivered_days_ago": days_ago,
        "message": f"Order {order.order_id} was delivered {days_ago} days ago and is within the 7-day return window. To confirm return eligibility, could you please confirm if the product is unopened, unused, and in its original packaging?",
        "policy_note": "Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.",
    }


def check_damaged_reporting_eligibility(
    order_id: str,
    db: Session,
    customer_id: int | None = None,
    has_photos: bool | None = None,
    delivered_days_ago: int | None = None,
    delivered_hours_ago: float | None = None,
) -> dict:
    """
    Deterministically evaluates eligibility for damaged/defective product reporting based on Aura Skincare policy:
    - Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.
    """
    if not order_id or not str(order_id).strip():
        return {
            "success": False,
            "eligible": False,
            "error": "Please provide your order ID, for example ORD-106.",
            "order_id": None,
        }

    normalized_id = str(order_id).strip().upper()
    order = db.scalar(select(Order).where(Order.order_id == normalized_id))

    if order is None:
        return {
            "success": False,
            "eligible": False,
            "error": f"I couldn't find order {normalized_id}. Please check the order ID and try again.",
            "order_id": normalized_id,
        }

    if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
        return _format_account_mismatch_error(normalized_id, customer_id, db)

    status = (order.status or "").strip()
    if status.lower() != "delivered":
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "reason": f"Order {order.order_id} has not been delivered yet (current status: {status}). Damaged product replacement applies after delivery.",
            "message": f"Order {order.order_id} is currently {status} and has not been delivered yet.",
            "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
        }

    # Determine hours since delivery
    if delivered_hours_ago is not None:
        hours_ago = float(delivered_hours_ago)
    elif delivered_days_ago is not None:
        hours_ago = float(delivered_days_ago) * 24.0
    elif order.delivered_days_ago is not None:
        hours_ago = float(order.delivered_days_ago) * 24.0
    else:
        hours_ago = None

    if hours_ago is None:
        return {
            "success": True,
            "eligible": None,
            "missing_info": ["delivered_time"],
            "order_id": order.order_id,
            "status": status,
            "message": f"Order {order.order_id} is marked Delivered, but the delivery time is not recorded. Could you please confirm when the order was delivered (within 48 hours)?",
            "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
        }

    if hours_ago > 48.0:
        time_text = f"{int(hours_ago // 24)} days" if hours_ago >= 24 else f"{hours_ago:.0f} hours"
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "hours_since_delivery": hours_ago,
            "reason": f"Reported {time_text} after delivery, which exceeds the 48-hour reporting window.",
            "message": f"Order {order.order_id} is not eligible for damaged/defective replacement because it was delivered {time_text} ago, exceeding our 48-hour reporting window.",
            "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
        }

    # Within 48 hours: check photos requirement
    if has_photos is True:
        return {
            "success": True,
            "eligible": True,
            "order_id": order.order_id,
            "status": status,
            "hours_since_delivery": hours_ago,
            "has_photos": True,
            "message": f"Order {order.order_id} is eligible for a replacement. It was reported within 48 hours of delivery and photos have been provided.",
            "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
        }

    if has_photos is False:
        return {
            "success": True,
            "eligible": False,
            "order_id": order.order_id,
            "status": status,
            "hours_since_delivery": hours_ago,
            "has_photos": False,
            "reason": "Photos of the damaged or defective product are required for replacement.",
            "message": f"Order {order.order_id} was reported within 48 hours of delivery, but photos of the damaged or defective product are required to process a replacement. Please share clear photos.",
            "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
        }

    # has_photos is None: ask customer for photos
    return {
        "success": True,
        "eligible": None,
        "missing_info": ["photos"],
        "order_id": order.order_id,
        "status": status,
        "hours_since_delivery": hours_ago,
        "message": f"Order {order.order_id} was delivered within the 48-hour reporting window. To process a replacement, could you please provide photos of the damaged or defective product?",
        "policy_note": "Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.",
    }


def get_shipping_and_cod_policy(
    order_amount: int | float | None = None,
    order_id: str | None = None,
    db: Session | None = None,
    customer_id: int | None = None,
) -> dict:
    """
    Evaluates shipping fees, delivery timeline, and COD availability according to Aura Skincare policy:
    - Free shipping for orders above ₹499.
    - Orders below ₹499 have a ₹50 shipping fee.
    - Standard delivery takes 3–5 business days.
    - COD is available for orders up to ₹2,500, payable by cash or UPI.
    """
    resolved_amount = None
    if order_amount is not None:
        try:
            resolved_amount = float(order_amount)
        except (ValueError, TypeError):
            pass

    if resolved_amount is None and order_id and db:
        normalized_id = str(order_id).strip().upper()
        order = db.scalar(select(Order).where(Order.order_id == normalized_id))
        if order and (customer_id is None or order.customer_id is None or order.customer_id == customer_id):
            resolved_amount = float(order.amount)

    policy_rules = {
        "free_shipping_threshold": 499,
        "standard_shipping_fee": 50,
        "standard_delivery_timeline": "3–5 business days",
        "cod_maximum_limit": 2500,
        "cod_payment_methods": ["Cash", "UPI"],
    }

    if resolved_amount is None:
        return {
            "success": True,
            "policy": policy_rules,
            "message": (
                "Aura Skincare shipping & payment policies: Free shipping for orders above ₹499 "
                "(orders below ₹499 have a ₹50 shipping fee). Standard delivery takes 3–5 business days. "
                "Cash on Delivery (COD) is available for orders up to ₹2,500, payable by cash or UPI."
            ),
        }

    is_free_shipping = resolved_amount > 499
    shipping_fee = 0 if is_free_shipping else 50
    cod_available = resolved_amount <= 2500

    return {
        "success": True,
        "order_amount": resolved_amount,
        "free_shipping": is_free_shipping,
        "shipping_fee": shipping_fee,
        "delivery_timeline": "3–5 business days",
        "cod_available": cod_available,
        "cod_payment_methods": ["Cash", "UPI"] if cod_available else [],
        "message": (
            f"For an order of ₹{resolved_amount:.0f}: "
            f"{'Free shipping applies (orders above ₹499).' if is_free_shipping else 'A ₹50 shipping fee applies (orders below ₹499).'} "
            f"Standard delivery takes 3–5 business days. "
            f"{'Cash on Delivery (COD) is available up to ₹2,500, payable by cash or UPI.' if cod_available else 'Cash on Delivery (COD) is not available for orders above ₹2,500.'}"
        ),
        "policy": policy_rules,
    }


def seed_orders(db: Session) -> None:
    """Insert assignment mock customers and orders if they aren't present."""
    # 1. Seed mock customers
    mock_customers = [
        {
            "full_name": "Priya Sharma",
            "email": "priya@example.com",
            "password": "Password123!",
        },
        {
            "full_name": "Rahul Verma",
            "email": "rahul@example.com",
            "password": "Password123!",
        },
        {
            "full_name": "Ananya Patel",
            "email": "ananya@example.com",
            "password": "Password123!",
        },
        {
            "full_name": "Divesh Matkar",
            "email": "matkardivesh26@gmail.com",
            "password": "Password123!",
        },
        {
            "full_name": "Sneha Kapoor",
            "email": "sneha@example.com",
            "password": "Password123!",
        },
        {
            "full_name": "Rohan Mehta",
            "email": "rohan@example.com",
            "password": "Password123!",
        },
        {
            "full_name": "Kavita Nair",
            "email": "kavita@example.com",
            "password": "Password123!",
        },
    ]

    customer_map = {}
    for item in mock_customers:
        existing = db.scalar(select(Customer).where(Customer.email == item["email"]))
        if not existing:
            customer = Customer(
                full_name=item["full_name"],
                email=item["email"],
                hashed_password=hash_password(item["password"]),
            )
            db.add(customer)
            db.flush()
            customer_map[item["full_name"]] = customer.id
        else:
            customer_map[item["full_name"]] = existing.id
            # Ensure known test password for seeded users
            existing.hashed_password = hash_password(item["password"])

    db.commit()

    # 2. Seed mock orders
    sample_orders = [
        {
            "order_id": "ORD-101",
            "customer_id": customer_map.get("Priya Sharma"),
            "customer_name": "Priya Sharma",
            "product_name": "Vitamin C Serum (30ml)",
            "amount": 699,
            "status": "Out for Delivery",
            "courier": "BlueDart",
            "tracking_number": "BD-982103",
            "expected_delivery": "by 6 PM today",
            "items_summary": "Vitamin C Serum (30ml)",
        },
        {
            "order_id": "ORD-102",
            "customer_id": customer_map.get("Rahul Verma"),
            "customer_name": "Rahul Verma",
            "product_name": "Hydrating Sunscreen SPF 50",
            "amount": 499,
            "status": "Delivered",
            "courier": "Delhivery",
            "tracking_number": "DL-441029",
            "expected_delivery": None,
            "delivered_days_ago": 14,
            "items_summary": "Hydrating Sunscreen SPF 50",
        },
        {
            "order_id": "ORD-103",
            "customer_id": customer_map.get("Ananya Patel"),
            "customer_name": "Ananya Patel",
            "product_name": "Green Tea Face Wash + Toner",
            "amount": 850,
            "status": "Processing",
            "courier": None,
            "tracking_number": None,
            "expected_delivery": "in 2-3 business days",
            "items_summary": "Green Tea Face Wash + Toner",
        },
        {
            "order_id": "ORD-104",
            "customer_id": customer_map.get("Divesh Matkar"),
            "customer_name": "Divesh Matkar",
            "product_name": "Niacinamide 10% Glow Serum + B5 Moisturizer",
            "amount": 1199,
            "status": "Out for Delivery",
            "courier": "BlueDart",
            "tracking_number": "BD-771920",
            "expected_delivery": "by 6 PM today",
            "items_summary": "Niacinamide 10% Glow Serum, B5 Moisturizer (50ml)",
        },
        {
            "order_id": "ORD-105",
            "customer_id": customer_map.get("Sneha Kapoor"),
            "customer_name": "Sneha Kapoor",
            "product_name": "Hyaluronic Acid Deep Moisture Gel",
            "amount": 649,
            "status": "In Transit",
            "courier": "Delhivery",
            "tracking_number": "DL-883102",
            "expected_delivery": "Tomorrow by 2 PM",
            "items_summary": "Hyaluronic Acid Deep Moisture Gel (50g)",
        },
        {
            "order_id": "ORD-106",
            "customer_id": customer_map.get("Rohan Mehta"),
            "customer_name": "Rohan Mehta",
            "product_name": "Salicylic Acid Pore Minimizing Cleanser",
            "amount": 499,
            "status": "Delivered",
            "courier": "DTDC",
            "tracking_number": "DT-441209",
            "expected_delivery": None,
            "delivered_days_ago": 2,
            "items_summary": "Salicylic Acid 2% Cleanser (150ml)",
        },
        {
            "order_id": "ORD-107",
            "customer_id": customer_map.get("Kavita Nair"),
            "customer_name": "Kavita Nair",
            "product_name": "Retinol 0.5% Night Repair Cream",
            "amount": 999,
            "status": "Processing",
            "courier": None,
            "tracking_number": None,
            "expected_delivery": "in 3-4 business days",
            "items_summary": "Retinol 0.5% Night Repair Cream (30ml)",
        },
    ]

    for item in sample_orders:
        existing_order = db.scalar(select(Order).where(Order.order_id == item["order_id"]))
        if not existing_order:
            db.add(Order(**item))
        else:
            # Update customer_id if it was not linked previously
            if existing_order.customer_id is None and item["customer_id"] is not None:
                existing_order.customer_id = item["customer_id"]

    db.commit()

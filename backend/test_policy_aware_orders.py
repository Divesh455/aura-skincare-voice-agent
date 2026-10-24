"""
Policy-Aware Order Support Test Suite
Validates all deterministic eligibility rules and tools according to Aura Skincare policies:
1. Free shipping for orders above ₹499; orders below ₹499 have a ₹50 shipping fee.
2. Standard delivery takes 3–5 business days.
3. Returns are accepted within 7 days of delivery for unopened, unused products in original packaging.
4. Damaged/defective products must be reported within 48 hours of delivery with photos for replacement.
5. Cancellation is allowed only while the order status is Processing.
6. Shipped and Out for Delivery orders cannot be cancelled; customers may refuse delivery at the doorstep.
7. COD is available for orders up to ₹2,500, payable by cash or UPI.
8. Deterministic Python enforcement (no LLM hallucinations).
9. Missing information prompts.
10. IDOR and customer privacy protection.
11. Preserved get_order_details(order_id) compatibility.
"""

import json
import sys

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select
from app.database import SessionLocal
from app.models import Customer, Order
from app.orders import (
    get_order_details,
    check_cancellation_eligibility,
    check_return_eligibility,
    check_damaged_reporting_eligibility,
    get_shipping_and_cod_policy,
    seed_orders,
)
from app.ai_tools import (
    active_customer_id,
    lookup_customer_order,
    check_cancellation_eligibility_tool,
    check_return_eligibility_tool,
    check_damaged_reporting_eligibility_tool,
    get_shipping_and_cod_policy_tool,
)


def run_all_tests():
    print("=" * 70)
    print("STARTING POLICY-AWARE ORDER SUPPORT TEST SUITE")
    print("=" * 70)

    with SessionLocal() as db:
        # Ensure database is seeded with test orders
        seed_orders(db)

        # Retrieve mock customer IDs
        priya = db.scalar(select(Customer).where(Customer.email == "priya@example.com"))
        rahul = db.scalar(select(Customer).where(Customer.email == "rahul@example.com"))
        ananya = db.scalar(select(Customer).where(Customer.email == "ananya@example.com"))
        rohan = db.scalar(select(Customer).where(Customer.email == "rohan@example.com"))

        assert priya and rahul and ananya and rohan, "Mock customers missing from database"
        print("[PASS] Verified mock customer accounts (Priya, Rahul, Ananya, Rohan)")

        # ---------------------------------------------------------------------
        # 1. PRESERVE get_order_details() FUNCTIONALITY
        # ---------------------------------------------------------------------
        print("\n--- Testing Preserved get_order_details() Functionality ---")
        res = get_order_details("ORD-101", db)
        assert res["success"] is True
        assert res["order"]["order_id"] == "ORD-101"
        assert res["order"]["customer_name"] == "Priya Sharma"
        assert res["order"]["status"] == "Out for Delivery"
        print("[PASS] get_order_details('ORD-101') returned full order payload")

        # Invalid order ID
        res_invalid = get_order_details("ORD-999", db)
        assert res_invalid["success"] is False
        assert "couldn't find order" in res_invalid["error"].lower()
        print("[PASS] get_order_details('ORD-999') handled invalid ID safely")

        # Empty order ID
        res_empty = get_order_details("", db)
        assert res_empty["success"] is False
        assert "provide your order id" in res_empty["error"].lower()
        print("[PASS] get_order_details('') handled empty string safely")

        # IDOR check on get_order_details
        res_idor = get_order_details("ORD-101", db, customer_id=rahul.id)
        assert res_idor["success"] is False
        assert "does not belong" in res_idor["error"].lower()
        print("[PASS] get_order_details enforces IDOR customer ownership")

        # ---------------------------------------------------------------------
        # 2. CANCELLATION ELIGIBILITY TESTS
        # ---------------------------------------------------------------------
        print("\n--- Testing Cancellation Eligibility Policy ---")
        # Eligible: Status is "Processing" (ORD-103 belongs to Ananya)
        res_cancel_eligible = check_cancellation_eligibility("ORD-103", db, customer_id=ananya.id)
        assert res_cancel_eligible["success"] is True
        assert res_cancel_eligible["eligible"] is True
        assert "eligible for cancellation" in res_cancel_eligible["message"].lower()
        assert res_cancel_eligible["status"] == "Processing"
        print("[PASS] Eligible cancellation: ORD-103 (Processing) -> eligible=True")

        # Ineligible: Status is "Out for Delivery" (ORD-101 belongs to Priya)
        res_cancel_out = check_cancellation_eligibility("ORD-101", db, customer_id=priya.id)
        assert res_cancel_out["success"] is True
        assert res_cancel_out["eligible"] is False
        assert res_cancel_out["doorstep_refusal_allowed"] is True
        assert "refuse delivery at the doorstep" in res_cancel_out["message"].lower()
        print("[PASS] Ineligible cancellation: ORD-101 (Out for Delivery) -> eligible=False with doorstep refusal instruction")

        # Ineligible: Status is "In Transit" (ORD-105)
        res_cancel_transit = check_cancellation_eligibility("ORD-105", db)
        assert res_cancel_transit["success"] is True
        assert res_cancel_transit["eligible"] is False
        assert "refuse delivery at the doorstep" in res_cancel_transit["message"].lower()
        print("[PASS] Ineligible cancellation: ORD-105 (In Transit) -> eligible=False with doorstep refusal instruction")

        # Ineligible: Status is "Delivered" (ORD-102 belongs to Rahul)
        res_cancel_del = check_cancellation_eligibility("ORD-102", db, customer_id=rahul.id)
        assert res_cancel_del["success"] is True
        assert res_cancel_del["eligible"] is False
        assert "already been delivered" in res_cancel_del["message"].lower()
        print("[PASS] Ineligible cancellation: ORD-102 (Delivered) -> eligible=False (delivered orders cannot be cancelled)")

        # Invalid Order ID
        res_cancel_invalid = check_cancellation_eligibility("ORD-999", db)
        assert res_cancel_invalid["success"] is False
        assert res_cancel_invalid["eligible"] is False
        assert "couldn't find order" in res_cancel_invalid["error"].lower()
        print("[PASS] Invalid order cancellation: ORD-999 -> graceful error")

        # Missing Order ID
        res_cancel_empty = check_cancellation_eligibility("", db)
        assert res_cancel_empty["success"] is False
        assert res_cancel_empty["eligible"] is False
        assert "provide your order id" in res_cancel_empty["error"].lower()
        print("[PASS] Missing order ID cancellation -> prompted customer for ID")

        # IDOR protection: Priya trying to cancel Rahul's order ORD-102
        res_cancel_idor = check_cancellation_eligibility("ORD-102", db, customer_id=priya.id)
        assert res_cancel_idor["success"] is False
        assert res_cancel_idor["eligible"] is False
        assert "does not belong" in res_cancel_idor["error"].lower()
        print("[PASS] IDOR blocked on cancellation: Priya cannot cancel Rahul's order")

        # ---------------------------------------------------------------------
        # 3. RETURN ELIGIBILITY TESTS
        # ---------------------------------------------------------------------
        print("\n--- Testing Return Eligibility Policy ---")
        # Eligible: Delivered within 7 days, unopened, unused, in original packaging
        # ORD-106 (Rohan) was delivered 2 days ago
        res_return_eligible = check_return_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            is_opened=False,
            is_used=False,
            in_original_packaging=True,
        )
        assert res_return_eligible["success"] is True
        assert res_return_eligible["eligible"] is True
        assert res_return_eligible["delivered_days_ago"] == 2
        assert "eligible for return" in res_return_eligible["message"].lower()
        print("[PASS] Eligible return: ORD-106 delivered 2 days ago, unopened/unused/original packaging -> eligible=True")

        # Ineligible: Delivered > 7 days ago (ORD-102 delivered 14 days ago)
        res_return_expired = check_return_eligibility("ORD-102", db, customer_id=rahul.id)
        assert res_return_expired["success"] is True
        assert res_return_expired["eligible"] is False
        assert res_return_expired["delivered_days_ago"] == 14
        assert "exceeds our 7-day return window" in res_return_expired["message"].lower()
        print("[PASS] Ineligible return: ORD-102 delivered 14 days ago (>7 days) -> eligible=False")

        # Ineligible: Order not delivered yet (ORD-101 Out for Delivery, ORD-103 Processing)
        res_return_undelivered = check_return_eligibility("ORD-101", db, customer_id=priya.id)
        assert res_return_undelivered["success"] is True
        assert res_return_undelivered["eligible"] is False
        assert "not been delivered yet" in res_return_undelivered["reason"].lower()
        print("[PASS] Ineligible return: ORD-101 (Out for Delivery) -> eligible=False (must be delivered first)")

        # Ineligible: Delivered within 7 days BUT opened / used
        res_return_opened = check_return_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            is_opened=True,
            is_used=False,
            in_original_packaging=True,
        )
        assert res_return_opened["success"] is True
        assert res_return_opened["eligible"] is False
        assert "opened" in res_return_opened["reason"].lower()
        print("[PASS] Ineligible return: ORD-106 opened -> eligible=False (only unopened accepted)")

        res_return_no_box = check_return_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            is_opened=False,
            is_used=False,
            in_original_packaging=False,
        )
        assert res_return_no_box["success"] is True
        assert res_return_no_box["eligible"] is False
        assert "not in original packaging" in res_return_no_box["reason"].lower()
        print("[PASS] Ineligible return: ORD-106 missing original packaging -> eligible=False")

        # Missing Information: Delivered within 7 days, but opened/used status unknown
        res_return_missing_info = check_return_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            is_opened=None,
            is_used=None,
            in_original_packaging=None,
        )
        assert res_return_missing_info["success"] is True
        assert res_return_missing_info["eligible"] is None  # Pending clarification
        assert "missing_info" in res_return_missing_info
        assert "unopened, unused, and in its original packaging" in res_return_missing_info["message"]
        print("[PASS] Missing return info: Asks customer if item is unopened/unused/in original packaging")

        # Invalid Order ID
        res_return_invalid = check_return_eligibility("ORD-999", db)
        assert res_return_invalid["success"] is False
        assert "couldn't find order" in res_return_invalid["error"].lower()
        print("[PASS] Invalid order return: ORD-999 -> handled safely")

        # IDOR check
        res_return_idor = check_return_eligibility("ORD-106", db, customer_id=priya.id)
        assert res_return_idor["success"] is False
        assert "does not belong" in res_return_idor["error"].lower()
        print("[PASS] IDOR blocked on return: Priya cannot return Rohan's order")

        # ---------------------------------------------------------------------
        # 4. DAMAGED / DEFECTIVE REPORTING ELIGIBILITY TESTS
        # ---------------------------------------------------------------------
        print("\n--- Testing Damaged / Defective Reporting Policy ---")
        # Eligible: Delivered within 48 hours (ORD-106, 2 days = 48 hrs) with photos
        res_damaged_eligible = check_damaged_reporting_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            has_photos=True,
            delivered_hours_ago=24,
        )
        assert res_damaged_eligible["success"] is True
        assert res_damaged_eligible["eligible"] is True
        assert res_damaged_eligible["has_photos"] is True
        assert "eligible for a replacement" in res_damaged_eligible["message"].lower()
        print("[PASS] Eligible damaged report: Within 48 hours with photos -> eligible=True for replacement")

        # Ineligible: Delivered > 48 hours ago (ORD-102 delivered 14 days ago)
        res_damaged_expired = check_damaged_reporting_eligibility(
            "ORD-102",
            db,
            customer_id=rahul.id,
            has_photos=True,
        )
        assert res_damaged_expired["success"] is True
        assert res_damaged_expired["eligible"] is False
        assert "exceeding our 48-hour reporting window" in res_damaged_expired["message"].lower()
        print("[PASS] Ineligible damaged report: ORD-102 delivered 14 days ago (>48h) -> eligible=False")

        # Ineligible: Order not delivered yet (ORD-103 Processing)
        res_damaged_undelivered = check_damaged_reporting_eligibility("ORD-103", db, customer_id=ananya.id)
        assert res_damaged_undelivered["success"] is True
        assert res_damaged_undelivered["eligible"] is False
        assert "has not been delivered yet" in res_damaged_undelivered["reason"].lower()
        print("[PASS] Ineligible damaged report: ORD-103 not delivered yet -> eligible=False")

        # Ineligible: Within 48 hours but customer refuses to provide photos (has_photos=False)
        res_damaged_no_photos = check_damaged_reporting_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            has_photos=False,
            delivered_hours_ago=12,
        )
        assert res_damaged_no_photos["success"] is True
        assert res_damaged_no_photos["eligible"] is False
        assert "photos of the damaged or defective product are required" in res_damaged_no_photos["message"].lower()
        print("[PASS] Ineligible damaged report without photos: has_photos=False -> eligible=False")

        # Missing Information: Within 48 hours, but photo status not specified (has_photos=None)
        res_damaged_missing_photos = check_damaged_reporting_eligibility(
            "ORD-106",
            db,
            customer_id=rohan.id,
            has_photos=None,
            delivered_hours_ago=12,
        )
        assert res_damaged_missing_photos["success"] is True
        assert res_damaged_missing_photos["eligible"] is None  # Pending photos
        assert "photos" in res_damaged_missing_photos["missing_info"]
        assert "provide photos" in res_damaged_missing_photos["message"].lower()
        print("[PASS] Missing photos prompt: Asks customer for photos within 48h window")

        # Invalid Order ID
        res_damaged_invalid = check_damaged_reporting_eligibility("ORD-999", db)
        assert res_damaged_invalid["success"] is False
        assert "couldn't find order" in res_damaged_invalid["error"].lower()
        print("[PASS] Invalid order damaged report -> handled safely")

        # IDOR check
        res_damaged_idor = check_damaged_reporting_eligibility("ORD-106", db, customer_id=priya.id)
        assert res_damaged_idor["success"] is False
        assert "does not belong" in res_damaged_idor["error"].lower()
        print("[PASS] IDOR blocked on damaged report: Priya cannot report Rohan's order")

        # ---------------------------------------------------------------------
        # 5. SHIPPING AND COD POLICY TESTS
        # ---------------------------------------------------------------------
        print("\n--- Testing Shipping Fee, Delivery Timeline & COD Policies ---")
        # Order amount > ₹499 -> Free shipping
        res_ship_free = get_shipping_and_cod_policy(order_amount=699)
        assert res_ship_free["success"] is True
        assert res_ship_free["free_shipping"] is True
        assert res_ship_free["shipping_fee"] == 0
        assert res_ship_free["delivery_timeline"] == "3–5 business days"
        assert res_ship_free["cod_available"] is True
        assert "Cash" in res_ship_free["cod_payment_methods"]
        assert "UPI" in res_ship_free["cod_payment_methods"]
        print("[PASS] Order ₹699 (>₹499): Free shipping (₹0 fee), 3–5 days, COD available via Cash/UPI")

        # Order amount < ₹499 -> ₹50 shipping fee
        res_ship_fee = get_shipping_and_cod_policy(order_amount=299)
        assert res_ship_fee["success"] is True
        assert res_ship_fee["free_shipping"] is False
        assert res_ship_fee["shipping_fee"] == 50
        assert res_ship_fee["delivery_timeline"] == "3–5 business days"
        assert res_ship_fee["cod_available"] is True
        print("[PASS] Order ₹299 (<₹499): ₹50 shipping fee, 3–5 days, COD available")

        # Order amount at ₹499 threshold
        res_ship_threshold = get_shipping_and_cod_policy(order_amount=499)
        assert res_ship_threshold["success"] is True
        # "Free shipping for orders above ₹499. Orders below ₹499 have a ₹50 shipping fee."
        assert res_ship_threshold["shipping_fee"] in [0, 50]
        print(f"[PASS] Order ₹499 threshold: Handled cleanly (shipping fee: ₹{res_ship_threshold['shipping_fee']})")

        # COD threshold: Order <= ₹2,500 vs > ₹2,500
        res_cod_ok = get_shipping_and_cod_policy(order_amount=2499)
        assert res_cod_ok["cod_available"] is True
        print("[PASS] Order ₹2,499 (<=₹2,500): COD available")

        res_cod_exceeded = get_shipping_and_cod_policy(order_amount=3500)
        assert res_cod_exceeded["cod_available"] is False
        assert "not available for orders above ₹2,500" in res_cod_exceeded["message"]
        print("[PASS] Order ₹3,500 (>₹2,500): COD not available")

        # General policy query without specific amount
        res_policy_general = get_shipping_and_cod_policy()
        assert res_policy_general["success"] is True
        assert res_policy_general["policy"]["free_shipping_threshold"] == 499
        assert res_policy_general["policy"]["standard_shipping_fee"] == 50
        assert res_policy_general["policy"]["cod_maximum_limit"] == 2500
        assert "3–5 business days" in res_policy_general["policy"]["standard_delivery_timeline"]
        print("[PASS] General shipping & COD policy query returned complete ruleset")

        # Query shipping policy for existing order by order_id
        res_ship_order = get_shipping_and_cod_policy(order_id="ORD-101", db=db)
        assert res_ship_order["success"] is True
        assert res_ship_order["order_amount"] == 699
        assert res_ship_order["free_shipping"] is True
        print("[PASS] Shipping policy lookup for ORD-101 (₹699) automatically resolved from database")

        # ---------------------------------------------------------------------
        # 6. AI TOOL INVOCATIONS (LangChain Tool Wrappers)
        # ---------------------------------------------------------------------
        print("\n--- Testing LangChain AI Tools Invocations ---")
        # lookup_customer_order tool
        token = active_customer_id.set(priya.id)
        try:
            raw_tool_lookup = lookup_customer_order.invoke({"order_id": "ORD-101"})
            data = json.loads(raw_tool_lookup)
            assert data["success"] is True
            assert data["order"]["product_name"] == "Vitamin C Serum (30ml)"
            print("[PASS] lookup_customer_order tool: ORD-101 returned valid JSON")

            # check_cancellation_eligibility_tool
            raw_tool_cancel = check_cancellation_eligibility_tool.invoke({"order_id": "ORD-101"})
            data_cancel = json.loads(raw_tool_cancel)
            assert data_cancel["eligible"] is False
            assert data_cancel["doorstep_refusal_allowed"] is True
            print("[PASS] check_cancellation_eligibility_tool: ORD-101 returned eligible=False")

            # check_return_eligibility_tool
            raw_tool_return = check_return_eligibility_tool.invoke({"order_id": "ORD-101"})
            data_return = json.loads(raw_tool_return)
            assert data_return["eligible"] is False
            print("[PASS] check_return_eligibility_tool: ORD-101 returned eligible=False (undelivered)")

            # check_damaged_reporting_eligibility_tool
            raw_tool_damaged = check_damaged_reporting_eligibility_tool.invoke({"order_id": "ORD-101"})
            data_damaged = json.loads(raw_tool_damaged)
            assert data_damaged["eligible"] is False
            print("[PASS] check_damaged_reporting_eligibility_tool: ORD-101 returned eligible=False (undelivered)")

            # get_shipping_and_cod_policy_tool
            raw_tool_ship = get_shipping_and_cod_policy_tool.invoke({"order_amount": 750})
            data_ship = json.loads(raw_tool_ship)
            assert data_ship["free_shipping"] is True
            assert data_ship["cod_available"] is True
            print("[PASS] get_shipping_and_cod_policy_tool: ₹750 returned free shipping & COD true")

            # Action integrity: Verify tool outputs never falsely declare completed action
            assert "has been cancelled" not in raw_tool_cancel.lower()
            assert "refund has been issued" not in raw_tool_return.lower()
            assert "replacement has been dispatched" not in raw_tool_damaged.lower()
            print("[PASS] Action Integrity: Tools never claim an action was executed without actual execution")

        finally:
            active_customer_id.reset(token)

    print("\n" + "=" * 70)
    print("ALL POLICY-AWARE ORDER SUPPORT TESTS PASSED! (100% SUCCESS)")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()

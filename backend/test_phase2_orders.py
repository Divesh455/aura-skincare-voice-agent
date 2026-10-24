"""
Phase 2 Automated Test Suite: Secure Customer and Order Ownership
Validates all acceptance criteria for Feature 2:
- Customer ownership validation
- Insecure Direct Object Reference (IDOR) prevention
- Preservation of mock orders ORD-101, ORD-102, ORD-103
- Strict authentication enforcement
"""

import json
from fastapi.testclient import TestClient

from app.ai_tools import active_customer_id, lookup_customer_order
from app.main import app

client = TestClient(app)


def get_token(test_client: TestClient, email: str, password: str = "Password123!") -> str:
    res = test_client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def run_phase2_tests():
    print("=" * 60)
    print("RUNNING PHASE 2 TEST SUITE: ORDER OWNERSHIP & IDOR PREVENTION")
    print("=" * 60)

    with TestClient(app) as test_client:
        # Obtain auth tokens for the three mock customers
        priya_token = get_token(test_client, "priya@example.com")
        rahul_token = get_token(test_client, "rahul@example.com")
        ananya_token = get_token(test_client, "ananya@example.com")

        print("[PASS] Obtained valid tokens for Priya, Rahul, and Ananya")

        # ---------------------------------------------------------
        # 1. Verify Authorized Access to Owned Orders
        # ---------------------------------------------------------
        # Priya accesses ORD-101
        res = test_client.get(
            "/api/orders/ORD-101",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json()["order"]["product_name"] == "Vitamin C Serum (30ml)"
        print("[PASS] Priya successfully accesses her order ORD-101")

        # Rahul accesses ORD-102
        res = test_client.get(
            "/api/orders/ORD-102",
            headers={"Authorization": f"Bearer {rahul_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json()["order"]["product_name"] == "Hydrating Sunscreen SPF 50"
        print("[PASS] Rahul successfully accesses his order ORD-102")

        # Ananya accesses ORD-103
        res = test_client.get(
            "/api/orders/ORD-103",
            headers={"Authorization": f"Bearer {ananya_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json()["order"]["product_name"] == "Green Tea Face Wash + Toner"
        print("[PASS] Ananya successfully accesses her order ORD-103")

        # ---------------------------------------------------------
        # 2. Verify Cross-Customer Access Is Strictly Blocked (IDOR)
        # ---------------------------------------------------------
        # Priya attempts to access Rahul's order ORD-102
        res = test_client.get(
            "/api/orders/ORD-102",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        assert "does not belong to your account" in res.json()["detail"]
        print("[PASS] IDOR blocked: Priya cannot access Rahul's ORD-102 (403 Forbidden)")

        # Priya attempts to access Ananya's order ORD-103
        res = test_client.get(
            "/api/orders/ORD-103",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        assert "does not belong to your account" in res.json()["detail"]
        print("[PASS] IDOR blocked: Priya cannot access Ananya's ORD-103 (403 Forbidden)")

        # Rahul attempts to access Priya's order ORD-101
        res = test_client.get(
            "/api/orders/ORD-101",
            headers={"Authorization": f"Bearer {rahul_token}"}
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("[PASS] IDOR blocked: Rahul cannot access Priya's ORD-101 (403 Forbidden)")

        # Ananya attempts to access Priya's order ORD-101
        res = test_client.get(
            "/api/orders/ORD-101",
            headers={"Authorization": f"Bearer {ananya_token}"}
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("[PASS] IDOR blocked: Ananya cannot access Priya's ORD-101 (403 Forbidden)")

        # ---------------------------------------------------------
        # 3. Nonexistent Orders & Unauthenticated Access
        # ---------------------------------------------------------
        # Nonexistent order ORD-999
        res = test_client.get(
            "/api/orders/ORD-999",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("[PASS] Nonexistent order correctly returns 404 Not Found")

        # Unauthenticated order lookup
        res = test_client.get("/api/orders/ORD-101")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
        print("[PASS] Unauthenticated access to order details blocked (401 Unauthorized)")

        # ---------------------------------------------------------
        # 4. Customer Orders List Endpoint (/api/orders)
        # ---------------------------------------------------------
        # Priya's order list
        res = test_client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert res.status_code == 200
        priya_orders = res.json()["orders"]
        assert len(priya_orders) == 1
        assert priya_orders[0]["order_id"] == "ORD-101"
        print("[PASS] GET /api/orders returns only Priya's order (ORD-101)")

        # Rahul's order list
        res = test_client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {rahul_token}"}
        )
        assert res.status_code == 200
        rahul_orders = res.json()["orders"]
        assert len(rahul_orders) == 1
        assert rahul_orders[0]["order_id"] == "ORD-102"
        print("[PASS] GET /api/orders returns only Rahul's order (ORD-102)")

        # Ananya's order list
        res = test_client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {ananya_token}"}
        )
        assert res.status_code == 200
        ananya_orders = res.json()["orders"]
        assert len(ananya_orders) == 1
        assert ananya_orders[0]["order_id"] == "ORD-103"
        print("[PASS] GET /api/orders returns only Ananya's order (ORD-103)")

        # Unauthenticated request to /api/orders
        res = test_client.get("/api/orders")
        assert res.status_code == 401
        print("[PASS] Unauthenticated GET /api/orders blocked (401 Unauthorized)")

        # ---------------------------------------------------------
        # 5. AI Tool Ownership Context Validation
        # ---------------------------------------------------------
        # Mock customer IDs from profile
        priya_me = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {priya_token}"}).json()
        priya_cid = priya_me["id"]

        # Set active context to Priya
        tok = active_customer_id.set(priya_cid)
        try:
            # Looking up Priya's own order
            res1 = json.loads(lookup_customer_order.invoke({"order_id": "ORD-101"}))
            assert res1["success"] is True
            assert res1["order"]["product_name"] == "Vitamin C Serum (30ml)"

            # Attempting to look up Rahul's order while Priya is active
            res2 = json.loads(lookup_customer_order.invoke({"order_id": "ORD-102"}))
            assert res2["success"] is False
            assert "does not belong to your account" in res2["error"]
            print("[PASS] AI Tool enforces customer ownership: Priya cannot probe Rahul's order through Aria")
        finally:
            active_customer_id.reset(tok)

    print("=" * 60)
    print("ALL PHASE 2 TESTS PASSED SUCCESSFULLY! (100% PASS)")
    print("=" * 60)


if __name__ == "__main__":
    run_phase2_tests()

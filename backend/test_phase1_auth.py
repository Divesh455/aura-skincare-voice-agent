"""
Phase 1 Automated Test Suite: Customer Registration, Login & Authentication
Tests all acceptance criteria for Feature 1 and verifies DB safety.
"""

import sys
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Customer, Order
from app.orders import seed_orders

client = TestClient(app)


def run_phase1_tests():
    print("=" * 60)
    print("RUNNING PHASE 1 TEST SUITE: AUTHENTICATION & SECURITY")
    print("=" * 60)

    # 1. Trigger app lifespan (creates tables and seeds mock accounts)
    with TestClient(app) as test_client:
        # Check health endpoint
        health_resp = test_client.get("/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        print("[PASS] Health & PostgreSQL connection: OK")

        # 2. Verify Seed Data for Mock Customers & Order Associations
        with SessionLocal() as db:
            priya = db.query(Customer).filter_by(email="priya@example.com").first()
            rahul = db.query(Customer).filter_by(email="rahul@example.com").first()
            ananya = db.query(Customer).filter_by(email="ananya@example.com").first()

            assert priya is not None, "Mock customer Priya Sharma was not seeded."
            assert rahul is not None, "Mock customer Rahul Verma was not seeded."
            assert ananya is not None, "Mock customer Ananya Patel was not seeded."

            # Verify password hashing
            assert priya.hashed_password.startswith("$argon2"), "Password was not hashed using Argon2!"

            # Verify order links
            ord_101 = db.query(Order).filter_by(order_id="ORD-101").first()
            ord_102 = db.query(Order).filter_by(order_id="ORD-102").first()
            ord_103 = db.query(Order).filter_by(order_id="ORD-103").first()

            assert ord_101.customer_id == priya.id, f"ORD-101 not linked to Priya (got {ord_101.customer_id}, expected {priya.id})"
            assert ord_102.customer_id == rahul.id, f"ORD-102 not linked to Rahul (got {ord_102.customer_id}, expected {rahul.id})"
            assert ord_103.customer_id == ananya.id, f"ORD-103 not linked to Ananya (got {ord_103.customer_id}, expected {ananya.id})"
            print("[PASS] Mock customers and order associations seeded with Argon2 hashes: OK")

        # 3. Test Registration - Validation Constraints
        # Test password mismatch
        mismatch_payload = {
            "full_name": "Test User",
            "email": "mismatch@example.com",
            "password": "Password123!",
            "password_confirm": "DifferentPassword123!",
        }
        res = test_client.post("/api/auth/register", json=mismatch_payload)
        assert res.status_code == 422, f"Expected 422 for password mismatch, got {res.status_code}"
        print("[PASS] Registration rejected password mismatch: OK")

        # Test invalid email format
        bad_email_payload = {
            "full_name": "Test User",
            "email": "not-an-email",
            "password": "Password123!",
            "password_confirm": "Password123!",
        }
        res = test_client.post("/api/auth/register", json=bad_email_payload)
        assert res.status_code == 422, f"Expected 422 for invalid email, got {res.status_code}"
        print("[PASS] Registration rejected invalid email format: OK")

        # Test short password
        short_pass_payload = {
            "full_name": "Test User",
            "email": "shortpass@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        res = test_client.post("/api/auth/register", json=short_pass_payload)
        assert res.status_code == 422, f"Expected 422 for weak password, got {res.status_code}"
        print("[PASS] Registration rejected weak password (<8 characters): OK")

        # 4. Test Successful Registration
        new_customer_email = "newcustomer@test.com"
        reg_payload = {
            "full_name": "Aarav Gupta",
            "email": new_customer_email,
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
        }
        res = test_client.post("/api/auth/register", json=reg_payload)
        assert res.status_code in (201, 409), f"Unexpected status: {res.status_code}"
        if res.status_code == 201:
            data = res.json()
            assert "access_token" in data, "No access_token returned"
            assert data["customer"]["full_name"] == "Aarav Gupta"
            assert data["customer"]["welcome_message"] == "Hi Aarav! Welcome back to Aura Skincare."
            print("[PASS] New customer registration & personalized welcome message: OK")

        # Test Duplicate Email Registration
        res = test_client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 409, f"Expected 409 for duplicate email, got {res.status_code}"
        print("[PASS] Duplicate email registration rejected with 409 Conflict: OK")

        # 5. Test Customer Login
        # Login with correct password for Priya
        login_res = test_client.post("/api/auth/login", json={
            "email": "priya@example.com",
            "password": "Password123!"
        })
        assert login_res.status_code == 200, f"Login failed for Priya: {login_res.text}"
        priya_data = login_res.json()
        priya_token = priya_data["access_token"]
        assert priya_token, "No access_token returned for Priya"
        assert priya_data["customer"]["welcome_message"] == "Hi Priya! Welcome back to Aura Skincare."
        print("[PASS] Login with correct credentials: OK")

        # Login with wrong password
        wrong_pass_res = test_client.post("/api/auth/login", json={
            "email": "priya@example.com",
            "password": "WrongPassword999!"
        })
        assert wrong_pass_res.status_code == 401, f"Expected 401 for wrong password, got {wrong_pass_res.status_code}"
        print("[PASS] Login with invalid password rejected with 401: OK")

        # Login for non-existent email
        not_found_res = test_client.post("/api/auth/login", json={
            "email": "nonexistent@aura.com",
            "password": "Password123!"
        })
        assert not_found_res.status_code == 401, f"Expected 401 for non-existent user, got {not_found_res.status_code}"
        print("[PASS] Login with nonexistent email rejected with 401: OK")

        # 6. Test Protected Endpoint /api/auth/me
        # Call without token
        unauth_me = test_client.get("/api/auth/me")
        assert unauth_me.status_code == 401, f"Expected 401 for unauthenticated request, got {unauth_me.status_code}"
        print("[PASS] /api/auth/me blocks unauthenticated requests: OK")

        # Call with Priya's token
        auth_me = test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert auth_me.status_code == 200, f"Failed to get profile: {auth_me.text}"
        profile = auth_me.json()
        assert profile["full_name"] == "Priya Sharma"
        assert profile["welcome_message"] == "Hi Priya! Welcome back to Aura Skincare."
        print("[PASS] /api/auth/me returns verified profile & personalized greeting: OK")

        # 7. Test Order Ownership Authorization
        # Priya accesses her own order (ORD-101)
        ord101_res = test_client.get(
            "/api/orders/ORD-101",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert ord101_res.status_code == 200, f"Priya could not access ORD-101: {ord101_res.text}"
        assert ord101_res.json()["order"]["product_name"] == "Vitamin C Serum (30ml)"
        print("[PASS] Authorized customer accesses own order ORD-101: OK")

        # Priya attempts to access Rahul's order (ORD-102) -> must be 403 Forbidden!
        ord102_res = test_client.get(
            "/api/orders/ORD-102",
            headers={"Authorization": f"Bearer {priya_token}"}
        )
        assert ord102_res.status_code == 403, f"Expected 403 when accessing another's order, got {ord102_res.status_code}"
        print("[PASS] Unauthorized access to another customer's order is blocked (403 Forbidden): OK")

        # Unauthenticated request to order lookup
        no_auth_ord = test_client.get("/api/orders/ORD-101")
        assert no_auth_ord.status_code == 401, f"Expected 401 without token, got {no_auth_ord.status_code}"
        print("[PASS] Unauthenticated order lookup blocked (401 Unauthorized): OK")

    print("=" * 60)
    print("ALL PHASE 1 TESTS PASSED SUCCESSFULLY! (100% PASS)")
    print("=" * 60)


if __name__ == "__main__":
    run_phase1_tests()

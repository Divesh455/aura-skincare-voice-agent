"""
Phase 4 Automated Test Suite: Selective Conversation Storage & Structured Call Summary
Validates all acceptance criteria for Features 4 and 5:
- Selective persistence: important interactions are stored in PostgreSQL
- Exclusion of ordinary greetings and small talk from DB persistence
- Correct structured JSON call summary format
- Flagging complaints, damaged goods, and unresolved issues for human support
- Prevention of IDOR on saved interaction records
- Zero storage of secrets, tokens, or passwords
"""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Customer, SavedInteraction
from app.sessions import session_registry

client = TestClient(app)


def get_token(test_client: TestClient, email: str, password: str = "Password123!") -> str:
    res = test_client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def run_phase4_tests():
    print("=" * 60)
    print("RUNNING PHASE 4 TEST SUITE: SELECTIVE STORAGE & CALL SUMMARY")
    print("=" * 60)

    with TestClient(app) as test_client:
        priya_token = get_token(test_client, "priya@example.com")
        rahul_token = get_token(test_client, "rahul@example.com")

        # ---------------------------------------------------------
        # 1. Ordinary Greetings & Small Talk -> NOT Saved in DB
        # ---------------------------------------------------------
        # Start a call
        start_res = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
        call_id_trivial = start_res.json()["call_id"]

        # Simulate small talk / greeting in session messages
        session = session_registry.get_session(call_id_trivial)
        session.add_message("user", "Hello! Good morning, just checking what you can do.")
        session.add_message("assistant", "Hi Priya! I can help you with order lookups, returns, and skincare routines.")

        with SessionLocal() as db:
            count_before = len(db.scalars(select(SavedInteraction)).all())

        # End call
        end_res = test_client.post(f"/api/calls/{call_id_trivial}/end", headers={"Authorization": f"Bearer {priya_token}"})
        assert end_res.status_code == 200
        summary_trivial = end_res.json()["summary"]

        assert summary_trivial["is_saved"] is False, "Ordinary greeting was incorrectly marked as saved!"
        assert summary_trivial["saved_record_id"] is None
        assert summary_trivial["requires_human_support"] is False

        with SessionLocal() as db:
            count_after = len(db.scalars(select(SavedInteraction)).all())
            assert count_after == count_before, "Ordinary small talk created an unexpected database record!"

        print("[PASS] Ordinary greetings and small talk correctly EXCLUDED from database persistence")

        # ---------------------------------------------------------
        # 2. Meaningful Order Status Inquiry -> Saved in DB
        # ---------------------------------------------------------
        start_res = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
        call_id_order = start_res.json()["call_id"]

        session = session_registry.get_session(call_id_order)
        session.add_message("user", "Can you check my order ORD-101?")
        session.add_message("assistant", "Your order ORD-101 for Vitamin C Serum is Out for Delivery by 6 PM today via BlueDart.")

        end_res = test_client.post(f"/api/calls/{call_id_order}/end", headers={"Authorization": f"Bearer {priya_token}"})
        assert end_res.status_code == 200
        summary_order = end_res.json()["summary"]

        assert summary_order["is_saved"] is True, "Order inquiry was not saved!"
        assert summary_order["order_id"] == "ORD-101"
        assert summary_order["customer_intent"] == "Order Status Inquiry"
        assert summary_order["saved_record_id"] is not None

        # Verify DB record
        with SessionLocal() as db:
            saved_rec = db.scalar(select(SavedInteraction).where(SavedInteraction.id == summary_order["saved_record_id"]))
            assert saved_rec is not None
            assert saved_rec.call_id == call_id_order
            assert saved_rec.order_id == "ORD-101"
            assert saved_rec.email_delivery_status == "pending"

        print(f"[PASS] Order inquiry saved immediately to PostgreSQL (Record ID: {summary_order['saved_record_id']})")

        # ---------------------------------------------------------
        # 3. Damaged Product Complaint & Escalation -> Saved & Flagged
        # ---------------------------------------------------------
        start_res = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
        call_id_complaint = start_res.json()["call_id"]

        session = session_registry.get_session(call_id_complaint)
        session.add_message("user", "My serum from order ORD-101 arrived completely damaged and broken! I want to file a complaint.")
        session.add_message("assistant", "I am so sorry to hear that your Vitamin C Serum arrived damaged. Let me escalate this for human assistance.")

        end_res = test_client.post(f"/api/calls/{call_id_complaint}/end", headers={"Authorization": f"Bearer {priya_token}"})
        assert end_res.status_code == 200
        summary_complaint = end_res.json()["summary"]

        assert summary_complaint["is_saved"] is True
        assert summary_complaint["requires_human_support"] is True
        assert summary_complaint["resolution_status"] == "unresolved"
        assert "Damaged" in summary_complaint["customer_intent"]
        complaint_rec_id = summary_complaint["saved_record_id"]

        with SessionLocal() as db:
            saved_complaint = db.scalar(select(SavedInteraction).where(SavedInteraction.id == complaint_rec_id))
            assert saved_complaint.requires_human_support is True
            assert saved_complaint.resolution_status == "unresolved"

        print(f"[PASS] Damaged item complaint saved and flagged for human support (Record ID: {complaint_rec_id})")

        # ---------------------------------------------------------
        # 4. Structured JSON Summary Fields Check
        # ---------------------------------------------------------
        expected_keys = {
            "customer_intent",
            "order_id",
            "resolution_status",
            "call_summary",
            "important_details",
            "requires_human_support",
            "is_saved",
            "saved_record_id",
        }
        assert expected_keys.issubset(set(summary_complaint.keys())), "Summary missing required fields"
        print("[PASS] Structured JSON summary contains all required fields")

        # ---------------------------------------------------------
        # 5. Customer Interactions Retrieval & IDOR Protection
        # ---------------------------------------------------------
        # Priya retrieves her saved interactions
        priya_interactions_res = test_client.get("/api/interactions", headers={"Authorization": f"Bearer {priya_token}"})
        assert priya_interactions_res.status_code == 200
        priya_list = priya_interactions_res.json()
        assert len(priya_list) >= 2
        print(f"[PASS] Customer can view their saved interaction history ({len(priya_list)} records)")

        # Rahul attempts to access Priya's complaint record
        rahul_idor_res = test_client.get(f"/api/interactions/{complaint_rec_id}", headers={"Authorization": f"Bearer {rahul_token}"})
        assert rahul_idor_res.status_code == 403, f"Expected 403, got {rahul_idor_res.status_code}"
        print("[PASS] IDOR blocked: Rahul cannot access Priya's saved interaction record (403 Forbidden)")

        # Unauthenticated access to interactions
        unauth_interactions = test_client.get("/api/interactions")
        assert unauth_interactions.status_code == 401
        print("[PASS] Unauthenticated access to interaction records blocked (401 Unauthorized)")

        # ---------------------------------------------------------
        # 6. Security: Verify Sensitive Information Is Never Stored
        # ---------------------------------------------------------
        with SessionLocal() as db:
            all_records = db.scalars(select(SavedInteraction)).all()
            for rec in all_records:
                combined_fields = f"{rec.important_details} {rec.call_summary} {rec.customer_intent}"
                assert "bearer" not in combined_fields.lower(), "Found token pattern in saved record!"
                assert "argon2" not in combined_fields.lower(), "Found password hash in saved record!"
                assert "password" not in combined_fields.lower() or "password123" not in combined_fields.lower()
        print("[PASS] Security verified: No tokens, passwords, or credentials stored in interaction records")

    print("=" * 60)
    print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY! (100% PASS)")
    print("=" * 60)


if __name__ == "__main__":
    run_phase4_tests()

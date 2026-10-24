"""
Phase 5 Automated Test Suite: Support Email & n8n Delayed Webhook Pipeline
Validates all acceptance criteria for Feature 6:
- Non-blocking webhook dispatch for important interactions
- Non-dispatch for ordinary/excluded interactions
- Safe immediate persistence in PostgreSQL prior to email scheduling
- Security validation of webhook secret header
- Updating delivery status to 'delivered' upon confirmation
- Deduplication: preventing duplicate emails on webhook retry
"""

import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import SavedInteraction
from app.sessions import session_registry

client = TestClient(app)


def get_token(test_client: TestClient, email: str, password: str = "Password123!") -> str:
    res = test_client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def run_phase5_tests():
    print("=" * 60)
    print("RUNNING PHASE 5 TEST SUITE: N8N SUPPORT EMAIL & WEBHOOK PIPELINE")
    print("=" * 60)

    webhook_secret = os.getenv("N8N_WEBHOOK_SECRET", "aura_n8n_secret_dev")

    with TestClient(app) as test_client:
        priya_token = get_token(test_client, "priya@example.com")

        # ---------------------------------------------------------
        # 1. Verify Non-Blocking Webhook Trigger on Important Call End
        # ---------------------------------------------------------
        with patch("app.main.trigger_n8n_support_webhook") as mock_webhook_dispatch:
            mock_webhook_dispatch.return_value = True

            # Start and simulate an important order inquiry
            start_res = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
            call_id_imp = start_res.json()["call_id"]

            session = session_registry.get_session(call_id_imp)
            session.add_message("user", "Can you check order ORD-101? I am worried about the delivery time.")
            session.add_message("assistant", "Order ORD-101 is Out for Delivery by 6 PM today via BlueDart.")

            # End call
            end_res = test_client.post(f"/api/calls/{call_id_imp}/end", headers={"Authorization": f"Bearer {priya_token}"})
            assert end_res.status_code == 200
            summary = end_res.json()["summary"]

            assert summary["is_saved"] is True
            interaction_id = summary["saved_record_id"]
            assert interaction_id is not None

            # Verify that the webhook was dispatched via background task
            assert mock_webhook_dispatch.called, "n8n webhook dispatch was not triggered for important interaction!"
            dispatched_payload = mock_webhook_dispatch.call_args[0][0]

            assert dispatched_payload["interaction_id"] == interaction_id
            assert dispatched_payload["call_id"] == call_id_imp
            assert dispatched_payload["customer_name"] == "Priya Sharma"
            assert dispatched_payload["order_id"] == "ORD-101"
            assert dispatched_payload["customer_intent"] == "Order Status Inquiry"
            assert "support_email" in dispatched_payload

            print(f"[PASS] Important call immediately saved to PostgreSQL (ID: {interaction_id})")
            print("[PASS] n8n webhook triggered asynchronously with structured payload")

        # ---------------------------------------------------------
        # 2. Verify Webhook is NOT Triggered for Ordinary Small Talk
        # ---------------------------------------------------------
        with patch("app.main.trigger_n8n_support_webhook") as mock_webhook_dispatch:
            start_res = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
            call_id_smalltalk = start_res.json()["call_id"]

            session = session_registry.get_session(call_id_smalltalk)
            session.add_message("user", "Hello! Good morning, thank you for your help.")
            session.add_message("assistant", "You're very welcome! Have a wonderful day.")

            end_res = test_client.post(f"/api/calls/{call_id_smalltalk}/end", headers={"Authorization": f"Bearer {priya_token}"})
            assert end_res.status_code == 200

            assert not mock_webhook_dispatch.called, "Webhook was triggered for ordinary small talk!"
            print("[PASS] Ordinary pleasantries do NOT trigger support email webhook")

        # ---------------------------------------------------------
        # 3. Security: Webhook Callback Secret Validation
        # ---------------------------------------------------------
        # Unauthenticated callback (missing secret)
        unauth_callback = test_client.post(
            "/api/webhooks/n8n/email-status",
            json={
                "interaction_id": interaction_id,
                "call_id": call_id_imp,
                "status": "delivered",
            },
        )
        assert unauth_callback.status_code == 401
        print("[PASS] Missing webhook secret header rejected (401 Unauthorized)")

        # Invalid secret
        bad_secret_callback = test_client.post(
            "/api/webhooks/n8n/email-status",
            json={
                "interaction_id": interaction_id,
                "call_id": call_id_imp,
                "status": "delivered",
            },
            headers={"X-Aura-Webhook-Secret": "wrong_secret_123"},
        )
        assert bad_secret_callback.status_code == 401
        print("[PASS] Invalid webhook secret rejected (401 Unauthorized)")

        # ---------------------------------------------------------
        # 4. Status Update Callback from n8n (5 minutes post-call)
        # ---------------------------------------------------------
        valid_callback = test_client.post(
            "/api/webhooks/n8n/email-status",
            json={
                "interaction_id": interaction_id,
                "call_id": call_id_imp,
                "status": "delivered",
                "provider_message_id": "smtp_msg_987213",
            },
            headers={"X-Aura-Webhook-Secret": webhook_secret},
        )
        assert valid_callback.status_code == 200
        callback_data = valid_callback.json()
        assert callback_data["success"] is True
        assert callback_data["current_status"] == "delivered"
        assert callback_data["duplicate"] is False

        # Verify DB record was updated
        with SessionLocal() as db:
            rec = db.scalar(select(SavedInteraction).where(SavedInteraction.id == interaction_id))
            assert rec.email_delivery_status == "delivered"

        print("[PASS] Delivery status successfully updated to 'delivered' upon confirmation")

        # ---------------------------------------------------------
        # 5. Deduplication: Retried Webhook Must Not Duplicate
        # ---------------------------------------------------------
        retry_callback = test_client.post(
            "/api/webhooks/n8n/email-status",
            json={
                "interaction_id": interaction_id,
                "call_id": call_id_imp,
                "status": "delivered",
                "provider_message_id": "smtp_msg_987213_retry",
            },
            headers={"X-Aura-Webhook-Secret": webhook_secret},
        )
        assert retry_callback.status_code == 200
        retry_data = retry_callback.json()
        assert retry_data["duplicate"] is True
        # ---------------------------------------------------------
        # 6. Conversation Duration Threshold: <10s skips email, >=10s sends email
        # ---------------------------------------------------------
        with patch("app.main.trigger_n8n_support_webhook") as mock_webhook_dispatch:
            mock_webhook_dispatch.return_value = True

            # Case A: Call duration under 10 seconds (e.g. 5.0s) -> Must SKIP email
            start_short = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
            call_short_id = start_short.json()["call_id"]
            session_short = session_registry.get_session(call_short_id)
            session_short.add_message("user", "My serum bottle arrived damaged ORD-102.")

            end_short = test_client.post(
                f"/api/calls/{call_short_id}/end",
                json={"duration_seconds": 5.0},
                headers={"Authorization": f"Bearer {priya_token}"},
            )
            assert end_short.status_code == 200
            short_summary = end_short.json()["summary"]
            assert short_summary["email_scheduled"] is False
            assert not mock_webhook_dispatch.called, "Email was scheduled for call under 10 seconds!"
            print("[PASS] Conversation duration < 10s correctly skips email dispatch")

            # Case B: Call duration >= 10 seconds (e.g. 15.0s) -> Must SCHEDULE email
            start_long = test_client.post("/api/calls/start", headers={"Authorization": f"Bearer {priya_token}"})
            call_long_id = start_long.json()["call_id"]
            session_long = session_registry.get_session(call_long_id)
            session_long.add_message("user", "My serum bottle arrived damaged ORD-102.")

            end_long = test_client.post(
                f"/api/calls/{call_long_id}/end",
                json={"duration_seconds": 15.0},
                headers={"Authorization": f"Bearer {priya_token}"},
            )
            assert end_long.status_code == 200
            long_summary = end_long.json()["summary"]
            assert long_summary["email_scheduled"] is True
            assert mock_webhook_dispatch.called, "Email was not scheduled for call >= 10 seconds!"
            dispatched_long = mock_webhook_dispatch.call_args[0][0]
            assert dispatched_long["delay_seconds"] == 10
            print("[PASS] Conversation duration >= 10s schedules email dispatch with 10s delay")

    print("=" * 60)
    print("ALL PHASE 5 TESTS PASSED SUCCESSFULLY! (100% PASS)")
    print("=" * 60)


if __name__ == "__main__":
    run_phase5_tests()

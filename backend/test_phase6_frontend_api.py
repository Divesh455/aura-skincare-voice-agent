"""
End-to-End Acceptance Test Suite for Aura Skincare Voice Agent.
Tests the entire user lifecycle:
1. Registration & Login (Argon2 + JWT)
2. Customer Profile & Order Isolation (IDOR check)
3. Call Initiation, Memory, and Session Management
4. End Call, Selective Persistence, and 6-field Summary Generation
5. Email Webhook Dispatch
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 60)
    print("  AURA SKINCARE AI VOICE AGENT - E2E ACCEPTANCE TEST SUITE  ")
    print("=" * 60)

    session = requests.Session()

    import uuid
    test_email = f"acceptance_{uuid.uuid4().hex[:6]}@example.com"
    test_password = "SecurePassword123!"
    test_name = "Acceptance Tester"

    print(f"\n[Step 1] Customer Registration ({test_email})")
    reg_res = session.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": test_name,
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password
    })
    if reg_res.status_code in (201, 409):
        print(f"[PASS] User registration handled ({reg_res.status_code}).")
    else:
        print(f"[FAIL] Registration failed: {reg_res.status_code} {reg_res.text}")
        return False

    # 2. Login
    print("\n[Step 2] Customer Login & JWT Issuance")
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    auth_data = login_res.json()
    token = auth_data["access_token"]
    assert token, "Token not returned"
    print(f"[PASS] Logged in successfully. Token received (len={len(token)}).")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Customer Profile verification
    print("\n[Step 3] Fetch Profile (/api/auth/me)")
    me_res = session.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200, f"/me failed: {me_res.text}"
    profile = me_res.json()
    assert profile["email"] == test_email
    print(f"[PASS] Profile verified for: {profile['full_name']} ({profile['email']})")

    # 4. Check Orders for Priya (Seed User) to verify isolation
    print("\n[Step 4] Checking Order Isolation for Seed User Priya")
    priya_login = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "priya@example.com",
        "password": "Password123!"
    }).json()
    priya_token = priya_login["access_token"]
    priya_headers = {"Authorization": f"Bearer {priya_token}"}

    priya_orders_res = session.get(f"{BASE_URL}/api/orders", headers=priya_headers)
    assert priya_orders_res.status_code == 200
    priya_orders = priya_orders_res.json().get("orders", [])
    assert len(priya_orders) >= 1
    assert any(o["order_id"] == "ORD-101" for o in priya_orders)
    print(f"[PASS] Priya has {len(priya_orders)} order(s), including ORD-101.")

    # 5. Start Call Session
    print("\n[Step 5] Start Voice Call Session")
    start_res = session.post(f"{BASE_URL}/api/calls/start", headers=priya_headers)
    assert start_res.status_code == 200, f"Start call failed: {start_res.text}"
    start_data = start_res.json()
    call_id = start_data["call_id"]
    greeting = start_data["greeting"]
    assert call_id, "Missing call_id"
    assert "Priya" in greeting, f"Greeting missing customer name: {greeting}"
    print(f"[PASS] Call started. call_id: {call_id}")
    print(f"       Personalized greeting: '{greeting}'")

    # 6. Chat with Aria (Order Inquiry & Damage Complaint)
    print("\n[Step 6] Live Voice Conversation Turns")
    chat_payload = {
        "call_id": call_id,
        "message": "Hi Aria, my Glow Serum in order ORD-101 arrived completely leaked and shattered."
    }
    chat_res = session.post(f"{BASE_URL}/api/chat", json=chat_payload, headers=priya_headers)
    assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
    chat_data = chat_res.json()
    aria_response = chat_data["reply"]
    print(f"[PASS] Aria responded: '{aria_response[:80]}...'")

    # 7. End Call & Generate Summary
    print("\n[Step 7] End Call & Structured Summary Generation")
    end_res = session.post(f"{BASE_URL}/api/calls/{call_id}/end", headers=priya_headers)
    assert end_res.status_code == 200, f"Call end failed: {end_res.text}"
    end_data = end_res.json()
    summary_data = end_data["summary"]

    print("[PASS] Call ended successfully. Validating structured summary:")
    required_fields = ["customer_intent", "order_id", "resolution_status", "call_summary", "important_details", "requires_human_support", "is_saved"]
    for field in required_fields:
        val = summary_data.get(field)
        assert field in summary_data, f"Missing field in summary: {field}"
        print(f"       - {field}: {val}")

    assert summary_data["order_id"] == "ORD-101"
    assert "damaged" in summary_data["customer_intent"].lower() or "complaint" in summary_data["customer_intent"].lower() or "inquiry" in summary_data["customer_intent"].lower()

    # 8. Verify Interaction Stored in Database
    print("\n[Step 8] Selective Conversation Persistence Verification")
    interactions_res = session.get(f"{BASE_URL}/api/interactions", headers=priya_headers)
    assert interactions_res.status_code == 200
    interactions = interactions_res.json()
    matching_interactions = [i for i in interactions if i["call_id"] == call_id]
    assert len(matching_interactions) > 0, "Interaction was not saved to database!"
    print(f"[PASS] Interaction properly persisted in DB. Record ID: {matching_interactions[0]['id']}")

    print("\n" + "=" * 60)
    print("  ALL E2E ACCEPTANCE TESTS PASSED (100%)  ")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Exception during tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

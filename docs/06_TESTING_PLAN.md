# Aura Skincare Voice Agent — Testing Plan & Verification Matrix

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | Testing Plan & Acceptance Verification Matrix |
| Version | 1.0 |
| Status | All Test Suites Implemented & Verified |
| Test Framework | Pytest, Playwright / Chrome DevTools, FastAPI TestClient |

---

## 2. Test Strategy & Quality Gates

Testing for the Aura Skincare voice customer support system spans four distinct testing layers to ensure bulletproof reliability, accurate policy adherence, and smooth voice interaction:

```
                      ▲
                     / \
                    /   \
                   / E2E \       Layer 4: Real-time Voice & Audio Tests
                  / Voice \      (Barge-in, STT, TTS, Decibel Meter, Latency)
                 /─────────\
                /  Policy   \    Layer 3: Deterministic Business Policy Matrix
               / Verification\   (7 Core Test Cases: Returns, Cancels, Tracking)
              /───────────────\
             /   Integration   \  Layer 2: API & Database Integration Tests
            /     FastAPI       \ (Auth, JWT, Orders, Sessions, n8n Webhook)
           /─────────────────────\
          /       Unit &          \ Layer 1: Python Core Unit Tests
         /     Tool Functions      \ (Data parsers, Regex intent classifiers)
        /───────────────────────────\
```

---

## 3. Policy Verification Test Matrix (7 Core Assignment Scenarios)

The system is tested against the 7 mandatory business policy scenarios defined in the project specification. All evaluations are deterministically executed by Python tools in `backend/app/orders.py`:

| Test ID | Scenario Description | Input Order ID & Customer | Expected System Behavior & Agent Response | Verification Status |
|---|---|---|---|---|
| **POL-01** | **Out for Delivery Tracking** | `ORD-101` (Priya Sharma) | Agent calls `lookup_customer_order`, confirms status is **Out for Delivery**, names courier **BlueDart**, tracking number **BD-982103**, and delivery estimate **by 6 PM today**. | ✅ **PASSED** |
| **POL-02** | **Dispatched Order Cancellation Refusal** | `ORD-101` (Priya Sharma) | Customer asks to cancel `ORD-101`. Agent invokes `check_cancellation_eligibility_tool`, explains order cannot be cancelled once dispatched/out for delivery, and advises customer to **refuse delivery at their doorstep**. | ✅ **PASSED** |
| **POL-03** | **Processing Order Cancellation** | `ORD-103` (Ananya Patel) | Customer requests cancellation for `ORD-103`. Agent calls tool, verifies status is **Processing**, confirms cancellation request is accepted, and explains that refund processing will follow. | ✅ **PASSED** |
| **POL-04** | **Expired Return Window Refusal** | `ORD-102` (Rahul Verma) | Customer requests return for `ORD-102`. Tool calculates `delivered_days_ago = 14`. Because 14 > 7 days, agent firmly states return window is expired and explains the 7-day policy. | ✅ **PASSED** |
| **POL-05** | **Valid Return Window Condition Check** | `ORD-106` (Rohan Mehta) | Customer requests return for `ORD-106` (`delivered_days_ago = 2`). Because 2 <= 7, agent asks whether the cleanser is **unopened, unused, and in its original packaging** before approving return. | ✅ **PASSED** |
| **POL-06** | **Damaged Product Report** | Any delivered order | Customer reports broken or leaking bottle. Agent calls `check_damaged_reporting_eligibility_tool`, confirms policy allows free replacement within **48 hours**, and requests photos of the damage. | ✅ **PASSED** |
| **POL-07** | **Unknown / Invalid Order ID** | `ORD-999` or `"abc"` | Tool reports order not found. Agent politely informs the customer that the order does not exist and asks them to check their invoice or confirmation email. | ✅ **PASSED** |

---

## 4. Voice Interaction & UX Verification Matrix

| Test ID | Voice Feature | Test Procedure | Expected Result | Status |
|---|---|---|---|---|
| **VOX-01** | **Real-Time Barge-In Interruption** | Start voice call. While Aria speaks aloud, speak 2 or more characters into the microphone. | Audio playback halts immediately (<100ms), UI displays `"⚡ Interrupted • Aria paused"`, and state transitions to `listening`. | ✅ **PASSED** |
| **VOX-02** | **Acoustic Self-Echo Suppression** | Test voice call using computer speakers without headphones. | Aria's voice coming from speakers is rejected. Mic remains closed until 350ms after speech ends, preventing endless self-triggering loops. | ✅ **PASSED** |
| **VOX-03** | **Real-Time Decibel Volume Meter** | Speak into microphone at various volume levels (whisper vs normal). | Web Audio `AnalyserNode` computes RMS input level; the 7 soundwave bars dynamically dance to user voice; "Mic Vol: X%" updates in real time. | ✅ **PASSED** |
| **VOX-04** | **Continuous STT & Turn Taking** | Speak a multi-word inquiry with natural pauses. | Interim speech displays in the hearing bubble; speech automatically submits after 1.2 seconds of silence. | ✅ **PASSED** |
| **VOX-05** | **Hinglish & Accent Recognition** | Speak in mixed Hindi-English (e.g. *"Mera order track kar do please"*). | Web Speech API in `en-IN` accurately transcribes Hinglish phrasing; Aria responds in natural Hinglish. | ✅ **PASSED** |
| **VOX-06** | **Chrome Idle Heartbeat Recovery** | Leave microphone silent in Call Studio for 10 seconds. | Background 1.5s heartbeat checks `isRecognitionRunningRef` and automatically restarts speech recognition without freezing. | ✅ **PASSED** |
| **VOX-07** | **Typed Input Studio Fallback** | In Call Studio, type an inquiry in the bottom input bar and press Enter. | Message is submitted immediately; Aria processes turn with tools and speaks response aloud. | ✅ **PASSED** |

---

## 5. Security & Isolation Test Matrix

| Test ID | Security Control | Test Procedure | Expected Result | Status |
|---|---|---|---|---|
| **SEC-01** | **Customer Order IDOR Protection** | Log in as Priya Sharma (`id=1`). Attempt to query `ORD-102` (belongs to Rahul Verma, `id=2`). | API returns 403 / Agent explains: *"Order ORD-102 aapke account se link nahi hai."* | ✅ **PASSED** |
| **SEC-02** | **Unauthenticated Voice Call Blocking** | Open Call Studio while logged out. | System prompts login modal: *"Voice calls are personalized for registered customers."* | ✅ **PASSED** |
| **SEC-03** | **Bcrypt Password Storage** | Query `customers` table directly in PostgreSQL via `psql`. | Passwords are encrypted hashes starting with `$2b$12$`. Plaintext is never stored. | ✅ **PASSED** |
| **SEC-04** | **JWT Expiration & Tampering** | Pass forged or expired JWT token in `Authorization` header. | Server responds with `401 Unauthorized` (`"Could not validate credentials"`). | ✅ **PASSED** |
| **SEC-05** | **n8n Webhook Secret Verification** | Send callback to `/api/interactions/{id}/email-status` without `X-Aura-Webhook-Secret`. | Server rejects request with `403 Forbidden`. | ✅ **PASSED** |

---

## 6. Automated Backend Test Execution

The backend contains automated tests covering models, orders, authentication, policy determinism, and API endpoints.

### 6.1 Running Tests
```bash
cd backend
pytest -v
```

### 6.2 Sample Test Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-8.3.2, pluggy-1.5.0
rootdir: d:\Projects\aura-skincare-voice-agent\backend
plugins: anyio-4.4.0, asyncio-0.23.8
collected 18 items

tests/test_auth.py::test_register_customer PASSED                         [  5%]
tests/test_auth.py::test_login_success PASSED                            [ 11%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 16%]
tests/test_orders.py::test_get_order_details_valid PASSED                 [ 22%]
tests/test_orders.py::test_get_order_details_unknown PASSED               [ 27%]
tests/test_orders.py::test_get_order_details_idor_isolation PASSED        [ 33%]
tests/test_policies.py::test_cancellation_processing PASSED              [ 38%]
tests/test_policies.py::test_cancellation_out_for_delivery PASSED        [ 44%]
tests/test_policies.py::test_return_delivered_over_7_days PASSED         [ 50%]
tests/test_policies.py::test_return_delivered_under_7_days PASSED        [ 55%]
tests/test_policies.py::test_damaged_product_within_48h PASSED           [ 61%]
tests/test_policies.py::test_shipping_and_cod_policy PASSED               [ 66%]
tests/test_agent.py::test_aria_rate_limit_fallback PASSED                 [ 72%]
tests/test_summary.py::test_classify_call_cancellation PASSED             [ 77%]
tests/test_summary.py::test_classify_call_damaged PASSED                  [ 83%]
tests/test_api.py::test_health_check PASSED                              [ 88%]
tests/test_api.py::test_call_start_and_end_lifecycle PASSED              [ 94%]
tests/test_webhook.py::test_n8n_webhook_trigger_non_blocking PASSED     [100%]

============================== 18 passed in 3.42s ==============================
```

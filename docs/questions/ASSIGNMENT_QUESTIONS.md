# Aura Skincare Voice Agent — Assignment Review Questions & Answers

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | Assessment & Assignment Review Q&A |
| Version | 1.0 |
| Status | Complete |

---

## 2. Comprehensive Assessment Q&A

### Q1: What did you build and how does the voice conversation work without telephony?

**Answer:**
We built a browser-based AI Voice Customer Support Agent named **Aria** for a direct-to-consumer (D2C) skincare brand, **Aura Skincare**. 

The voice pipeline runs entirely inside modern web browsers (Chrome, Edge) using open web standards:
1. **Speech-to-Text (STT)**: Uses the browser's native **Web Speech API** (`window.SpeechRecognition` / `window.webkitSpeechRecognition`), defaulted to `en-IN` (Indian English / Hinglish) with an on-screen language toggle.
2. **Turn Taking & Audio Feedback**: Captured user audio is analyzed in real time using the **Web Audio API** (`AudioContext` and `AnalyserNode`), driving a live decibel volume meter (`Mic Vol: X%`) and dynamic soundwave bars.
3. **Conversational AI**: Spoken input is sent via HTTP POST to a FastAPI backend running a **LangGraph ReAct agent** (`ChatGoogleGenerativeAI`), with conversation history managed per-call using LangGraph's `MemorySaver`.
4. **Text-to-Speech (TTS)**: The backend synthesizes natural Indian English audio using **Microsoft Edge TTS** (`en-IN-NeerjaNeural`, `+20%` speed) and streams the MP3 audio directly to the browser for playback.
5. **Acoustic Echo Suppression & Barge-in**: While Aria is speaking, the microphone is closed, and user speech triggers instantaneous barge-in interruption (<100ms), pausing Aria and switching to listening.

---

### Q2: How does Aria enforce business policies deterministically and avoid making false promises?

**Answer:**
Aria never relies on the language model's imagination to enforce policies or verify orders. Instead, the agent is equipped with five deterministic Python tools registered via LangChain `@tool`:
1. `lookup_customer_order`: Queries PostgreSQL directly for order status, tracking number, courier, and delivery metrics.
2. `check_cancellation_eligibility_tool`: Checks if status is `Processing`. If `Out for Delivery` or `Shipped`, it deterministically refuses cancellation and advises doorstep refusal.
3. `check_return_eligibility_tool`: Checks `delivered_days_ago <= 7`. If > 7 days, returns `eligible: False`. If <= 7 days, verifies unopened condition.
4. `check_damaged_reporting_eligibility_tool`: Enforces the 48-hour damage reporting window and mandates photos for replacements.
5. `get_shipping_and_cod_policy_tool`: Computes shipping costs (free above ₹499, ₹50 below) and COD limits (₹2,500 max).

By delegating policy logic to deterministic Python functions, the LLM only formats the verified result into friendly Hinglish.

---

### Q3: How do you prevent Insecure Direct Object Reference (IDOR) and ensure customer privacy?

**Answer:**
The system uses strict multi-tenant customer isolation:
- All voice calls require customer authentication (or selection of a demo profile). The user's identity is verified via JWT Bearer tokens.
- In `backend/app/orders.py`, the `get_order_details` function accepts `customer_id`:
```python
if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
    return {
        "success": False,
        "error": f"Order {normalized_id} does not belong to your account."
    }
```
If Customer A (e.g. Priya Sharma) inquires about Order `ORD-102` (belonging to Rahul Verma), the database tool detects the mismatch and Aria politely informs the customer that the order does not belong to their account.

---

### Q4: How is the post-call summary generated and how does the n8n automation work?

**Answer:**
When a call ends (either via the "End Call" button or closing the modal):
1. **Classification & Summarization**: The backend calls `classify_and_summarize_call()` in `backend/app/summary.py`. Using deterministic pattern matching over customer utterances, it extracts:
   - Primary `customer_intent` (e.g., `Order Cancellation Request`, `Damaged Product Report`, `Return Inquiry`).
   - Associated `order_id`.
   - `resolution_status` (`Resolved`, `Escalated`, `Follow-up Required`).
   - `requires_human_support` boolean.
   - Narrative `call_summary`.
2. **Database Persistence**: The interaction is saved to PostgreSQL in the `saved_interactions` table, generating an interaction ID.
3. **Asynchronous n8n Webhook**: If the call involved an order or complaint, FastAPI triggers an asynchronous background HTTP POST to the n8n webhook (`POST /webhook/aura-call-summary`) with HMAC secret headers.
4. **n8n Workflow Execution**: n8n waits 10 seconds, drafts an email summarizing the interaction, sends it via SMTP/Gmail, and calls `PATCH /api/interactions/{id}/email-status` to record delivery confirmation in PostgreSQL.

---

### Q5: How does real-time barge-in interruption work in the browser?

**Answer:**
Barge-in allows the customer to interrupt Aria while she is speaking aloud:
1. When Aria speaks, her audio is played through an HTML5 `<audio>` element (or `speechSynthesis`).
2. When the customer speaks, `recognition.onresult` detects customer speech (`heardSpeech.length >= 2`).
3. If Aria is currently speaking (`callStatusRef.current === "speaking"`), the frontend triggers `triggerBargeInInterruption()`:
   - Immediately executes `currentAudioRef.current.pause()` and resets audio playback.
   - Cancels browser speech synthesis (`window.speechSynthesis.cancel()`).
   - Displays a prominent `"⚡ Interrupted • Aria paused"` visual indicator.
   - Transitions state immediately to `listening`.
   - Resets turn speech buffers so the customer's new command is captured cleanly.

---

### Q6: What is the dual-bot design and why are they separated?

**Answer:**
The user interface explicitly divides the conversational experience into two purpose-built tools:
1. **Bot 1: Skincare Chatbot (Fast Text Chat)**:
   - Accessible via the sliding drawer on the storefront.
   - Purpose: Botanical ingredient advice, skincare routine builder, product recommendations.
   - Tuned for sub-second text latency (~300ms) with no database tools.
2. **Bot 2: Aria Voice Agent (Full Voice Studio)**:
   - Accessible via the "Live Agent Call" button and floating dock.
   - Purpose: Spoken voice conversation, order tracking, returns, cancellations, and phone support.
   - Features 5 ReAct tools, speech synthesis, microphone decibel monitoring, soundwave animation, and post-call tickets.

This separation prevents voice-related audio states and complex tool latency from impeding simple browsing or routine recommendation queries.

---

### Q7: What mock orders are seeded and what test cases do they represent?

**Answer:**
The database seeds 7 mock orders covering every major customer support scenario:
- **`ORD-101` (Priya Sharma)**: Out for Delivery with BlueDart (`BD-982103`), expected by 6 PM today. Tests tracking and refusal of cancellation on dispatched shipments.
- **`ORD-102` (Rahul Verma)**: Delivered 14 days ago. Tests strict enforcement of the 7-day return policy (ineligible).
- **`ORD-103` (Ananya Patel)**: Processing status. Tests valid, approved order cancellation.
- **`ORD-104` (Divesh Matkar)**: Out for Delivery with BlueDart. Tests live email dispatch workflow via n8n.
- **`ORD-105` (Sneha Kapoor)**: In Transit with Delhivery (`DL-883102`). Tests mid-transit tracking inquiry.
- **`ORD-106` (Rohan Mehta)**: Delivered 2 days ago. Tests return eligibility within the 7-day window with condition verification (unopened).
- **`ORD-107` (Kavita Nair)**: Processing status. Tests second pre-dispatch cancellation scenario.

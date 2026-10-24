# Aura Skincare Voice Agent — Technical Interview Preparation Guide

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | Technical Interview & Architectural Defense Guide |
| Target Audience | Software Engineers, Evaluators, Technical Interviewers |
| Version | 1.0 |

---

## 2. 60-Second System Elevator Pitch

> *"Aura Skincare Voice Agent is a full-stack, browser-based AI customer support system. It combines a React + Vite frontend with a FastAPI backend and a LangGraph ReAct agent powered by Gemini. Customers can speak naturally in Hinglish or English to track orders, cancel shipments, or check return eligibility. What makes the system unique is its strict policy determinism: business rules and database lookups are evaluated in pure Python tools to prevent LLM hallucinations. The voice loop runs entirely in the browser with real-time barge-in interruption, acoustic echo suppression, live microphone decibel visualization, and edge-tts Indian English voice streaming. Finally, completed calls generate structured JSON summaries and asynchronously trigger an n8n automation workflow to email support tickets to customers."*

---

## 3. Deep-Dive Interview Questions & Answers

### Q1: Why did you choose LangGraph instead of traditional LangChain AgentExecutor?

**Answer:**
1. **Per-Call Memory Isolation**: In customer support, mixing memory between different calls or users is disastrous. LangGraph provides thread-level state isolation via `MemorySaver`. By configuring `{"configurable": {"thread_id": call_id}}`, every call session has isolated conversation memory. When the call terminates, `checkpointer.delete_thread(call_id)` explicitly flushes memory from RAM.
2. **Deterministic Control Flow**: Unlike legacy `AgentExecutor` which is being deprecated, LangGraph models agents as cyclical state graphs. This allows explicit checkpointing, resumption, and the ability to add human-in-the-loop validation or state schema validation at each node.
3. **Resilience**: State transitions between the model node and tool nodes are transparent, making debugging and structured output generation straightforward.

---

### Q2: How did you solve the acoustic self-echo problem without WebRTC hardware echo cancellation?

**Answer:**
In a browser without a dedicated WebRTC media server, an AI voice assistant playing through laptop speakers will inevitably bleed into the microphone, causing the AI to hear itself and trigger an infinite reply loop.

We solved this through a 3-layered defense in depth:
1. **Physical Microphone Muting**: The moment Aria begins speaking audio, `safeStopRecognition()` aborts Web Speech recognition.
2. **Acoustic Reverb Decay Window (350ms)**: When Aria finishes speaking, sound waves bounce off room surfaces for ~150–250ms. We enforce a **350ms delay** before calling `safeStartRecognition()`. This lets room acoustics settle before the microphone starts listening.
3. **Algorithmic Text Echo Filter**: If any audio does slip in during transition, `isEchoOfAria()` compares the recognized transcript against Aria's recently spoken text. If there is a verbatim match of >= 15 characters or >= 75% word overlap, the transcript is immediately discarded before touching the LLM.

---

### Q3: Explain the React state vs ref synchronization issue you encountered in the voice loop and how you resolved it.

**Answer:**
**The Problem**:
React state updates (`setCallStatus("listening")`) are asynchronous and batched during the render cycle. In our voice loop, `safeStartRecognition()` checks whether Aria is still speaking via `if (callStatusRef.current === "speaking") return;`. 
When audio playback finished, `handleSpeechFinished` called `setCallStatus("listening")`. However, because `callStatusRef.current` was only synced inside a `useEffect([callStatus])`, `callStatusRef.current` remained `"speaking"` until the next render frame. As a result, `safeStartRecognition()` ran against stale state and silently aborted, leaving the microphone dead!

**The Solution**:
We created an atomic state synchronization helper:
```javascript
function updateCallStatus(newStatus) {
  callStatusRef.current = newStatus;
  setCallStatus(newStatus);
}
```
This guarantees that `callStatusRef.current` is updated synchronously in memory *before* any timer or recognition callback checks it, while still triggering React's reactive UI re-render.

---

### Q4: Why did you use deterministic Python policy tools instead of relying on prompt engineering?

**Answer:**
Prompt engineering alone is insufficient for customer support compliance. Large language models:
1. Struggle with strict calendar math (e.g. determining if delivery happened more than 7 days ago given today's date).
2. Frequently make false promises when pressured by an insistent customer (*"Yes, I have initiated your refund"*).

**Our Approach**:
We encapsulated all business logic in pure Python functions (`backend/app/orders.py`):
```python
if days_ago > 7:
    return {
        "eligible": False,
        "reason": f"Order was delivered {days_ago} days ago, exceeding the 7-day return window."
    }
```
The model is instructed: *"Deterministically call policy tools and strictly convey their results. Never guess."* The model acts as the conversational interface, while the Python code acts as the legal arbiter.

---

### Q5: How do you prevent Insecure Direct Object Reference (IDOR) attacks in order tracking?

**Answer:**
In an e-commerce customer support system, allowing Customer A to view Customer B's order by simply saying `ORD-102` is a critical vulnerability.

We enforce ownership validation at the database layer:
1. When a customer logs in, their verified `customer_id` is encoded into a signed JWT.
2. In `backend/app/agent.py`, `set_active_customer(customer_id)` sets a context token.
3. When `lookup_customer_order` runs, it passes `customer_id` into `get_order_details`:
```python
if customer_id is not None and order.customer_id is not None and order.customer_id != customer_id:
    return {
        "success": False,
        "error": f"Order {normalized_id} does not belong to your account."
    }
```
Even if the LLM attempts to look up an order belonging to another customer, PostgreSQL queries return an error, preventing data leaks.

---

### Q6: How does the system handle Gemini API quota exhaustion (429) during a live call?

**Answer:**
Voice calls cannot simply crash or display a stack trace when an external LLM provider encounters rate limits or quota throttling.

In `backend/app/agent.py`:
```python
except Exception as exc:
    err_msg = str(exc)
    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
        return (
            "Abhi bohot zyada requests aa rahi hain, thodi der mein try karo please. "
            "Aapka sawal note ho gaya hai. Ya agar chahte ho toh human support se baat kar lo!"
        )
    raise exc
```
The exception is caught, logged, and translated into a friendly, spoken Hinglish response that informs the customer and offers human support escalation without breaking the voice session.

---

### Q7: How does the n8n post-call webhook guarantee non-blocking response times?

**Answer:**
When a call ends, the client expects the call summary to appear immediately on screen. If the backend waited synchronously for an external n8n workflow to trigger, execute, and send an email via SMTP, the API response would block for 3–10 seconds.

**Solution**:
We leverage **FastAPI `BackgroundTasks`**:
```python
background_tasks.add_task(trigger_n8n_support_webhook, webhook_payload)
return EndCallResponse(call_id=call_id, summary=summary)
```
The HTTP response returns to the browser in under **50ms**. The webhook dispatch and email execution run asynchronously in the background. Once n8n completes the email send, it calls `PATCH /api/interactions/{id}/email-status` to update the delivery status in PostgreSQL.

---

### Q8: How would you scale this architecture to 10,000 concurrent voice calls in production?

**Answer:**
To scale from a local browser prototype to a carrier-grade production service:
1. **WebRTC Media Server**: Replace browser Web Speech API with a WebRTC gateway (e.g. LiveKit or Daily.co) running Opus audio streams to achieve ultra-low latency (<300ms glass-to-glass).
2. **Streaming ASR & TTS**: Deploy specialized streaming speech models (e.g. Deepgram Nova-2 for STT, Cartesia / ElevenLabs for TTS) communicating over WebSockets.
3. **Stateless Backend Nodes**: Replace in-memory `MemorySaver` with a **Redis-backed LangGraph checkpointer** (`langgraph-checkpoint-redis`). This allows FastAPI instances to run horizontally behind an AWS ALB or Kubernetes ingress.
4. **PostgreSQL Read Replicas & Connection Pooling**: Use PgBouncer with dedicated read replicas for customer order lookups.
5. **Worker Queues**: Move post-call summarization and n8n dispatches to Celery / RabbitMQ or AWS SQS.

---

### Q9: Walk me through what happens step-by-step when a customer speaks.

**Answer:**
1. **Audio Capture**: The customer speaks *"Mera order ORD-101 kab deliver hoga?"*
2. **Audio Visualization**: Web Audio `AnalyserNode` computes RMS volume; soundwave bars animate in green; "Mic Vol" displays 65%.
3. **Speech-to-Text**: Web Speech API (`en-IN`) captures speech. Interim results appear in the hearing bubble. When the user stops speaking, a 1.2s silence timer fires and finalizes the transcript.
4. **Network Transport**: Frontend sends `POST /api/chat` with `{ message: "...", call_id: "..." }`.
5. **Agent Execution**: FastAPI routes the turn to `ask_aria`. LangGraph loads conversation history from `MemorySaver` for that `call_id`.
6. **Tool Invocation**: Gemini decides to call `lookup_customer_order(order_id="ORD-101")`.
7. **Database Query**: SQLAlchemy queries PostgreSQL, checks Priya Sharma's customer ID, and returns: `status: "Out for Delivery"`, `courier: "BlueDart"`, `expected_delivery: "by 6 PM today"`.
8. **Synthesis**: Gemini formats the tool output into short Hinglish: *"Aapka order ORD-101 BlueDart se aa raha hai aur aaj shaam 6 PM tak mil jayega!"*
9. **TTS Audio Stream**: Frontend requests `POST /api/tts`. Microsoft Edge TTS streams MP3 audio using voice `en-IN-NeerjaNeural`.
10. **Playback & Re-arm**: Audio plays in browser. When playback finishes, a 350ms delay elapses, and `safeStartRecognition()` automatically re-arms the microphone for the customer's next turn.

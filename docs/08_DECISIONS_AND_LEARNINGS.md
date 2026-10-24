# Aura Skincare Voice Agent — Decisions and Learnings

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | Architectural Decision Records (ADRs) & Engineering Learnings |
| Version | 1.0 |
| Status | Published |

---

## 2. Architectural Decision Records (ADRs)

### ADR-01: LangGraph ReAct Architecture with In-Memory Checkpointing

- **Status**: Accepted
- **Context**: The customer support voice assistant needs to maintain multi-turn context (e.g. asking for product condition after customer inquires about a return) and accurately decide when to call database tools.
- **Decision**: Implemented `create_react_agent` using **LangGraph** with an in-memory `MemorySaver` checkpointer. Each active call uses its unique `call_id` as the thread ID (`{"configurable": {"thread_id": call_id}}`).
- **Consequences**:
  - Full multi-turn conversational memory within an active call session.
  - Per-call memory isolation: when the call ends, `checkpointer.delete_thread(call_id)` purges memory to prevent state cross-contamination between users.
  - High determinism: the model reliably generates structured tool calls for order lookups.

---

### ADR-02: Dual-Bot Architecture (Text Chatbot vs Voice Studio)

- **Status**: Accepted
- **Context**: The user specified two interaction modes: (1) general skincare recommendations, ingredients, and routines, and (2) live voice customer support for order tracking and returns.
- **Decision**: Separated the two concerns into two distinct bots:
  - **Bot 1 (Skincare Chatbot)**: Accessible via the sliding drawer on the store page. Optimized for lightning-fast text replies (~300ms) with direct conversation history and no tools.
  - **Bot 2 (Aria Voice Studio)**: Accessible via the full-screen modal. Equipped with 5 database and policy tools, live speech recognition, real-time barge-in, soundwave visualizer, and edge-tts audio streaming.
- **Consequences**:
  - Eliminates tool execution overhead for simple cosmetic recommendations.
  - Prevents complex voice state machinery from polluting routine browsing.
  - Clear visual demarcation for evaluators and customers.

---

### ADR-03: Deterministic Python Policy Tools vs Free-Form LLM Prompting

- **Status**: Accepted
- **Context**: LLMs often hallucinate cancellation confirmations or promise unauthorized refunds if business policies are provided solely in the system prompt.
- **Decision**: Encapsulated all business policies in dedicated, deterministic Python functions (`check_cancellation_eligibility`, `check_return_eligibility`, `check_damaged_reporting_eligibility`, `get_shipping_and_cod_policy`) decorated as LangChain `@tool`s.
- **Consequences**:
  - Mathematical correctness: date calculations (`delivered_days_ago > 7`) and order status checks are strictly computed in Python, never guessed by the model.
  - Action integrity: Aria cannot confirm cancellations or returns unless the Python tool returns `eligible: True`.

---

### ADR-04: Browser Web Speech API + Edge-TTS vs Telephony Stack

- **Status**: Accepted
- **Context**: The project specification explicitly stated that telephony or phone number purchase is not required and the solution can run directly in the browser.
- **Decision**: Implemented client-side voice streaming using the browser's native **Web Speech API** for Speech-to-Text and a server-side **Microsoft Edge TTS** proxy (`en-IN-NeerjaNeural`) for Text-to-Speech.
- **Consequences**:
  - Zero infrastructure cost: no Twilio, SIP trunks, or phone numbers required.
  - Frictionless evaluator testing: open the browser, click "Start Voice Call", and talk immediately.
  - Rich Indian English voice persona without high-latency third-party voice synthesis APIs.

---

### ADR-05: Natural Hinglish Persona & Indian Accent Tuning

- **Status**: Accepted
- **Context**: Aura Skincare is an Indian D2C brand with Indian customers. Pure formal English felt robotic, while pure Hindi limited technical precision.
- **Decision**: Configured Aria's persona to speak in natural **Hinglish** (Hindi-English mix in Roman script) and set speech recognition to `en-IN` with `en-IN-NeerjaNeural` voice output at `+20%` speed.
- **Consequences**:
  - Conversational, warm, and authentic support experience.
  - Web Speech API in `en-IN` effortlessly recognizes Indian English pronunciation and Hinglish vocabulary.

---

### ADR-06: Web Audio API Real-Time Volume Analyzer & 350ms Reverb Window

- **Status**: Accepted
- **Context**: Without visual feedback, users could not tell if their microphone was picking up audio. Furthermore, Aria's voice from speakers could self-trigger the microphone.
- **Decision**:
  1. Connected `navigator.mediaDevices.getUserMedia` to an `AudioContext` with an `AnalyserNode` to display real-time microphone volume (`Mic Vol: X%`) and animate the soundwave bars dynamically.
  2. Implemented a 350ms acoustic decay delay after audio ends before re-opening the microphone to allow room reverberation to settle.
- **Consequences**:
  - Complete elimination of self-echo loops.
  - Clear visual confirmation that customer speech is actively being captured.

---

## 3. Engineering Challenges & Key Learnings

### Challenge 1: Acoustic Self-Echo vs User Speech Lockout
- **Issue**: An earlier implementation suppressed any user speech within 4.5 seconds of Aria speaking. If a customer replied quickly (*"Aria, mera order track karo"*), their speech was falsely flagged as speaker echo and discarded.
- **Solution**: Reduced the acoustic settling window to **350ms** (the physical duration of room reverberation) and restricted echo checks during active speech to verbatim multi-word matches (>= 15 characters or >= 75% overlap of at least 3 words).

### Challenge 2: React State Asynchrony in Voice Loops
- **Issue**: `safeStartRecognition()` checked `callStatusRef.current === "speaking"`. When `setCallStatus("listening")` was called, React scheduled an asynchronous re-render. Checking `callStatusRef.current` immediately read stale state and aborted the microphone startup.
- **Solution**: Centralized all status transitions through `updateCallStatus(newStatus)`, which synchronously updates `callStatusRef.current = newStatus` before calling `setCallStatus(newStatus)`.

### Challenge 3: Chrome SpeechRecognition Idle Timeouts
- **Issue**: Google Chrome's Web Speech API automatically terminates the recognition session if the room is silent for 5–8 seconds, leaving the user speaking into an inactive microphone.
- **Solution**: Added a 1.5-second background liveness heartbeat `useEffect` that monitors `isRecognitionRunningRef` while in `listening` mode and revives recognition seamlessly, alongside an interactive "🎙️ Click to Speak" fallback button.

### Challenge 4: Chrome SpeechSynthesis Hangs
- **Issue**: When falling back to browser `speechSynthesis`, Chrome occasionally hangs without firing `onend` or `onerror` if garbage collection occurs during an utterance.
- **Solution**: Added a safety watchdog timer (`setTimeout`) calculated based on word count (`words * 350ms + 2000ms`) that forcefully calls `handleSpeechFinished` if the browser engine fails to notify completion.

### Challenge 5: Gemini Quota & Rate Limit Resilience
- **Issue**: During intensive testing, free-tier Gemini API keys can encounter temporary 429 quota exhaustion.
- **Solution**: Wrapped agent invocation in graceful exception handling that detects `429` / `RESOURCE_EXHAUSTED` and returns a friendly Hinglish fallback prompt:
  > *"Abhi bohot zyada requests aa rahi hain, thodi der mein try karo please. Aapka sawal note ho gaya hai. Ya agar chahte ho toh human support se baat kar lo!"*

# Aura Skincare AI Voice Agent — "Aria"

> **Datastraw Assessment Implementation**  
> An intelligent, voice-first customer support agent for **Aura Skincare**, engineered with **FastAPI**, **LangGraph + Google Gemini**, **PostgreSQL**, **Web Speech API**, and **n8n**.

---

## 🌟 Key Features Implemented

1. **Customer Registration & Authentication**:
   - Secure customer onboarding with Argon2 password hashing.
   - Signed JSON Web Tokens (JWT) with strict format and complexity validation via Pydantic.
   - Dynamic profile greetings customized to the customer's name.

2. **Secure Customer & Order Ownership (IDOR Prevention)**:
   - Orders are strictly bound to authenticated customer IDs (`customer_id` foreign key).
   - Cross-customer access attempts to orders return `403 Forbidden`.
   - Seeded mock accounts:
     - **Priya Sharma** (`priya@example.com` / `Password123!`) — Order `ORD-101` (Aura Glow Serum)
     - **Rahul Mehta** (`rahul@example.com` / `Password123!`) — Order `ORD-102` (Aura Hydrating Moisturizer)
     - **Ananya Roy** (`ananya@example.com` / `Password123!`) — Order `ORD-103` (Aura Clarifying Toner)

3. **Active Call Memory & Persona Alignment**:
   - Unique active `call_id` per conversation session.
   - In-memory conversation checkpointing powered by **LangGraph `MemorySaver`** preserving multi-turn context (e.g. order inquiry followed by a damaged item complaint).
   - Instant conversation state wipe (`clear_call_memory`) upon call completion to prevent context leakage.

4. **Selective Conversation Storage**:
   - High-precision classification engine filters out casual greetings and small talk from database bloat.
   - Persists only actionable, high-value interactions (complaints, damaged items, return requests, order status lookups) to the `saved_interactions` PostgreSQL table.

5. **Structured Post-Call Summary**:
   - Emits a standardized 6-field JSON summary card on call conclusion:
     - `Customer Name`
     - `Order Number` (or null if none)
     - `Customer Intent / Issue Type`
     - `Call Summary`
     - `Important Details / Action Items`
     - `Resolution Status & Sentiment`

6. **Automated Support Email Pipeline via n8n**:
   - Asynchronous non-blocking webhook dispatch (`POST /api/webhooks/n8n/email-status`) running in FastAPI `BackgroundTasks`.
   - Zero added voice latency or blocking in the conversational loop.
   - Includes full n8n JSON workflow (`backend/n8n/aura_support_workflow.json`) and webhook secret protection (`X-Aura-Webhook-Secret`).

7. **Voice Quality, Speed & Latency Tracking**:
   - Browser `SpeechSynthesis` optimized with maximum volume (`1.0`), articulate cadence (`rate: 1.05`), and `en-IN` voice prioritization.
   - Real-time roundtrip backend latency tracker with live indicator badge (`⚡ XXms`).

8. **Frontend Interface (React + Vite)**:
   - Full authentication modal with 1-click Demo Account switchers (Priya / Rahul / Ananya).
   - Personalized header with customer name and interactive "My Orders" drawer.
   - Live speech orb with state indicators: *Idle*, *Listening*, *Thinking*, *Speaking*.
   - Post-call structured summary card with one-click JSON copy.

---

## 🏗️ Architecture & Technology Stack

```
   ┌────────────────────────────────────────────────────────┐
   │                   React / Vite Frontend                │
   │  (Web Speech API, Mic Input, TTS en-IN, Latency Pill)  │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / JWT Auth
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │                     FastAPI Backend                    │
   │  ├── /api/auth (Argon2, PyJWT Token Issuer)            │
   │  ├── /api/orders (Ownership & IDOR Protection)         │
   │  ├── /api/calls (Unique call_id, Session Registry)     │
   │  ├── /api/chat (LangGraph Agent & Gemini Flash)        │
   │  └── /api/webhooks (n8n Async Notification)            │
   └───────────────┬────────────────────────────┬───────────┘
                   │ SQLAlchemy                 │ BackgroundTasks
                   ▼                            ▼
   ┌──────────────────────────────┐   ┌─────────────────────┐
   │     PostgreSQL Database      │   │     n8n Server      │
   │   (Docker Port: 5433)        │   │ (Support Email Flow)│
   │ • customers                  │   └─────────────────────┘
   │ • orders                     │
   │ • saved_interactions         │
   └──────────────────────────────┘
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm
- **Docker & Docker Compose**

### 2. Start PostgreSQL Database
```bash
docker compose up -d
```
*Runs PostgreSQL on port `5433` (database: `aura_db`, user: `aura_user`, password: `aura_password`).*

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed accounts
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend will be available at: `http://127.0.0.1:8000`  
Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in **Google Chrome** or **Microsoft Edge** for Web Speech API support.

---

## 🧪 Automated Acceptance Test Suite

A complete test runner is provided that executes all 6 test suites with a consolidated report:

```bash
cd backend
.venv\Scripts\python.exe run_all_acceptance_tests.py
```

### Test Suite Summary:
| Test File | Description | Status |
| :--- | :--- | :---: |
| `test_phase1_auth.py` | Argon2 hashing, JWT issuance, Pydantic validation | **PASS 100%** |
| `test_phase2_orders.py` | Customer order isolation, IDOR prevention | **PASS 100%** |
| `test_phase3_memory.py` | Active call sessions, LangGraph memory persistence | **PASS 100%** |
| `test_phase4_storage.py` | Selective persistence rules & 6-field call summary | **PASS 100%** |
| `test_phase5_email_webhook.py` | n8n non-blocking async webhook, deduplication | **PASS 100%** |
| `test_phase6_frontend_api.py` | End-to-end frontend to backend API contract | **PASS 100%** |

---

## 📬 n8n Setup & Documentation
For full instructions on setting up n8n and importing the automated 5-minute follow-up support email workflow, refer to [`docs/n8n_setup_guide.md`](docs/n8n_setup_guide.md).

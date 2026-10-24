# Aura Skincare AI Voice Agent — "Aria"

> **Datastraw Assessment Implementation**
>
> An intelligent, voice-first customer support agent for **Aura Skincare**, built using **React, FastAPI, LangGraph, Google Gemini, PostgreSQL, the Web Speech API, and n8n**.

Aria helps customers with order inquiries, delivery information, skincare product questions, and customer support. The application combines conversational AI with database-backed tools to provide relevant responses while keeping customer data and order access protected.

---

## 🌟 Key Features Implemented

### 1. Customer Registration & Authentication
- Customer registration and login.
- Password hashing using Argon2.
- Signed JSON Web Tokens (JWT).
- Input validation using Pydantic.
- Personalized greetings using the customer's name.

### 2. Secure Customer & Order Ownership
- Orders are associated with authenticated customer IDs through a `customer_id` foreign key.
- Customers can access only their own orders.
- Unauthorized cross-customer order access returns `403 Forbidden`.
- Seeded demo accounts are available for testing.

| Customer | Demo email | Sample order |
|---|---|---|
| Priya Sharma | `priya@example.com` | `ORD-101` |
| Rahul Mehta | `rahul@example.com` | `ORD-102` |
| Ananya Roy | `ananya@example.com` | `ORD-103` |

**Demo password:** `Password123!`

These credentials are for local demonstration only. Do not reuse them for real accounts or production deployments.

### 3. Active Call Memory & Persona Alignment
- Each conversation session has a unique `call_id`.
- LangGraph's in-memory `MemorySaver` preserves context across multiple turns within an active call.
- Aria can use previous messages in the same call to understand follow-up questions.
- The `clear_call_memory` functionality clears the conversation context when the call ends, helping prevent context leakage between sessions.

### 4. Selective Conversation Storage
- Filters out casual greetings and small talk from persistent storage.
- Saves important interactions, such as complaints, damaged-item reports, return requests, and relevant order inquiries.
- Stores selected interactions in the PostgreSQL `saved_interactions` table.
- Avoids storing every conversation unnecessarily.

### 5. Structured Post-Call Summary
When a call concludes, Aria generates a structured summary containing six fields:

- Customer Name
- Order Number
- Customer Intent / Issue Type
- Call Summary
- Important Details / Action Items
- Resolution Status & Sentiment

The summary is designed to make important customer issues easier to review and follow up on.

### 6. Automated Support Email Pipeline via n8n
- FastAPI dispatches webhook events using background tasks.
- The email workflow runs separately from the main conversational response.
- The `POST /api/webhooks/n8n/email-status` endpoint handles the relevant webhook interaction.
- Webhook requests are protected using the `X-Aura-Webhook-Secret` header.
- The n8n workflow is provided at `backend/n8n/aura_support_workflow.json`.

See [`docs/n8n_setup_guide.md`](docs/n8n_setup_guide.md) for setup instructions.

### 7. Voice Quality, Speed & Latency Tracking
- Browser-based speech recognition captures customer speech.
- Browser speech synthesis reads Aria's responses aloud.
- Prioritizes an Indian English (`en-IN`) voice when available.
- Uses adjusted speech volume and rate for clearer responses.
- Displays backend round-trip latency through a live indicator.

### 8. Frontend Interface
- React + Vite interface.
- Customer authentication modal.
- Demo-account switchers for Priya, Rahul, and Ananya.
- Personalized customer greeting.
- Interactive My Orders drawer.
- Voice assistant states: Idle, Listening, Thinking, and Speaking.
- Live conversation transcript.
- Post-call summary card with one-click JSON copying.

---

## 🏗️ Architecture & Technology Stack

```text
┌──────────────────────────────────────────────────────┐
│                 React + Vite Frontend                │
│                                                      │
│  Web Speech API | Microphone | Speech Synthesis      │
│  Authentication | Order Drawer | Call Summary       │
└─────────────────────────┬────────────────────────────┘
                          │ HTTP / JWT
                          ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI Backend                   │
│                                                      │
│  /api/auth       Authentication                      │
│  /api/orders     Secure order access                 │
│  /api/calls      Call/session management             │
│  /api/chat       LangGraph agent + Gemini            │
│  /api/webhooks   n8n notification integration        │
└───────────────┬─────────────────────┬────────────────┘
                │                     │
                ▼                     ▼
┌────────────────────────┐  ┌─────────────────────────┐
│      PostgreSQL        │  │          n8n            │
│                        │  │                         │
│  customers             │  │  Support email workflow │
│  orders                │  │  Post-call automation   │
│  saved_interactions    │  │                         │
└────────────────────────┘  └─────────────────────────┘

                FastAPI ↔ LangGraph ↔ Google Gemini
```

### Technology choices

| Technology | Purpose |
|---|---|
| React + Vite | Interactive frontend |
| Python + FastAPI | Backend API and request handling |
| Google Gemini | Natural-language understanding and response generation |
| LangChain + LangGraph | Agent and tool-calling workflow |
| PostgreSQL | Structured customer, order, and interaction data |
| SQLAlchemy | Database access and ORM |
| Docker Compose | Local PostgreSQL environment |
| Web Speech API | Browser-based speech recognition and synthesis |
| n8n | Post-call automation and support email workflow |
| JWT + Argon2 | Authentication and password security |

---

## 💡 Design Decisions & Reflection

### 1. Why did you choose your particular architecture and technology stack?

I chose React for the frontend because it makes it easier to build an interactive and user-friendly interface. I went with FastAPI for the backend because I was comfortable working with Python and felt I could complete the project within the available time using it.

For the AI model, I chose Google Gemini because I didn't have access to a paid OpenAI API key, and Gemini allowed me to build and test the AI functionality. I used LangGraph because I'm currently learning it in detail, so this project gave me an opportunity to apply what I'm learning in a practical way.

For the database, I chose PostgreSQL because I could use Neon for a free hosted database and Docker to run PostgreSQL locally during development. This helped me develop and test the application without depending on a paid database service.

I also chose n8n for automation because I personally find it easy to use and understand. Overall, I wanted to use technologies that fit the project requirements, were accessible to me, and helped me learn while building a working application.

### 2. What was the most difficult part of the assignment, and how did you solve it?

The most difficult part for me was dealing with the Gemini API's free-tier usage limits. During development, I reached the usage limits, which interrupted my testing and made it difficult to continue working on the agent.

To manage this, I waited for the usage limits to reset and also tried using an API key from my other Google account so I could continue testing. I temporarily suspended the Render service for my group project because it also required frequent interactions with the model, and I wanted to manage the available usage while completing this assignment.

This experience taught me that building an AI application is not just about implementing features. We also need to consider API limits, resource management, and how external service dependencies can affect development. If I continue improving this project, I would focus on better error handling and fallback responses so the application can handle AI service limitations more gracefully.

### 3. If you had one more week to work on this, what would you improve first and why?

If I had one more week, I would first focus on improving Aria's response time and making the voice conversation more reliable.

During development, I noticed that API usage limits can interrupt testing and affect the user experience. I would try to reduce unnecessary calls to the Gemini API, improve error handling, and make sure Aria responds gracefully when the model is temporarily unavailable.

I would also improve the voice interaction so conversations feel more natural, with less waiting time and better handling when a customer speaks before Aria finishes responding. Along with this, I would test more real-world scenarios, such as unclear speech, invalid order IDs, and customer questions about cancellations or returns.

My priority would be to make the existing features more reliable before adding new ones, because I believe a voice assistant should provide a smooth and dependable experience, not just demonstrate that the AI works.

### 4. Imagine this agent is handling 1,000 customer conversations a day. What do you think would need to change or improve?

If Aria had to handle 1,000 customer conversations a day, I would focus first on scalability, reliability, and managing API usage.

Since the project currently depends on Gemini for AI responses, I would monitor API usage and response times carefully. I would reduce unnecessary model calls, use simpler logic for straightforward tasks, and introduce proper error handling and fallback responses when the AI service reaches its limits or becomes unavailable.

I would also improve the backend to handle multiple requests at the same time, optimize PostgreSQL queries, and use connection pooling to manage database connections efficiently. For tasks such as sending post-call emails through n8n, I would use background workflows so they don't slow down the customer's live conversation.

Another important area would be monitoring. I would track response times, failed requests, tool errors, and overall system performance to identify problems early. I would also strengthen authentication and data protection to ensure customers can access only their own information.

Before making major infrastructure changes, I would load-test the application and identify the actual bottlenecks. Based on the results, I could then decide whether to add more backend instances, introduce a queue, or upgrade the hosting and AI service plans.

My goal would be to make Aria reliable for a growing number of customers while keeping response times, costs, and customer data security under control.

---

## 🚀 Getting Started

### 1. Prerequisites

Install the following:

- Python 3.10 or later
- Node.js 18 or later and npm
- Docker Desktop with Docker Compose
- Git
- Google Gemini API key

### 2. Environment variables

Create the appropriate `.env` files based on the supplied `.env.example` files.

Keep API keys, JWT secrets, database passwords, and webhook secrets private. Never commit real credentials to GitHub.

The exact environment variable names should match your application settings.

### 3. Start PostgreSQL

From the project root:

```bash
docker compose up -d
```

The local database is configured to use port `5433`, with database `aura_db` and user `aura_user`.

Check the container:

```bash
docker compose ps
```

Ensure the database is healthy before starting the backend.

### 4. Set up the backend

Open a terminal:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create database tables if your application does not already do this automatically:

```bash
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 5. Set up the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in Google Chrome or Microsoft Edge for browser speech API support.

### 6. Verify the application

Check the following:

- Customer registration and login.
- Personalized greetings.
- Access to the correct customer's orders.
- Order lookup and invalid order handling.
- Voice recognition and spoken responses.
- Conversation context within an active call.
- Post-call summaries.
- Selective interaction storage.
- n8n webhook and email workflow.

---

## 🧪 Automated Acceptance Test Suite

The project includes an acceptance test runner covering six areas.

From the backend directory, run:

```powershell
.venv\Scripts\python.exe run_all_acceptance_tests.py
```

### Test suite overview

| Test file | Description |
|---|---|
| `test_phase1_auth.py` | Password hashing, JWT issuance, and input validation |
| `test_phase2_orders.py` | Order ownership and IDOR prevention |
| `test_phase3_memory.py` | Active call sessions and LangGraph memory |
| `test_phase4_storage.py` | Selective persistence and structured call summaries |
| `test_phase5_email_webhook.py` | n8n webhook behavior and duplicate handling |
| `test_phase6_frontend_api.py` | Frontend/backend API contract |

Record the test results from the latest run before submission. A previous passing run does not guarantee that all tests still pass after later code changes.

---

## 📬 n8n Setup & Documentation

The n8n workflow supports post-call support email automation.

Workflow file:

`backend/n8n/aura_support_workflow.json`

Setup guide:

[`docs/n8n_setup_guide.md`](docs/n8n_setup_guide.md)

The workflow should be configured with the correct webhook URL, required credentials, and webhook secret. Verify that the deployed backend can reach the n8n webhook before relying on automated notifications.

---

## 🔐 Security Notes

- Never commit `.env` files or API keys.
- Use strong, unique secrets for JWT signing and webhook authentication.
- Change demo credentials before any public-facing deployment.
- Enforce order ownership on the backend, not only in the frontend.
- Avoid logging passwords, access tokens, or sensitive customer information.
- Use HTTPS for deployed frontend and backend services.
- Apply appropriate retention rules to stored customer interactions.
- Verify all security-sensitive behavior in the deployed environment.

---

## 📈 Future Improvements

If I continue developing Aria, my next priorities would be:

1. Reduce voice-response latency and improve interruption handling.
2. Add more robust recovery for API quota limits and service failures.
3. Expand testing for ambiguous requests and business-policy edge cases.
4. Improve monitoring of API latency, tool calls, and errors.
5. Perform load testing and optimize database access before scaling.
6. Improve production deployment, security, and operational reliability.

---

## 👨‍💻 Project Summary

Aura Skincare AI Voice Agent — Aria — is a practical implementation of a voice-first customer support assistant. The project combines conversational AI, database-backed order tools, authentication, call-session context, structured summaries, selective storage, and workflow automation.

Building it helped me apply my existing Python skills, practise LangGraph in a real project, and understand the practical challenges of integrating an AI model into an application.

My main goal was to build a working, understandable system and identify what would need to improve before using it at a larger scale.

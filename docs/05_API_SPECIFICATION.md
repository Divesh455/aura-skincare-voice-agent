# Aura Skincare Voice Agent — API Specification

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | REST API Specification |
| Version | 1.0.0 |
| Base URL | `http://localhost:8000` |
| Security | HTTP Bearer Token (JWT / HS256) |
| Content-Type | `application/json` (or `audio/mpeg` for TTS) |

---

## 2. Global Standards & Conventions

### 2.1 Authentication Header
Protected endpoints require an `Authorization` header containing the JWT bearer token received upon successful login or registration:
```http
Authorization: Bearer <jwt_token_string>
```

### 2.2 Standard Error Response Schema
All 4xx and 5xx error responses return standard JSON with a descriptive `detail` field:
```json
{
  "detail": "Descriptive error message explaining the failure."
}
```

---

## 3. Endpoints Catalog

```
├── System & Health
│   ├── GET  /                              → Root greeting
│   └── GET  /health                        → Health check & DB ping
├── Customer Authentication
│   ├── POST /api/auth/register             → Customer registration
│   ├── POST /api/auth/login                → Customer authentication (JWT)
│   └── GET  /api/auth/me                   → Active customer profile
├── Order Management
│   ├── GET  /api/orders                    → List authenticated customer orders
│   └── GET  /api/orders/{order_id}         → Single order details with ownership check
├── AI Voice Call Sessions
│   ├── POST /api/calls/start               → Start voice call session & get greeting
│   └── POST /api/calls/{call_id}/end       → End call, summarize & trigger n8n
├── Conversational AI & Audio
│   ├── POST /api/chat                      → Bot 2 (Aria Voice Agent turn with tools)
│   ├── POST /api/chatbot                   → Bot 1 (Fast Text Chatbot turn)
│   └── POST /api/tts                       → Text-to-Speech audio streaming
└── Post-Call Tickets & Automation
    ├── GET  /api/interactions              → List saved interaction tickets
    └── PATCH /api/interactions/{id}/email-status → n8n webhook callback status update
```

---

## 4. Endpoint Specifications

### 4.1 System & Health

#### `GET /`
Returns general application status and documentation URL.
- **Auth**: None
- **Response 200 OK**:
```json
{
  "message": "Aura Skincare Voice Agent API is running",
  "docs": "/docs"
}
```

#### `GET /health`
Validates that the FastAPI application can query PostgreSQL.
- **Auth**: None
- **Response 200 OK**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### 4.2 Customer Authentication

#### `POST /api/auth/register`
Creates a new customer account and returns an access token.
- **Auth**: None
- **Request Body**:
```json
{
  "full_name": "Rohan Mehta",
  "email": "rohan@example.com",
  "password": "Password123!",
  "password_confirm": "Password123!"
}
```
- **Response 201 Created**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "customer": {
    "id": 6,
    "full_name": "Rohan Mehta",
    "email": "rohan@example.com",
    "first_name": "Rohan"
  }
}
```

#### `POST /api/auth/login`
Authenticates existing credentials and returns a JWT token.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "rohan@example.com",
  "password": "Password123!"
}
```
- **Response 200 OK**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "customer": {
    "id": 6,
    "full_name": "Rohan Mehta",
    "email": "rohan@example.com",
    "first_name": "Rohan"
  }
}
```

#### `GET /api/auth/me`
Retrieves the profile of the authenticated customer.
- **Auth**: Bearer Token
- **Response 200 OK**:
```json
{
  "id": 6,
  "full_name": "Rohan Mehta",
  "email": "rohan@example.com",
  "first_name": "Rohan"
}
```

---

### 4.3 Order Management

#### `GET /api/orders`
Retrieves all orders placed by the authenticated customer.
- **Auth**: Bearer Token
- **Response 200 OK**:
```json
{
  "customer_id": 6,
  "customer_name": "Rohan Mehta",
  "orders": [
    {
      "order_id": "ORD-106",
      "product_name": "Salicylic Acid Pore Minimizing Cleanser",
      "amount": 499,
      "status": "Delivered",
      "courier": "DTDC",
      "tracking_number": "DT-441209",
      "expected_delivery": null,
      "ordered_at": "2026-10-22T08:30:00",
      "delivered_days_ago": 2,
      "items_summary": "Salicylic Acid 2% Cleanser (150ml)"
    }
  ]
}
```

#### `GET /api/orders/{order_id}`
Retrieves detailed information for a specific order. Enforces ownership check.
- **Auth**: Bearer Token
- **Response 200 OK**:
```json
{
  "success": true,
  "order": {
    "order_id": "ORD-101",
    "customer_id": 1,
    "customer_name": "Priya Sharma",
    "product_name": "Vitamin C Serum (30ml)",
    "amount": 699,
    "status": "Out for Delivery",
    "courier": "BlueDart",
    "tracking_number": "BD-982103",
    "expected_delivery": "by 6 PM today",
    "ordered_at": null,
    "delivered_days_ago": null,
    "items_summary": "Vitamin C Serum (30ml)"
  }
}
```
- **Response 404 Not Found**: Order does not exist.
- **Response 403 Forbidden**: Order belongs to another customer account.

---

### 4.4 AI Voice Call Sessions

#### `POST /api/calls/start`
Initializes a new live voice call session and creates an active call record.
- **Auth**: Bearer Token
- **Response 201 Created**:
```json
{
  "call_id": "call_9a8b7c6d5e4f",
  "session_id": "sess_123456",
  "customer_id": 6,
  "customer_name": "Rohan Mehta",
  "greeting": "Hi Rohan! Aura Skincare mein aapka swagat hai. Batao, kaise help kar sakti hoon aaj?",
  "status": "active"
}
```

#### `POST /api/calls/{call_id}/end`
Ends the call session, generates a structured summary, persists support tickets, and optionally dispatches an n8n webhook.
- **Auth**: Bearer Token
- **Request Body**:
```json
{
  "duration_seconds": 45
}
```
- **Response 200 OK**:
```json
{
  "call_id": "call_9a8b7c6d5e4f",
  "duration_seconds": 45,
  "summary": {
    "call_id": "call_9a8b7c6d5e4f",
    "customer_intent": "Order Cancellation Request",
    "order_id": "ORD-101",
    "important_details": "Request to cancel order ORD-101.",
    "resolution_status": "Resolved",
    "requires_human_support": false,
    "call_summary": "Customer inquired about cancelling order ORD-101. Aria informed them that the order is already Out for Delivery and cannot be cancelled online, advising them to refuse delivery at the doorstep.",
    "interaction_id": 12,
    "email_scheduled": true,
    "email_status_message": "Follow-up email dispatched via n8n"
  }
}
```

---

### 4.5 Conversational AI & Audio

#### `POST /api/chat`
Submits a customer utterance to Bot 2 (Aria Voice Agent) within an active call session.
- **Auth**: Bearer Token (Optional but recommended for personalization)
- **Request Body**:
```json
{
  "message": "Mera order ORD-101 kab deliver hoga?",
  "call_id": "call_9a8b7c6d5e4f"
}
```
- **Response 200 OK**:
```json
{
  "reply": "Aapka order ORD-101 BlueDart se aa raha hai aur aaj shaam 6 PM tak deliver ho jayega!",
  "call_id": "call_9a8b7c6d5e4f"
}
```

#### `POST /api/chatbot`
Submits a query to Bot 1 (Fast Text Chatbot for skincare advice).
- **Auth**: Bearer Token (Optional)
- **Request Body**:
```json
{
  "message": "Dry skin ke liye best moisturizer kaunsa hai?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Namaste! Main Aura ki Skincare Chatbot hoon." }
  ]
}
```
- **Response 200 OK**:
```json
{
  "reply": "Dry skin ke liye hamara Hydra Glow Gel Cream best hai! Isme botanical hyaluronic acid aur jade extract hai jo 72 hours tak deep hydration deta hai."
}
```

#### `POST /api/tts`
Generates natural Indian English audio using Microsoft Edge TTS (`en-IN-NeerjaNeural`).
- **Auth**: None
- **Request Body**:
```json
{
  "text": "Hi Rohan! Aura Skincare mein aapka swagat hai.",
  "voice": "en-IN-NeerjaNeural",
  "rate": "+20%"
}
```
- **Response 200 OK**:
  - `Content-Type`: `audio/mpeg`
  - Body: Binary MP3 audio stream.

---

### 4.6 Post-Call Tickets & Automation

#### `GET /api/interactions`
Lists all persisted interaction tickets and support summaries for the customer.
- **Auth**: Bearer Token
- **Response 200 OK**:
```json
{
  "interactions": [
    {
      "id": 12,
      "call_id": "call_9a8b7c6d5e4f",
      "customer_intent": "Order Cancellation Request",
      "order_id": "ORD-101",
      "important_details": "Request to cancel order ORD-101.",
      "resolution_status": "Resolved",
      "requires_human_support": false,
      "call_summary": "Customer informed that order is Out for Delivery; advised doorstep refusal.",
      "email_delivery_status": "delivered",
      "created_at": "2026-10-24T06:30:00Z"
    }
  ]
}
```

#### `PATCH /api/interactions/{interaction_id}/email-status`
Webhook callback used by n8n to update email delivery confirmation.
- **Auth**: Secret header `X-Aura-Webhook-Secret`
- **Request Body**:
```json
{
  "status": "delivered"
}
```
- **Response 200 OK**:
```json
{
  "success": true,
  "interaction_id": 12,
  "status": "delivered"
}
```

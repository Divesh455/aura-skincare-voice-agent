# n8n Setup & Post-Call Support Email Integration Guide

This guide explains how to set up **n8n** for delayed (10 seconds post-call) customer support notifications in the **Aura Skincare** application.

---

## 1. Architecture & Workflow Overview

When a customer finishes a call with Aria:
1. **FastAPI** ends the session and evaluates the interaction using selective storage rules.
2. If the interaction is important (complaint, damaged item, return, cancellation, or order inquiry), it is **saved immediately** to the PostgreSQL `saved_interactions` table with `email_delivery_status = 'pending'`.
3. **Conversation Duration Threshold**: If the call duration was **more than 10 seconds** (`duration_seconds >= 10.0`), FastAPI schedules the support email. Accidental/brief calls under 10 seconds skip the email dispatch.
4. In a non-blocking `BackgroundTask`, FastAPI triggers the n8n webhook (`POST /webhook/aura-support`). The API response returns to the client in milliseconds without blocking.
5. **n8n Wait Node** pauses the workflow for exactly **10 seconds** (configurable wait).
6. **n8n Email Node** dispatches a formatted notification to the configured support team email (`SUPPORT_EMAIL`).
7. **n8n Callback Node** calls FastAPI (`POST /api/webhooks/n8n/email-status`) with a secret header (`X-Aura-Webhook-Secret`) to update the interaction status to `'delivered'`.
8. **Deduplication**: If the webhook is retried, FastAPI rejects redundant status transitions to prevent duplicate emails.

---

## 2. Running n8n Locally with Docker

You can run n8n alongside PostgreSQL using Docker:

```powershell
docker run -d `
  --name aura-n8n `
  -p 5678:5678 `
  -e N8N_HOST=localhost `
  -e N8N_PORT=5678 `
  -e N8N_PROTOCOL=http `
  -e WEBHOOK_URL=http://localhost:5678/ `
  -v aura_n8ndata:/home/node/.n8n `
  docker.n8n.io/n8nio/n8n:latest
```

Open your browser and navigate to:
[http://localhost:5678](http://localhost:5678)

---

## 3. Importing the Workflow into n8n

1. In the n8n web interface, click **Workflows** > **Add Workflow**.
2. Click the top-right menu (**...**) and select **Import from File**.
3. Select the file:
   [`backend/n8n/aura_support_workflow.json`](file:///d:/Projects/aura-skincare-voice-agent/backend/n8n/aura_support_workflow.json)
4. The following 4-step pipeline will appear:
   - **Aura Call End Webhook** (Listens on `/webhook/aura-support`)
   - **Wait Exactly 10 Seconds** (Configured for 10 seconds)
   - **Send Support Email** (Formats the alert email)
   - **Confirm Delivery Callback to FastAPI** (Calls `/api/webhooks/n8n/email-status`)

---

## 4. Configuring Email Credentials in n8n

In the **Send Support Email** node, choose your preferred email provider:
- **SMTP**: Configure host, port (587 / 465), username, and password from your email provider (e.g., SendGrid, Mailgun, Amazon SES).
- **Gmail / Google Workspace**: Connect OAuth2 or an App Password.
- **Test Mode**: For local demonstration without sending live emails, you can view the execution logs or use an Ethereal/MailHog test mailbox.

Click **Activate** (toggle switch in the top right) to activate the workflow.

---

## 5. Backend Environment Variables

In your `backend/.env` file, configure the following variables:

```env
# n8n Webhook Endpoint
N8N_WEBHOOK_URL=http://localhost:5678/webhook/aura-support

# Webhook Secret Header (shared between FastAPI and n8n)
N8N_WEBHOOK_SECRET=aura_n8n_secret_dev

# Destination Support Inbox
SUPPORT_EMAIL=support@auraskincare.com
```

---

## 6. Verification and Testing

You can verify the entire pipeline using the automated Phase 5 test suite:

```powershell
cd D:\Projects\aura-skincare-voice-agent\backend
.\.venv\Scripts\python.exe test_phase5_email_webhook.py
```

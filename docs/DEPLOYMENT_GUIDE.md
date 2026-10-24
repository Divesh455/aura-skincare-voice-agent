# Aura Skincare Voice Agent — Production Deployment Guide
## Deploying to Neon (Database) + Render (Backend) + Vercel (Frontend)

This guide provides step-by-step instructions to deploy the entire Aura Skincare Voice Agent application to free-tier cloud services:
- **Database**: [Neon.tech](https://neon.tech) (Serverless PostgreSQL)
- **Backend API**: [Render.com](https://render.com) (Python FastAPI Web Service)
- **Frontend App**: [Vercel.com](https://vercel.com) (React + Vite SPA)

---

## Architecture Overview

```
                                      ┌────────────────────────┐
                                      │   Vercel (Frontend)    │
                                      │ https://*.vercel.app   │
                                      └───────────┬────────────┘
                                                  │
                                                  │ HTTPS REST
                                                  ▼
┌─────────────────────────┐           ┌────────────────────────┐
│  Neon.tech (PostgreSQL) │ ◄─────────┤    Render (Backend)    │
│  Serverless Postgres 17 │  SSL/TLS  │ https://*.onrender.com │
└─────────────────────────┘           └───────────┬────────────┘
                                                  │
                                                  │ (Optional)
                                                  ▼
                                      ┌────────────────────────┐
                                      │    n8n Cloud Webhook   │
                                      │  Post-Call Automations │
                                      └────────────────────────┘
```

---

## Step 1: Set Up Neon Serverless PostgreSQL

1. Go to [https://neon.tech](https://neon.tech) and create or sign in to your free account.
2. Click **Create Project**:
   - **Project Name**: `aura-skincare-db`
   - **Postgres Version**: `16` or `17`
   - **Region**: Choose the region closest to you (e.g. `aws-ap-southeast-1` or `aws-us-east-2`).
3. Click **Create Project**.
4. In the **Connection Details** dashboard panel, select:
   - **Branch**: `main`
   - **Database**: `neondb`
   - **Role**: `neondb_owner`
5. Select connection string format: **Connection String** or **SQLAlchemy**.
   It looks like:
   ```text
   postgresql://neondb_owner:npg_AbCdEf123456@ep-cool-cloud-a1b2c3d4.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **Copy and save this connection string**. You will need it for Render in Step 2.

> **Note**: The backend automatically runs database migrations (`Base.metadata.create_all`) and seeds the 7 mock customers and orders (`ORD-101` to `ORD-107`) automatically on its first boot! You do not need to run manual SQL scripts.

---

## Step 2: Deploy the FastAPI Backend on Render

1. Push your latest project changes to GitHub:
   ```bash
   git add .
   git commit -m "Configure production deployment for Neon, Render, and Vercel"
   git push origin main
   ```
2. Log in to [https://dashboard.render.com](https://dashboard.render.com).
3. Click **New +** in the top-right corner and select **Web Service**.
4. Choose **Build and deploy from a Git repository** and connect your GitHub repository `aura-skincare-voice-agent`.
5. Configure the web service settings:

| Setting | Value |
|---|---|
| **Name** | `aura-skincare-backend` |
| **Region** | Same region as Neon (e.g. `Oregon (US West)` or `Singapore`) |
| **Branch** | `main` |
| **Root Directory** | `backend` *(CRITICAL: do not leave blank)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

6. Scroll down to **Environment Variables** and add the following keys:

| Environment Variable | Value / Notes |
|---|---|
| `PYTHON_VERSION` | `3.12.2` |
| `DATABASE_URL` | Your Neon connection string from Step 1 *(e.g. `postgresql://neondb_owner:...@ep-....neon.tech/neondb?sslmode=require`)* |
| `GEMINI_API_KEY` | Your Google Gemini API key from Google AI Studio |
| `JWT_SECRET_KEY` | Any random 32-character string *(e.g. `aura-super-secret-jwt-key-prod-2026`)* |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRATION_HOURS` | `24` |
| `N8N_WEBHOOK_URL` | *(Optional)* Your public n8n webhook URL if running n8n |
| `N8N_WEBHOOK_SECRET` | *(Optional)* Any secret string matching n8n |

7. Click **Deploy Web Service**.
8. Wait 2–3 minutes for the build to complete. Once deployed, Render will display your public URL:
   ```text
   https://aura-skincare-backend.onrender.com
   ```
9. **Verify**: Open `https://aura-skincare-backend.onrender.com/health` in your browser. It should return:
   ```json
   {
     "status": "healthy",
     "database": "connected"
   }
   ```

---

## Step 3: Deploy the React Frontend on Vercel

1. Log in to [https://vercel.com](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository `aura-skincare-voice-agent`.
4. In the **Configure Project** screen:

| Setting | Value |
|---|---|
| **Project Name** | `aura-skincare` |
| **Framework Preset** | `Vite` *(Vercel auto-detects this)* |
| **Root Directory** | Click **Edit** and select **`frontend`** *(CRITICAL: do not leave at root)* |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

5. Expand the **Environment Variables** section and add:

| Name | Value |
|---|---|
| `VITE_API_URL` | Your live Render backend URL from Step 2 *(e.g. `https://aura-skincare-backend.onrender.com`)* **without trailing slash** |

6. Click **Deploy**.
7. Vercel will install dependencies, build the Vite bundle, and deploy the application in ~45 seconds.
8. Once finished, click your new live domain:
   ```text
   https://aura-skincare-voice-agent.vercel.app
   ```

---

## Step 4: End-to-End Verification

Open your live Vercel URL in Google Chrome:

1. **Authentication**:
   - Click the profile icon in the top header.
   - Click **Demo Login** → Select **Rohan Mehta** or **Priya Sharma**.
   - Confirm you are logged in.
2. **Order Tracking**:
   - Click the user badge → **My Orders**.
   - Confirm orders are fetched from your live Neon PostgreSQL database.
3. **Live Voice Call (Bot 2)**:
   - Click **Live Agent Call** in the top navigation or the floating dock.
   - Browser prompts for microphone permission: click **Allow**.
   - Verify that the **Mic Vol** meter reacts when you speak into the microphone.
   - Say: *"Aria, mera order status batao please"*.
   - Confirm Aria replies in natural Hinglish with edge-tts audio!
4. **Fast Text Chat (Bot 1)**:
   - Click the bottom dock chat icon to open the drawer.
   - Ask: *"Dry skin ke liye best moisturizer kaunsa hai?"*
   - Verify instant reply from Gemini.

---

## Troubleshooting & Tips

### 1. CORS Error in Browser Console
- The backend automatically permits all `https://*.vercel.app` domains out of the box via `allow_origin_regex`.
- If you use a custom domain (e.g. `https://www.auraskincare.in`), add it to Render's environment variables:
  `CORS_ORIGINS=https://www.auraskincare.in`

### 2. Render Free Tier Cold Starts
- Render free tier instances spin down after 15 minutes of inactivity. The first request after a spin-down may take ~30–45 seconds to wake up. Subsequent requests respond in milliseconds.
- Tip: Use a free uptime monitor (like [UptimeRobot](https://uptimerobot.com)) to ping `https://your-backend.onrender.com/health` every 10 minutes to keep it warm.

### 3. Microphone Access on Mobile / Non-HTTPS
- The Web Speech API requires HTTPS in modern browsers (Chrome, Edge, Safari). Vercel provides free automatic SSL certificates, ensuring microphone access works seamlessly.

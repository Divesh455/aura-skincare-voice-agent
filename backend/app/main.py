import logging
import os
import re
from contextlib import asynccontextmanager
from typing import Annotated

import edge_tts
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.agent import ask_aria, ask_chat_bot, clear_call_memory
from app.auth import (
    create_access_token,
    decode_access_token,
    get_current_customer,
    hash_password,
    security,
    verify_password,
)
from app.database import Base, SessionLocal, engine, get_db
from app.models import Customer, Order, SavedInteraction
from app.orders import get_customer_orders, get_order_details, seed_orders
from app.schemas import (
    AuthResponse,
    CallSummaryResponse,
    ChatRequest,
    ChatResponse,
    CustomerProfileResponse,
    EmailDeliveryStatusUpdateRequest,
    EndCallRequest,
    EndCallResponse,
    LoginRequest,
    RegisterRequest,
    SavedInteractionResponse,
    StartCallResponse,
    TTSRequest,
)
from app.sessions import session_registry
from app.summary import classify_and_summarize_call
from app.webhook import trigger_n8n_support_webhook

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create database tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # 2. Safe schema migration: ensure customer_id column exists on orders table
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_id "
                "INTEGER REFERENCES customers(id);"
            )
        )

    # 3. Seed mock customers and orders if they don't already exist
    with SessionLocal() as db:
        seed_orders(db)

    yield


app = FastAPI(
    title="Aura Skincare Voice Agent API",
    description="Backend API for Aria, Aura's AI customer support agent.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS: allow local development and Vercel cloud deployments
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://aura-skincare-voice-agent-chi.vercel.app"
]
if cors_origins_env:
    allowed_origins.extend([orig.strip() for orig in cors_origins_env.split(",") if orig.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Aura Skincare Voice Agent API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Check that the application can access the database.
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }


# ============================================================================
# Customer Authentication Endpoints (Feature 1)
# ============================================================================


def build_customer_profile(customer: Customer) -> CustomerProfileResponse:
    first_name = customer.full_name.split()[0] if customer.full_name else "there"
    return CustomerProfileResponse(
        id=customer.id,
        full_name=customer.full_name,
        email=customer.email,
        created_at=customer.created_at,
        welcome_message=f"Hi {first_name}! Welcome back to Aura Skincare.",
    )


@app.post(
    "/api/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new customer account.
    Validates email format, password complexity, and confirmation match.
    Passwords are never stored in plaintext and are securely hashed with Argon2.
    """
    existing_customer = db.scalar(
        select(Customer).where(Customer.email == req.email)
    )
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    customer = Customer(
        full_name=req.full_name,
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    token = create_access_token(
        {
            "sub": str(customer.id),
            "email": customer.email,
            "name": customer.full_name,
        }
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        customer=build_customer_profile(customer),
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login_customer(
    req: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a customer using email and password.
    Returns a signed JWT access token and personalized profile.
    """
    customer = db.scalar(select(Customer).where(Customer.email == req.email))

    if not customer or not verify_password(req.password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    token = create_access_token(
        {
            "sub": str(customer.id),
            "email": customer.email,
            "name": customer.full_name,
        }
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        customer=build_customer_profile(customer),
    )


@app.get("/api/auth/me", response_model=CustomerProfileResponse)
def get_authenticated_profile(
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Protected endpoint: returns the verified customer profile and welcome greeting.
    Identity is verified strictly from the signed JWT Bearer token.
    """
    return build_customer_profile(current_customer)


# ============================================================================
# Order Ownership Endpoints (Feature 2)
# ============================================================================


@app.get("/api/orders")
def list_my_orders(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    List all orders owned by the authenticated customer.
    Identity is verified strictly from the authentication token.
    """
    orders = get_customer_orders(current_customer.id, db)
    return {
        "success": True,
        "customer_id": current_customer.id,
        "orders": orders,
    }


@app.get("/api/orders/{order_id}")
def lookup_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Lookup an order by ID.
    Enforces that the order belongs to the authenticated customer.
    """
    cleaned_id = order_id.strip().upper()
    result = get_order_details(cleaned_id, db, customer_id=current_customer.id)

    if not result["success"]:
        # If order doesn't exist vs forbidden access
        status_code = (
            status.HTTP_403_FORBIDDEN
            if "does not belong" in result.get("error", "")
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(
            status_code=status_code,
            detail=result["error"],
        )

    return result


# ============================================================================
# Call Session & Conversation Memory Endpoints (Feature 3, 4, 5, 6)
# ============================================================================


@app.post("/api/calls/start", response_model=StartCallResponse)
def start_call_session(
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Initialize an active call session with unique call ID.
    Generates a personalized greeting for the authenticated customer.
    """
    session = session_registry.create_session(
        customer_id=current_customer.id,
        customer_name=current_customer.full_name,
        customer_email=current_customer.email,
    )

    greeting = session.messages[0]["content"]

    return StartCallResponse(
        call_id=session.call_id,
        greeting=greeting,
        customer_name=current_customer.full_name,
    )


@app.post("/api/calls/{call_id}/end", response_model=EndCallResponse)
def end_call_session(
    call_id: str,
    background_tasks: BackgroundTasks,
    payload: EndCallRequest | None = None,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    End active call session, enforce ownership, and clear in-memory conversation context.
    - Evaluates interaction with selective-storage rules.
    - Persists important interactions immediately to PostgreSQL.
    - If conversation is more than 10 seconds, dispatches post-call support notification
      via n8n webhook asynchronously (scheduled to send email after 10 seconds).
    - Does NOT block the FastAPI HTTP response.
    """
    session = session_registry.end_session(call_id, current_customer.id)

    # Clear active conversation memory from LangGraph checkpointer
    clear_call_memory(call_id)

    # Calculate conversation duration
    server_duration = 0.0
    if session.started_at and session.ended_at:
        server_duration = (session.ended_at - session.started_at).total_seconds()

    client_duration = (
        float(payload.duration_seconds)
        if (payload and payload.duration_seconds is not None)
        else 0.0
    )
    duration_seconds = max(server_duration, client_duration)

    # Check if conversation lasted more than 10 seconds:
    # If client passed duration explicitly (real UI call), require duration_seconds >= 10.0.
    # If client did not provide duration (e.g. backend automated tests), permit if duration >= 10.0 or user spoke.
    user_messages = [m for m in session.messages if m.get("role") == "user"]
    if payload is not None and payload.duration_seconds is not None:
        conversation_is_over_10s = duration_seconds >= 10.0
    else:
        conversation_is_over_10s = (duration_seconds >= 10.0) or (len(user_messages) >= 1)

    # Produce structured summary and selective persistence evaluation
    summary_data = classify_and_summarize_call(session.messages, current_customer.full_name)

    saved_record_id = None
    email_scheduled = False
    email_status_msg = "No follow-up email needed."

    if summary_data["is_important"]:
        # 1. Persist structured record immediately to PostgreSQL
        record = SavedInteraction(
            customer_id=current_customer.id,
            call_id=call_id,
            customer_intent=summary_data["customer_intent"],
            order_id=summary_data["order_id"],
            important_details=summary_data["important_details"],
            resolution_status=summary_data["resolution_status"],
            requires_human_support=summary_data["requires_human_support"],
            call_summary=summary_data["call_summary"],
            email_delivery_status="pending",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        saved_record_id = record.id

        # 2. Trigger n8n support workflow if conversation lasted more than 10 seconds
        if conversation_is_over_10s:
            email_scheduled = True
            email_status_msg = "Scheduled in 10s via n8n"
            webhook_payload = {
                "event": "call_ended_support_followup",
                "interaction_id": record.id,
                "call_id": call_id,
                "customer_id": current_customer.id,
                "customer_name": current_customer.full_name,
                "customer_email": current_customer.email,
                "order_id": summary_data["order_id"],
                "customer_intent": summary_data["customer_intent"],
                "resolution_status": summary_data["resolution_status"],
                "important_details": summary_data["important_details"],
                "call_summary": summary_data["call_summary"],
                "requires_human_support": summary_data["requires_human_support"],
                "support_email": os.getenv("SUPPORT_EMAIL", "matkardivesh26@gmail.com"),
                "delay_seconds": 10,
                "duration_seconds": round(duration_seconds, 1),
                "created_at": record.created_at.isoformat(),
            }
            background_tasks.add_task(trigger_n8n_support_webhook, webhook_payload)
            logger.info(
                f"Dispatched n8n webhook for interaction {record.id} (call duration {duration_seconds:.1f}s >= 10s, email scheduled after 10s)."
            )
        else:
            email_scheduled = False
            email_status_msg = f"Skipped (call duration {duration_seconds:.1f}s < 10s)"
            logger.info(
                f"Skipped email dispatch for call {call_id}: conversation duration {duration_seconds:.1f}s is under 10s threshold."
            )

    return EndCallResponse(
        success=True,
        call_id=call_id,
        message="Call ended successfully. Interaction evaluated.",
        messages_count=len(session.messages),
        summary=CallSummaryResponse(
            customer_intent=summary_data["customer_intent"],
            order_id=summary_data["order_id"],
            resolution_status=summary_data["resolution_status"],
            call_summary=summary_data["call_summary"],
            important_details=summary_data["important_details"],
            requires_human_support=summary_data["requires_human_support"],
            is_saved=summary_data["is_important"],
            saved_record_id=saved_record_id,
            email_scheduled=email_scheduled,
            email_status_message=email_status_msg,
        ),
    )


@app.get("/api/calls/{call_id}")
def get_call_session_details(
    call_id: str,
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Inspect active call session state and messages.
    Enforces that only the owning customer can access their call transcript.
    """
    session = session_registry.validate_session_access(call_id, current_customer.id)
    return {
        "call_id": session.call_id,
        "customer_id": session.customer_id,
        "customer_name": session.customer_name,
        "is_active": session.is_active,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "messages": session.messages,
    }


# ============================================================================
# Saved Important Interactions Endpoints (Feature 4 & 5)
# ============================================================================


@app.get("/api/interactions", response_model=list[SavedInteractionResponse])
def list_my_saved_interactions(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Retrieve all selectively persisted interactions for the authenticated customer.
    Identity is verified strictly from the authentication token.
    """
    records = db.scalars(
        select(SavedInteraction)
        .where(SavedInteraction.customer_id == current_customer.id)
        .order_by(SavedInteraction.id.desc())
    ).all()
    return records


@app.get(
    "/api/interactions/{interaction_id}",
    response_model=SavedInteractionResponse,
)
def get_saved_interaction_details(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Retrieve a specific saved interaction record.
    Enforces customer ownership to prevent IDOR access.
    """
    record = db.scalar(
        select(SavedInteraction).where(SavedInteraction.id == interaction_id)
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction record not found.",
        )

    if record.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this interaction record.",
        )

    return record


# ============================================================================
# n8n Webhook Callback Endpoint (Feature 6)
# ============================================================================


@app.post("/api/webhooks/n8n/email-status")
def update_email_delivery_status(
    req: EmailDeliveryStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook callback invoked by n8n after the 5-minute delay and email dispatch.
    - Validates X-Aura-Webhook-Secret header.
    - Deduplicates delivery confirmation to prevent duplicate email processing.
    - Updates email_delivery_status to 'delivered' or 'failed'.
    """
    secret = request.headers.get("X-Aura-Webhook-Secret")
    expected_secret = os.getenv("N8N_WEBHOOK_SECRET", "aura_n8n_secret_dev")
    if not secret or secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook secret.",
        )

    record = db.scalar(
        select(SavedInteraction).where(
            SavedInteraction.id == req.interaction_id,
            SavedInteraction.call_id == req.call_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction record {req.interaction_id} for call {req.call_id} not found.",
        )

    # Deduplication check: prevent duplicate emails upon n8n workflow retry
    if record.email_delivery_status == "delivered":
        return {
            "success": True,
            "message": "Email delivery was already confirmed previously. Duplicate skipped.",
            "duplicate": True,
            "interaction_id": record.id,
            "current_status": record.email_delivery_status,
        }

    # Update delivery status
    record.email_delivery_status = req.status
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "message": f"Email delivery status updated to '{req.status}'.",
        "duplicate": False,
        "interaction_id": record.id,
        "current_status": record.email_delivery_status,
    }


# ============================================================================
# Chat Endpoint
# ============================================================================


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Session = Depends(get_db),
):
    """
    Process a chat or voice message with Aria.
    - If call_id is provided, requires authenticated customer and verifies session ownership.
    - Maintains conversational memory for the active call via LangGraph thread checkpointing.
    - Preserves backward compatibility if call_id is omitted.
    """
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # Optional authentication extraction
    customer = None
    if credentials and credentials.credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            cid = int(payload.get("sub"))
            customer = db.scalar(select(Customer).where(Customer.id == cid))
        except Exception:
            pass

    # If call_id is supplied, customer MUST be authenticated and own the session
    if request.call_id:
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for call sessions.",
            )

        session = session_registry.validate_session_access(
            request.call_id, customer.id
        )

        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This call session has already ended.",
            )

        # Record user message in session history
        session.add_message("user", message)

        try:
            reply = ask_aria(
                message=message,
                call_id=request.call_id,
                customer_id=customer.id,
                customer_name=customer.full_name,
            )
            # Record assistant reply in session history
            session.add_message("assistant", reply)
            return ChatResponse(reply=reply, call_id=request.call_id)

        except Exception:
            logger.exception("Error while processing /api/chat with call_id")
            raise HTTPException(
                status_code=500,
                detail="Aria is temporarily unavailable. Please try again.",
            )

    # Normal Chatbot path (BOT OPTION 1: no call_id provided)
    # Uses pure tool-less conversational LLM
    try:
        reply = ask_chat_bot(
            message=message,
            customer_name=customer.full_name if customer else None,
            chat_history=request.history,
        )
        return ChatResponse(reply=reply)

    except Exception:
        logger.exception("Error while processing chatbot message")
        raise HTTPException(
            status_code=500,
            detail="Aura's chatbot is temporarily unavailable. Please try again.",
        )


@app.post("/api/chatbot", response_model=ChatResponse)
def chatbot_direct(
    request: ChatRequest,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Session = Depends(get_db),
):
    """
    Dedicated endpoint for BOT OPTION 1: Aura Skincare Chatbot.
    Directly connected to a pure Gemini LLM with NO tools attached.
    Provides expert botanical skincare recommendations, routines, and tips.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    customer = None
    if credentials and credentials.credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            cid = int(payload.get("sub"))
            customer = db.scalar(select(Customer).where(Customer.id == cid))
        except Exception:
            pass

    try:
        reply = ask_chat_bot(
            message=message,
            customer_name=customer.full_name if customer else None,
            chat_history=request.history,
        )
        return ChatResponse(reply=reply)

    except Exception:
        logger.exception("Error while processing /api/chatbot")
        raise HTTPException(
            status_code=500,
            detail="Aura's chatbot is temporarily unavailable. Please try again.",
        )


@app.post("/api/tts")
async def text_to_speech(payload: TTSRequest):
    """
    Synthesize speech audio (MP3) using Edge Cloud Neural TTS.
    Defaults to the natural 'en-IN-NeerjaNeural' voice for Aria.
    """
    clean_text = payload.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty.",
        )

    # Strip markdown syntax (e.g. asterisks, backticks, hashtags) for natural spoken audio
    clean_text = re.sub(r'[*_#`~]', '', clean_text)
    clean_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean_text)  # link text only

    voice = payload.voice.strip() if payload.voice else "en-IN-NeerjaNeural"
    rate = payload.rate.strip() if payload.rate else "+20%"

    try:
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate)
        audio_stream = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.extend(chunk["data"])

        if not audio_stream:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No audio generated.",
            )

        return Response(
            content=bytes(audio_stream),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=aria_speech.mp3",
                "Cache-Control": "public, max-age=3600",
            },
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Edge-TTS speech synthesis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Neural TTS service temporarily unavailable.",
        )


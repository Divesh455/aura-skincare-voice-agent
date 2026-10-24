import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(
        ..., min_length=2, max_length=100, description="Full name of customer"
    )
    email: str = Field(
        ..., min_length=5, max_length=255, description="Customer email address"
    )
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (min 8 chars, 1 letter, 1 number)"
    )
    password_confirm: str = Field(
        ..., min_length=8, max_length=128, description="Password confirmation"
    )

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        name = v.strip()
        if len(name) < 2:
            raise ValueError("Full name must be at least 2 characters long.")
        return name

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        email = v.strip().lower()
        # Standard email format validation regex
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            raise ValueError("Please provide a valid email address.")
        return email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number.")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Password and password confirmation do not match.")
        return self


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class CustomerProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    welcome_message: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: CustomerProfileResponse


class StartCallResponse(BaseModel):
    call_id: str
    greeting: str
    customer_name: str


class EndCallRequest(BaseModel):
    duration_seconds: float | None = Field(default=None, description="Call duration in seconds from client")


class CallSummaryResponse(BaseModel):
    customer_intent: str
    order_id: str | None = None
    resolution_status: str
    call_summary: str
    important_details: str
    requires_human_support: bool
    is_saved: bool
    saved_record_id: int | None = None
    email_scheduled: bool = False
    email_status_message: str | None = None


class EndCallResponse(BaseModel):
    success: bool
    call_id: str
    message: str
    messages_count: int
    summary: CallSummaryResponse


class SavedInteractionResponse(BaseModel):
    id: int
    customer_id: int
    call_id: str
    customer_intent: str
    order_id: str | None = None
    important_details: str
    resolution_status: str
    requires_human_support: bool
    call_summary: str
    email_delivery_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmailDeliveryStatusUpdateRequest(BaseModel):
    interaction_id: int
    call_id: str
    status: str = Field(..., description="'delivered' or 'failed'")
    provider_message_id: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    call_id: str | None = None
    history: list[dict[str, str]] | None = None


class ChatResponse(BaseModel):
    reply: str
    call_id: str | None = None


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    voice: str | None = "en-IN-NeerjaNeural"
    rate: str | None = "+20%"



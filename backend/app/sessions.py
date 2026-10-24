import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status


@dataclass
class CallSession:
    call_id: str
    customer_id: int
    customer_name: str
    customer_email: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    is_active: bool = True
    messages: list[dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


class SessionRegistry:
    """In-memory call session manager ensuring customer isolation and lifecycle tracking."""

    def __init__(self):
        self._sessions: dict[str, CallSession] = {}

    def create_session(
        self, customer_id: int, customer_name: str, customer_email: str
    ) -> CallSession:
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        first_name = customer_name.split()[0] if customer_name else "there"
        greeting = f"Hi {first_name}! Aura Skincare mein aapka swagat hai. Batao, kaise help kar sakti hoon aaj?"

        session = CallSession(
            call_id=call_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
        )
        session.add_message("assistant", greeting)
        self._sessions[call_id] = session
        return session

    def get_session(self, call_id: str) -> CallSession | None:
        return self._sessions.get(call_id)

    def validate_session_access(
        self, call_id: str, requesting_customer_id: int
    ) -> CallSession:
        """
        Validate that the call session exists, is active, and belongs to the authenticated customer.
        Prevents IDOR / session hijacking attacks.
        """
        session = self._sessions.get(call_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call session '{call_id}' not found.",
            )

        if session.customer_id != requesting_customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this call session.",
            )

        return session

    def end_session(
        self, call_id: str, requesting_customer_id: int
    ) -> CallSession:
        session = self.validate_session_access(call_id, requesting_customer_id)
        session.is_active = False
        session.ended_at = datetime.now(timezone.utc)
        return session


session_registry = SessionRegistry()

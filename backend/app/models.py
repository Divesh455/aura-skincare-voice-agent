from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["SavedInteraction"]] = relationship(
        "SavedInteraction", back_populates="customer", cascade="all, delete-orphan"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    courier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    expected_delivery: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    ordered_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    delivered_days_ago: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    items_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer | None"] = relationship("Customer", back_populates="orders")


class SavedInteraction(Base):
    __tablename__ = "saved_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    call_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_intent: Mapped[str] = mapped_column(String(255), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    important_details: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False)
    requires_human_support: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    call_summary: Mapped[str] = mapped_column(Text, nullable=False)
    email_delivery_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="interactions")

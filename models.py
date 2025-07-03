from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from database import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)
    rate_limits: Mapped[list["RateLimit"]] = relationship("RateLimit", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    tier: Mapped[SubscriptionTier] = mapped_column(SQLEnum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")

class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    requests_count: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rate_limits")

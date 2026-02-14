from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table
from core.database.models import Base, BillingTier
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum



class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"

class BillingPlan(Base):
    __tablename__ = "billing_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(Enum(BillingTier), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price_usd = Column(Float, nullable=False)
    yearly_price_usd = Column(Float, nullable=True)  # 10% discount applied
    billing_cycle = Column(String(20), default="monthly")
    max_agents = Column(Integer, nullable=False)
    max_api_calls_per_month = Column(Integer, nullable=False)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("billing_plans.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus, values_callable=lambda x: [item.value for item in x]), default=SubscriptionStatus.PENDING)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=True)
    paystack_subscription_code = Column(String(100), unique=True)
    paystack_customer_code = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("BillingPlan")
    payments = relationship("Payment", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount_usd = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus, values_callable=lambda x: [item.value for item in x]), default=PaymentStatus.PENDING)
    paystack_reference = Column(String(100), unique=True)
    paystack_transaction_id = Column(String(100))
    payment_method = Column(String(50), default="paystack")
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    subscription = relationship("Subscription", back_populates="payments")

class Usage(Base):
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    api_calls_count = Column(Integer, default=0)
    agent_usage = Column(JSON, default={})  # Store usage per agent
    storage_used_mb = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")
    subscription = relationship("Subscription")

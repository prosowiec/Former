"""SQLAlchemy models for authentication."""

from datetime import datetime
from pydantic import HttpUrl
from sqlalchemy import Column, Float, Integer, String, DateTime, Boolean, Text, JSON, UniqueConstraint, ForeignKey
import uuid

from .db import Base


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # None if using OAuth
    name = Column(String(255), nullable=True)
    surname = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True)  # G
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class UserBillingInfo(Base):
    """User billing and form fill quota tracking for Stripe transactions."""
    
    __tablename__ = "user_billing_info"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_amount_paid = Column(Float, default=0.0, nullable=False)  # Total amount user has paid
    form_fills_remaining = Column(Integer, default=10, nullable=False)  # Remaining form fills
    form_fills_used = Column(Integer, default=0, nullable=False)  # Total form fills used
    stripe_customer_id = Column(String(255), nullable=True, unique=True)  # Stripe customer ID
    stripe_subscription_id = Column(String(255), nullable=True)  # Stripe subscription ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserBillingInfo(user_id={self.user_id}, total_amount_paid={self.total_amount_paid}, form_fills_remaining={self.form_fills_remaining})>"


class StripeTransaction(Base):
    """Transaction history for Stripe payments."""
    
    __tablename__ = "stripe_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    stripe_transaction_id = Column(String(255), nullable=False, unique=True, index=True)  # Stripe payment intent ID
    amount = Column(Float, nullable=False)  # Amount paid in this transaction
    currency = Column(String(3), default="USD", nullable=False)  # Currency code
    form_fills_purchased = Column(Integer, default=0, nullable=False)  # Number of form fills purchased
    status = Column(String(50), nullable=False)  # e.g., 'succeeded', 'pending', 'failed'
    description = Column(Text, nullable=True)  # Transaction description
    stripe_metadata = Column(JSON, nullable=True)  # Additional metadata from Stripe
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<StripeTransaction(user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class AirflowTriggerInternalRequest(Base):
    __tablename__ = "airflow_trigger_requests"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_email = Column(String(255), nullable=False)
    form_url = Column(String(2048), nullable=False)
    dag_id = Column(String(255), nullable=False)
    run_id = Column(String(255), nullable=False)
    run_name = Column(String(255), nullable=True)
    num_executions = Column(Integer, nullable=False)
    base_interval_minutes = Column(Float, nullable=False)
    interval_jitter_minutes = Column(Float, nullable=False)
    age_profile = Column(String(50), nullable=True)
    political_leaning = Column(String(50), nullable=True)
    risk_tolerance = Column(String(50), nullable=True)
    verbosity = Column(String(50), nullable=True)
    formality = Column(String(50), nullable=True)
    state = Column(String(50), default="active", nullable=False)  # active, cancelled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AirflowProgress(Base):
    """Model to track Airflow DAG run progress."""
    
    __tablename__ = "airflow_progress"
    run_id = Column(String(255), primary_key=True)
    numberOfSuccessfulRuns = Column(Integer, default=0, nullable=False)
    hasFailedRuns = Column(Boolean, default=False, nullable=False)
    expectedTotalRuns = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<AirflowProgress(run_id={self.run_id}, numberOfSuccessfulRuns={self.numberOfSuccessfulRuns}, hasFailedRuns={self.hasFailedRuns}, expectedTotalRuns={self.expectedTotalRuns})>"


class FormPageAnswersCache(Base):
    __tablename__ = "form_page_answers_cache"

    id         = Column(Integer, primary_key=True)
    form_url   = Column(String(2048), nullable=False)
    page_index = Column(Integer, nullable=False)
    questions  = Column(JSON, nullable=False)
    answers    = Column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint("form_url", "page_index"),
    )    
    
class FormRunAnswers(Base):
    """Store answers used for each run - references the cache or stores run-specific data."""
    
    __tablename__ = "form_run_answers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(255), nullable=False, index=True)  # Airflow run_id
    execution_index = Column(Integer, nullable=False)  # Which execution in the run (0-indexed)
    form_url = Column(String(2048), nullable=False)
    cache_id = Column(String(36), nullable=True)  # Reference to FormAnswersCache (if cached)
    answers = Column(JSON, nullable=False)  # The actual answers used
    questions = Column(JSON, nullable=False)  # The questions at time of fill
    success = Column(Boolean, default=None, nullable=True)  # null = in progress, True = success, False = failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<FormRunAnswers(run_id={self.run_id}, execution_index={self.execution_index}, form_url={self.form_url}, success={self.success})>"

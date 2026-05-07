"""SQLAlchemy models for authentication."""

from datetime import datetime
from pydantic import HttpUrl
from sqlalchemy import Column, Float, Integer, String, DateTime, Boolean
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

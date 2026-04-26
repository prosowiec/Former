"""SQLAlchemy models for authentication."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
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
    google_id = Column(String(255), unique=True, nullable=True)  # Google OAuth ID
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

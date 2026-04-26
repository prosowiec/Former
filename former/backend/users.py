from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from .db import SessionLocal
from .models import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(password, password_hash)


def get_user(email: str, db: Optional[Session] = None) -> Optional[Dict]:
    """Get user by email."""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "surname": user.surname,
                "username": user.username,
            }
        return None
    finally:
        if close_db:
            db.close()


def authenticate_user(email: str, password: str, db: Optional[Session] = None) -> Optional[Dict]:
    """Authenticate user with email and password."""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "surname": user.surname,
            "username": user.username,
        }
    finally:
        if close_db:
            db.close()


def create_user(
    email: str,
    password: str,
    name: str = None,
    surname: str = None,
    username: str = None,
    db: Optional[Session] = None
) -> Dict:
    """Create a new user."""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User already exists")
        
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            surname=surname,
            username=username or email,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "surname": new_user.surname,
            "username": new_user.username,
        }
    except IntegrityError:
        db.rollback()
        raise ValueError("User already exists")
    finally:
        if close_db:
            db.close()


def get_or_create_oauth_user(
    email: str,
    name: str = None,
    picture: str = None,
    google_id: str = None,
    db: Optional[Session] = None
) -> Dict:
    """Get or create a user from OAuth (Google)."""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # Try to find by email first
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update google_id if provided and not set
            if google_id and not user.google_id:
                user.google_id = google_id
                db.commit()
                db.refresh(user)
            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "surname": user.surname,
                "username": user.username,
            }
        
        # Create new user
        new_user = User(
            email=email,
            name=name,
            google_id=google_id,
            username=email,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "surname": new_user.surname,
            "username": new_user.username,
        }
    finally:
        if close_db:
            db.close()

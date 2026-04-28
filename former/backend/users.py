from http.client import HTTPException
from fastapi import HTTPException
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


def get_user(email: str, db: Session) -> Optional[Dict]:
    """Get user by email."""    
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


def authenticate_user(email: str, password: str, db: Session) -> Optional[Dict]:
    """Authenticate user with email and password."""
    
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
    

def create_user(
    email: str,
    password: str,
    name: str,
    surname: str,
    username: str,
    db: Session
    ) -> Dict:
    """Create a new user."""    
    try:
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
    except IntegrityError as e:
        db.rollback()
        print("ERROR:", e)

        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )

def get_or_create_oauth_user(
    email: str,
    name: str,
    surname: str,
    google_id: str,
    db: Session
    ) -> Dict:
    
    """Get or create a user from OAuth (Google)."""
    
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
        surname=surname,
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

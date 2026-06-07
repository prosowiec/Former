from http.client import HTTPException
from fastapi import HTTPException
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import asyncio

from .db import SessionLocal
from .models import User, UserBillingInfo
from .auth import generate_email_verification_token, generate_password_reset_token
from ..config import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_SERVER,
    MAIL_PORT,
    EMAIL_VERIFY_URL,
    PASSWORD_RESET_URL,
    FRONTEND_URL,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(conf)


async def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    html: str = None
) -> bool:
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[recipient_email],
            body=html or body,
            subtype=MessageType.html,
        )

        await fast_mail.send_message(message)
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    

def send_email_sync(
    recipient_email: str,
    subject: str,
    body: str,
    html: str = None
) -> bool:
    """
    Synchronous wrapper for send_email.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(send_email(recipient_email, subject, body, html))


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
            "email_verified": user.email_verified
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
        "email_verified": user.email_verified
    }
    

def create_user(email: str, password: str, name: str, surname: str, db: Session) -> Dict:
    """Create a new user."""    
    try:
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            surname=surname,
            username= f"{name.strip()} {surname.strip()}",
            email_verified=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create billing info with default 10 form fills
        billing_info = UserBillingInfo(
            user_id=new_user.id,
            total_amount_paid=0.0,
            form_fills_remaining=20,
            form_fills_used=0,
        )
        db.add(billing_info)
        db.commit()
                
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "surname": new_user.surname,
            "username": new_user.username,
            "email_verified": new_user.email_verified
        }
    except IntegrityError as e:
        db.rollback()
        print("ERROR:", e)

        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )

def get_or_create_oauth_user(email: str, name: str, surname: str, google_id: str, db: Session) -> Dict:
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
    
    # Create new user - OAuth users have verified emails
    new_user = User(
        email=email,
        name=name,
        surname=surname,
        google_id=google_id,
        username=email,
        email_verified=True,  # OAuth email is already verified by provider
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    billing_info = UserBillingInfo(
        user_id=new_user.id,
        total_amount_paid=0.0,
        form_fills_remaining=10,
        form_fills_used=0,
    )
    db.add(billing_info)
    db.commit()
    
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "name": new_user.name,
        "surname": new_user.surname,
        "username": new_user.username,
    }


def send_email_verification(email: str, db: Session) -> Optional[str]:
    """Generate email verification token and send verification email to user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If already verified, no need to send again
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate verification token
    token, expires = generate_email_verification_token()
    user.email_verification_token = token
    user.email_verification_token_expires = expires
    db.commit()
    
    # Create verification link
    verify_link = f"{EMAIL_VERIFY_URL}?token={token}"
    
    # Prepare email content
    subject = "Email Verification - Former App"
    body = f"""Welcome to Former App!

Please verify your email by clicking the link below:
{verify_link}

This link will expire in 24 hours.

If you did not create this account, please ignore this email."""
    
    html = f"""<html>
    <body>
        <h2>Welcome to Former App!</h2>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email</a></p>
        <p>Or copy and paste this link:</p>
        <p>{verify_link}</p>
        <p style="color: #666; font-size: 12px;">This link will expire in 24 hours.</p>
        <p style="color: #666; font-size: 12px;">If you did not create this account, please ignore this email.</p>
    </body>
</html>"""
    
    # Send email
    email_sent = send_email_sync(email, subject, body, html)
    
    if not email_sent:
        # Log error but don't fail the request - token is still valid
        print(f"Warning: Failed to send verification email to {email}")
    
    return token


def verify_email(token: str, db: Session) -> Optional[Dict]:
    """Verify email using token."""
    user = db.query(User).filter(User.email_verification_token == token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    # Check if token expired
    if user.email_verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token has expired")
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_token_expires = None
    db.commit()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "email_verified": user.email_verified,
        "message": "Email verified successfully"
    }


def change_password(email: str, old_password: str, new_password: str, db: Session) -> Dict:
    """Change user password."""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.password_hash:
        raise HTTPException(status_code=400, detail="User has no password set (OAuth user)")
    
    # Verify old password
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    # Hash and set new password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


def request_password_reset(email: str, db: Session) -> Dict:
    """Generate password reset token and send password reset email."""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if user exists (security best practice)
        return {"message": "If email exists, password reset link has been sent"}
    
    if not user.password_hash:
        raise HTTPException(status_code=400, detail="Cannot reset password for OAuth users")
    
    # Generate reset token
    token, expires = generate_password_reset_token()
    user.password_reset_token = token
    user.password_reset_token_expires = expires
    db.commit()
    
    # Create password reset link
    reset_link = f"{PASSWORD_RESET_URL}?token={token}"
    
    # Prepare email content
    subject = "Password Reset Request - Former App"
    body = f"""Password Reset Request

We received a request to reset the password for your Former App account.

Please reset your password by clicking the link below:
{reset_link}

This link will expire in 1 hour.

If you did not request this, please ignore this email and your password will remain unchanged."""
    
    html = f"""<html>
    <body>
        <h2>Password Reset Request</h2>
        <p>We received a request to reset the password for your Former App account.</p>
        <p>Please reset your password by clicking the link below:</p>
        <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
        <p>Or copy and paste this link:</p>
        <p>{reset_link}</p>
        <p style="color: #666; font-size: 12px;">This link will expire in 1 hour.</p>
        <p style="color: #666; font-size: 12px;">If you did not request this, please ignore this email and your password will remain unchanged.</p>
    </body>
</html>"""
    
    # Send email
    email_sent = send_email_sync(email, subject, body, html)
    
    if not email_sent:
        # Log error but still return success - token is valid
        print(f"Warning: Failed to send password reset email to {email}")
    
    return {"message": "If email exists, password reset link has been sent"}


def reset_password(token: str, new_password: str, db: Session) -> Dict:
    """Reset password using token."""
    user = db.query(User).filter(User.password_reset_token == token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid password reset token")
    
    # Check if token expired
    if user.password_reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Password reset token has expired")
    
    # Hash and set new password
    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successfully"}

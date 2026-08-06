"""Authentication, OAuth, verification, and password endpoints."""

import secrets
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..auth import (
    build_google_login_url,
    create_token_pair,
    get_google_user_from_code,
    verify_token,
)
from ..db import get_db
from ..dependencies import get_current_user, get_verified_user
from ..schemas import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthRegisterRequest,
    ChangePasswordRequest,
    EmailVerificationResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    ResendVerificationEmailRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from ..users import (
    authenticate_user,
    change_password,
    create_user,
    get_or_create_oauth_user,
    get_user,
    request_password_reset,
    reset_password,
    send_email_verification,
    verify_email,
)
from ...config import FRONTEND_URL


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=AuthLoginResponse)
def auth_login(credentials: AuthLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(credentials.email, credentials.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    return AuthLoginResponse(user=UserResponse(**user), tokens=TokenResponse(**tokens))


@router.get("/tokens")
def auth_tokens(request: Request):
    """Exchange HTTP-only OAuth cookies for frontend-managed tokens."""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="No tokens found")

    response = JSONResponse(
        {"access_token": access_token, "refresh_token": refresh_token}
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post("/register", response_model=AuthLoginResponse)
def auth_register(credentials: AuthRegisterRequest, db: Session = Depends(get_db)):
    if get_user(credentials.email, db):
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(
        credentials.email,
        credentials.password,
        credentials.name,
        credentials.surname,
        db=db,
    )
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    return AuthLoginResponse(user=UserResponse(**user), tokens=TokenResponse(**tokens))


@router.get("/google")
def auth_google_login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    return RedirectResponse(url=build_google_login_url(state))


@router.get("/callback")
def auth_callback(request: Request, db: Session = Depends(get_db)):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    stored_state = request.session.get("oauth_state")
    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    del request.session["oauth_state"]
    google_user_info = get_google_user_from_code(code)
    user = get_or_create_oauth_user(
        email=google_user_info["email"],
        name=google_user_info.get("name"),
        surname=google_user_info.get("surname"),
        google_id=google_user_info.get("sub"),
        db=db,
    )
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))

    response = RedirectResponse(url=f"{FRONTEND_URL}/oauth-success")
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.post("/refresh", response_model=TokenResponse)
def auth_refresh(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user = get_user(payload.get("sub"), db)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return TokenResponse(
            **create_token_pair(user["email"], user.get("name"), user.get("surname"))
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token refresh failed") from exc


@router.post("/logout")
def auth_logout():
    response = JSONResponse({"detail": "Logged out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.get("/me")
def auth_me(current_user: Annotated[Dict, Depends(get_current_user)]):
    return JSONResponse({"user": current_user})


@router.post("/verify-email/send", response_model=MessageResponse)
def send_verification_email_endpoint(
    request: ResendVerificationEmailRequest,
    db: Session = Depends(get_db),
):
    send_email_verification(request.email, db)
    return MessageResponse(
        message="Verification email sent. Please check your inbox and click the link to verify your email."
    )


@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email_endpoint(
    verify_data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    return EmailVerificationResponse(**verify_email(verify_data.token, db))


@router.post("/change-password", response_model=MessageResponse)
def change_password_endpoint(
    password_data: ChangePasswordRequest,
    current_user: Annotated[Dict, Depends(get_verified_user)],
    db: Session = Depends(get_db),
):
    result = change_password(
        current_user["email"],
        password_data.old_password,
        password_data.new_password,
        db,
    )
    return MessageResponse(**result)


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset_endpoint(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    result = request_password_reset(reset_data.email, db)
    return MessageResponse(message=result["message"])


@router.post("/password-reset/confirm", response_model=MessageResponse)
def reset_password_endpoint(
    reset_data: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
):
    return MessageResponse(
        **reset_password(reset_data.token, reset_data.new_password, db)
    )

"""Authentication, OAuth, verification, and password endpoints."""

import logging
import secrets
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
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
    AuthRegisterRequest,
    ChangeEmailRequest,
    ChangePasswordRequest,
    EmailVerificationResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    ResendVerificationEmailRequest,
    UserResponse,
    VerifyEmailRequest,
)
from ..users import (
    authenticate_user,
    change_email,
    change_password,
    create_user,
    get_or_create_oauth_user,
    get_user,
    request_password_reset,
    reset_password,
    send_email_verification,
    verify_email,
)
from ...config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    FRONTEND_URL,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

ACCESS_COOKIE_MAX_AGE = 60 * ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS


def _set_auth_cookies(response: Response, tokens: dict) -> None:
    common = {
        "httponly": True,
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE,
        "path": "/",
    }
    response.set_cookie(
        "access_token", tokens["access_token"], max_age=ACCESS_COOKIE_MAX_AGE, **common
    )
    response.set_cookie(
        "refresh_token", tokens["refresh_token"], max_age=REFRESH_COOKIE_MAX_AGE, **common
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post("/login", response_model=UserResponse)
def auth_login(
    credentials: AuthLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(credentials.email, credentials.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    _set_auth_cookies(response, tokens)
    return UserResponse(**user)


@router.post("/register", response_model=UserResponse)
def auth_register(
    credentials: AuthRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    if get_user(credentials.email, db):
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(
        credentials.email,
        credentials.password,
        credentials.name,
        credentials.surname,
        db=db,
    )
    try:
        send_email_verification(user["email"], db)
    except Exception:
        # Registration is durable at this point. A user can retry delivery via
        # /auth/verify-email/send if the mail provider is temporarily down.
        logger.exception("Failed to send registration verification email")
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    _set_auth_cookies(response, tokens)
    return UserResponse(**user)


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

    response = RedirectResponse(url=f"{FRONTEND_URL}/home")
    _set_auth_cookies(response, tokens)
    return response


@router.post("/refresh", response_model=UserResponse)
def auth_refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh cookie missing")
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user = get_user(payload.get("sub"), db)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        _set_auth_cookies(
            response,
            create_token_pair(user["email"], user.get("name"), user.get("surname")),
        )
        return UserResponse(**user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token refresh failed") from exc


@router.post("/logout")
def auth_logout():
    response = JSONResponse({"detail": "Logged out"})
    _clear_auth_cookies(response)
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
    response = JSONResponse(result)
    _clear_auth_cookies(response)
    return response


@router.post("/change-email", response_model=MessageResponse)
def change_email_endpoint(
    email_data: ChangeEmailRequest,
    current_user: Annotated[Dict, Depends(get_verified_user)],
    db: Session = Depends(get_db),
):
    result = change_email(
        current_user["email"],
        email_data.new_email,
        email_data.password,
        db,
    )
    response = JSONResponse(result)
    _clear_auth_cookies(response)
    return response


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

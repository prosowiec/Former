import hashlib
import secrets
from datetime import datetime
from typing import Annotated, Dict, Optional

import httpx
import stripe
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from former.backend.models import AirflowProgress, AirflowTriggerInternalRequest, UserBillingInfo, StripeTransaction, User


from .auth import build_google_login_url, get_google_user_from_code, create_token_pair, verify_token
from ..config import FRONTEND_URL, SECRET_KEY, STRIPE_SECRET_KEY
from .dagOperations import trigger_airflow_dag, cancel_airflow_dag
from .schemas import (
    AirflowRunResponse,
    AirflowTriggerRequest,
    AirflowTriggerResponse,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthLoginResponse,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    UserBillingInfoResponse,
    StripeTransactionResponse,
    StripeTransactionRequest,
    UpdateFormFillsRequest,
    CreatePaymentIntentRequest,
    CreatePaymentIntentResponse,
    ConfirmPaymentRequest,
    VerifyEmailRequest,
    ResendVerificationEmailRequest,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailVerificationResponse,
    MessageResponse,
)
from .users import authenticate_user, create_user, get_user, get_or_create_oauth_user, send_email_verification, verify_email, change_password, request_password_reset, reset_password
from .db import get_db, init_db

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> Dict:
    """Dependency to get current user from JWT token in Authorization header."""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user(email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

app = FastAPI(
    title="Former Airflow Trigger API",
    description="Trigger the Airflow form filler DAG with a form URL.",
    version="0.1.0",
)

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=AuthLoginResponse)
def auth_login(credentials: AuthLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(credentials.email, credentials.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )

@app.get("/auth/tokens")
def auth_tokens(request: Request):
    """Exchange httpOnly OAuth cookies for tokens the frontend can store."""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    
    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="No tokens found")
    
    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
    # Clear the httpOnly cookies — frontend takes over storage from here
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@app.post("/auth/register", response_model=AuthLoginResponse)
def auth_register(credentials: AuthRegisterRequest, db: Session = Depends(get_db)):
    if get_user(credentials.email, db):
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(credentials.email, credentials.password, credentials.name, credentials.surname, db=db)
    
    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )


@app.get("/auth/google")
def auth_google_login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state  # store in session, not a separate cookie
    google_login_url = build_google_login_url(state)
    return RedirectResponse(url=google_login_url)


@app.get("/auth/callback")
def auth_callback(request: Request, db: Session = Depends(get_db)):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    stored_state = request.session.get("oauth_state")  # read from session

    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    # Consume the state
    del request.session["oauth_state"]

    google_user_info = get_google_user_from_code(code)
    user = get_or_create_oauth_user(
        email=google_user_info["email"],
        name=google_user_info.get("name"),
        surname=google_user_info.get("surname"),
        google_id=google_user_info.get("sub"),
        db=db
    )

    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))

    response = RedirectResponse(url=f"{FRONTEND_URL}/oauth-success")
    response.set_cookie(key="access_token", value=tokens["access_token"],
                        httponly=True, secure=False, samesite="lax")
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"],
                        httponly=True, secure=False, samesite="lax")

    return response

@app.post("/auth/refresh", response_model=TokenResponse)
def auth_refresh(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        user = get_user(email, db)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Create new token pair
        tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
        
        return TokenResponse(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token refresh failed")


@app.post("/auth/logout")
def auth_logout():
    response = JSONResponse({"detail": "Logged out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


def get_verified_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> Dict:
    """Dependency to get current user and verify email is verified."""
    # Call get_current_user synchronously (it handles the same as before)
    # We're doing the email verification check here
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user(email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if email is verified
        db_user = db.query(User).filter(User.email == email).first()
        if not db_user or not db_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required to access this resource"
            )
        
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/auth/me")
def auth_me(current_user: Annotated[Dict, Depends(get_current_user)]):
    """Get current authenticated user."""
    return JSONResponse({"user": current_user})


@app.post("/auth/verify-email/send", response_model=MessageResponse)
def send_verification_email(request: ResendVerificationEmailRequest, db: Session = Depends(get_db)):
    """Send email verification link to user."""
    send_email_verification(request.email, db)
    return MessageResponse(message="Verification email sent. Please check your inbox and click the link to verify your email.")


@app.post("/auth/verify-email", response_model=EmailVerificationResponse)
def verify_email_endpoint(verify_data: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email using token."""
    result = verify_email(verify_data.token, db)
    return EmailVerificationResponse(**result)


@app.post("/auth/change-password", response_model=MessageResponse)
def change_password_endpoint(
    password_data: ChangePasswordRequest,
    current_user: Annotated[Dict, Depends(get_verified_user)],
    db: Session = Depends(get_db)
):
    """Change user's password."""
    result = change_password(current_user["email"], password_data.old_password, password_data.new_password, db)
    return MessageResponse(**result)


@app.post("/auth/password-reset/request", response_model=MessageResponse)
def request_password_reset_endpoint(reset_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset."""
    result = request_password_reset(reset_data.email, db)
    return MessageResponse(message=result["message"])


@app.post("/auth/password-reset/confirm", response_model=MessageResponse)
def reset_password_endpoint(reset_data: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    result = reset_password(reset_data.token, reset_data.new_password, db)
    return MessageResponse(**result)

def get_progress_state(progress: AirflowProgress) -> str:
    if not progress:
        return "queued"
    if progress.hasFailedRuns:
        return "failed"
    if progress.numberOfSuccessfulRuns >= progress.expectedTotalRuns:
        return "success"
    if progress.numberOfSuccessfulRuns > 0:
        return "running"
    return "queued"


def build_run_id(base_run_id: Optional[str], user_id: str, max_length: int = 255) -> str:
    if base_run_id:
        candidate = f"{base_run_id}_{user_id}"
    else:
        candidate = f"former_run_{secrets.token_hex(8)}"

    if len(candidate) <= max_length:
        return candidate

    digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:16]
    prefix_length = max_length - len(digest) - 1
    return f"{candidate[:prefix_length]}_{digest}"


@app.get("/airflow/runs", response_model=list[AirflowRunResponse])
def list_airflow_runs(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Return all DAG runs triggered by the current user."""
    runs = (
        db.query(AirflowTriggerInternalRequest)
        .filter_by(user_email=current_user["email"])
        .order_by(AirflowTriggerInternalRequest.created_at.desc())
        .all()
    )

    run_ids = [run.run_id for run in runs]
    progress_by_run = {}
    if run_ids:
        progress_rows = db.query(AirflowProgress).filter(AirflowProgress.run_id.in_(run_ids)).all()
        progress_by_run = {row.run_id: row for row in progress_rows}

    result = []
    for run in runs:
        progress = progress_by_run.get(run.run_id)
        state = run.state if run.state == "cancelled" else get_progress_state(progress)
        result.append(
            {
                "dag_id": run.dag_id,
                "dag_run_id": run.run_id,
                "form_url": run.form_url,
                "num_executions": run.num_executions,
                "base_interval_minutes": run.base_interval_minutes,
                "interval_jitter_minutes": run.interval_jitter_minutes,
                "created_at": run.created_at.isoformat() if run.created_at else datetime.utcnow().isoformat(),
                "state": state,
                "run_name": run.run_name,
                "age_profile": run.age_profile,
                "political_leaning": run.political_leaning,
                "risk_tolerance": run.risk_tolerance,
                "verbosity": run.verbosity,
                "formality": run.formality,
                "progress": {
                    "numberOfSuccessfulRuns": progress.numberOfSuccessfulRuns,
                    "hasFailedRuns": progress.hasFailedRuns,
                    "expectedTotalRuns": progress.expectedTotalRuns,
                }
                if progress
                else None,
            }
        )
    return result


@app.post("/airflow/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(
    payload: AirflowTriggerRequest,
    current_user: Annotated[Dict, Depends(get_verified_user)],
    db: Session = Depends(get_db)
) -> AirflowTriggerResponse:
    """Trigger an Airflow DAG. Requires JWT authentication."""
    
    try:
        dag_run_id = build_run_id(payload.run_id, current_user["id"])
        response_payload = trigger_airflow_dag(
            str(payload.form_url),
            payload.dag_id,
            current_user["id"],
            dag_run_id,
            payload.num_executions,
            payload.base_interval_minutes,
            payload.interval_jitter_minutes,
        )

        db.add(AirflowTriggerInternalRequest(
            user_email=current_user["email"],
            form_url=str(payload.form_url),
            dag_id=payload.dag_id,
            run_id=dag_run_id,
            run_name=payload.run_name,
            num_executions=payload.num_executions,
            base_interval_minutes=payload.base_interval_minutes,
            interval_jitter_minutes=payload.interval_jitter_minutes,
            age_profile=payload.conf_personality.get("age_profile") if payload.conf_personality else None,
            political_leaning=payload.conf_personality.get("political_leaning") if payload.conf_personality else None,
            risk_tolerance=payload.conf_personality.get("risk_tolerance") if payload.conf_personality else None,
            verbosity=payload.conf_personality.get("verbosity") if payload.conf_personality else None,
            formality=payload.conf_personality.get("formality") if payload.conf_personality else None,
        ))        
        db.commit()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Airflow API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to call Airflow API: {exc}")

    dag_run_id = response_payload.get("dag_run_id") or response_payload.get("dag_run", {}).get("dag_run_id", "")
    state = response_payload.get("state", "unknown")

    return AirflowTriggerResponse(
        dag_id=payload.dag_id,
        dag_run_id=dag_run_id,
        state=state,
        num_executions=payload.num_executions,
        base_interval_minutes=payload.base_interval_minutes,
        interval_jitter_minutes=payload.interval_jitter_minutes,
        airflow_response=response_payload,
    )


@app.post("/airflow/runs/{dag_run_id}/cancel")
async def  cancel_airflow_run(
    dag_run_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Cancel an Airflow DAG run. If it's a parent DAG, cancels all child DAG runs too. 
    Requires JWT authentication."""
    
    # Verify that the run belongs to the current user
    run = (
        db.query(AirflowTriggerInternalRequest)
        .filter_by(run_id=dag_run_id, user_email=current_user["email"])
        .first()
    )
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail="Run not found or you don't have permission to cancel it"
        )
    
    try:
        response = await cancel_airflow_dag(run.dag_id, dag_run_id, cancel_children=True)
        
        # Update the state in the database
        run.state = "cancelled"
        
        db.commit()
        
        return {
            "dag_run_id": dag_run_id,
            "state": "cancelled",
            "message": "Run cancelled successfully",
            "airflow_response": response,
        }
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Airflow API error: {exc.response.text}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel run: {exc}"
        )


@app.get("/billing/info", response_model=UserBillingInfoResponse)
def get_billing_info(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get current user's billing information."""
    billing_info = db.query(UserBillingInfo).filter_by(user_id=current_user["id"]).first()
    
    if not billing_info:
        raise HTTPException(status_code=404, detail="Billing information not found")
    
    return UserBillingInfoResponse(
        id=billing_info.id,
        user_id=billing_info.user_id,
        total_amount_paid=billing_info.total_amount_paid,
        form_fills_remaining=billing_info.form_fills_remaining,
        form_fills_used=billing_info.form_fills_used,
        stripe_customer_id=billing_info.stripe_customer_id,
        stripe_subscription_id=billing_info.stripe_subscription_id,
        created_at=billing_info.created_at.isoformat() if billing_info.created_at else None,
        updated_at=billing_info.updated_at.isoformat() if billing_info.updated_at else None,
    )


@app.post("/billing/transaction", response_model=StripeTransactionResponse)
def create_billing_transaction(
    transaction: StripeTransactionRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Record a Stripe transaction and update user's billing info."""
    
    # Check if transaction already exists
    existing = db.query(StripeTransaction).filter_by(
        stripe_transaction_id=transaction.stripe_transaction_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Transaction already recorded")
    
    # Create transaction record
    stripe_transaction = StripeTransaction(
        user_id=current_user["id"],
        stripe_transaction_id=transaction.stripe_transaction_id,
        amount=transaction.amount,
        currency=transaction.currency,
        form_fills_purchased=transaction.form_fills_purchased,
        status=transaction.status,
        description=transaction.description,
        stripe_metadata=transaction.stripe_metadata,
    )
    
    db.add(stripe_transaction)
    
    # Update user's billing info if transaction succeeded
    if transaction.status == "succeeded":
        billing_info = db.query(UserBillingInfo).filter_by(user_id=current_user["id"]).first()
        
        if not billing_info:
            raise HTTPException(status_code=404, detail="Billing information not found")
        
        billing_info.total_amount_paid += transaction.amount
        billing_info.form_fills_remaining += transaction.form_fills_purchased
    
    db.commit()
    db.refresh(stripe_transaction)
    
    return StripeTransactionResponse(
        id=stripe_transaction.id,
        user_id=stripe_transaction.user_id,
        stripe_transaction_id=stripe_transaction.stripe_transaction_id,
        amount=stripe_transaction.amount,
        currency=stripe_transaction.currency,
        form_fills_purchased=stripe_transaction.form_fills_purchased,
        status=stripe_transaction.status,
        description=stripe_transaction.description,
        created_at=stripe_transaction.created_at.isoformat() if stripe_transaction.created_at else None,
    )


@app.post("/billing/deduct-form-fills")
def deduct_form_fills(
    request_data: UpdateFormFillsRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Deduct form fills from user's remaining balance."""
    
    billing_info = db.query(UserBillingInfo).filter_by(user_id=current_user["id"]).first()
    
    if not billing_info:
        raise HTTPException(status_code=404, detail="Billing information not found")
    
    if billing_info.form_fills_remaining < request_data.form_fills_to_deduct:
        raise HTTPException(status_code=400, detail="Insufficient form fills remaining")
    
    billing_info.form_fills_remaining -= request_data.form_fills_to_deduct
    billing_info.form_fills_used += request_data.form_fills_to_deduct
    
    db.commit()
    db.refresh(billing_info)
    
    return {
        "form_fills_remaining": billing_info.form_fills_remaining,
        "form_fills_used": billing_info.form_fills_used,
        "message": f"Successfully deducted {request_data.form_fills_to_deduct} form fills",
    }


@app.get("/billing/transactions", response_model=list[StripeTransactionResponse])
def get_transactions(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get all transactions for the current user."""
    transactions = (
        db.query(StripeTransaction)
        .filter_by(user_id=current_user["id"])
        .order_by(StripeTransaction.created_at.desc())
        .all()
    )
    
    return [
        StripeTransactionResponse(
            id=t.id,
            user_id=t.user_id,
            stripe_transaction_id=t.stripe_transaction_id,
            amount=t.amount,
            currency=t.currency,
            form_fills_purchased=t.form_fills_purchased,
            status=t.status,
            description=t.description,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in transactions
    ]


@app.post("/billing/create-payment-intent", response_model=CreatePaymentIntentResponse)
def create_payment_intent(
    request_data: CreatePaymentIntentRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Create a Stripe PaymentIntent for the user."""
    
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    
    # Get or create customer
    billing_info = db.query(UserBillingInfo).filter_by(user_id=current_user["id"]).first()
    if not billing_info:
        raise HTTPException(status_code=404, detail="Billing information not found")
    
    try:
        # Create or retrieve Stripe customer
        if not billing_info.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user["email"],
                name=f"{current_user.get('name', '')} {current_user.get('surname', '')}".strip(),
                metadata={"user_id": current_user["id"]},
            )
            billing_info.stripe_customer_id = customer.id
            db.commit()
        
        # Create PaymentIntent
        amount_cents = int(request_data.amount_eur * 100)  # Stripe uses cents
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="eur",
            customer=billing_info.stripe_customer_id,
            metadata={
                "user_id": current_user["id"],
                "form_fills_purchased": request_data.form_fills_purchased,
            },
        )
        
        return CreatePaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount_eur=request_data.amount_eur,
            form_fills_purchased=request_data.form_fills_purchased,
        )
    except stripe.error.CardError as e:
        raise HTTPException(status_code=400, detail=f"Card error: {e.user_message}")
    except stripe.error.RateLimitError:
        raise HTTPException(status_code=429, detail="Too many requests")
    except stripe.error.AuthenticationError:
        raise HTTPException(status_code=401, detail="Stripe authentication failed")
    except stripe.error.APIConnectionError:
        raise HTTPException(status_code=503, detail="Stripe service unavailable")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@app.post("/billing/confirm-payment", response_model=StripeTransactionResponse)
def confirm_payment(
    request_data: ConfirmPaymentRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Confirm payment and record transaction."""
    
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    
    try:
        # Retrieve the PaymentIntent
        intent = stripe.PaymentIntent.retrieve(request_data.payment_intent_id)
        
        if intent.status != "succeeded":
            raise HTTPException(status_code=400, detail=f"Payment not successful: {intent.status}")
        
        # Get user's billing info
        billing_info = db.query(UserBillingInfo).filter_by(user_id=current_user["id"]).first()
        if not billing_info:
            raise HTTPException(status_code=404, detail="Billing information not found")
        
        # Check if transaction already recorded
        existing = db.query(StripeTransaction).filter_by(
            stripe_transaction_id=intent.id
        ).first()
        
        if existing:
            return StripeTransactionResponse(
                id=existing.id,
                user_id=existing.user_id,
                stripe_transaction_id=existing.stripe_transaction_id,
                amount=existing.amount,
                currency=existing.currency,
                form_fills_purchased=existing.form_fills_purchased,
                status=existing.status,
                description=existing.description,
                created_at=existing.created_at.isoformat() if existing.created_at else None,
            )
        
        # Get metadata
        metadata = intent.get("metadata", {})
        form_fills = int(metadata.get("form_fills_purchased", 0))
        
        # Create transaction record
        stripe_transaction = StripeTransaction(
            user_id=current_user["id"],
            stripe_transaction_id=intent.id,
            amount=intent.amount / 100,  # Convert from cents
            currency=intent.currency.upper(),
            form_fills_purchased=form_fills,
            status="succeeded",
            description=f"{form_fills} form fills",
            stripe_metadata=dict(intent),
        )
        
        db.add(stripe_transaction)
        
        # Update billing info
        billing_info.total_amount_paid += stripe_transaction.amount
        billing_info.form_fills_remaining += form_fills
        
        db.commit()
        db.refresh(stripe_transaction)
        
        return StripeTransactionResponse(
            id=stripe_transaction.id,
            user_id=stripe_transaction.user_id,
            stripe_transaction_id=stripe_transaction.stripe_transaction_id,
            amount=stripe_transaction.amount,
            currency=stripe_transaction.currency,
            form_fills_purchased=stripe_transaction.form_fills_purchased,
            status=stripe_transaction.status,
            description=stripe_transaction.description,
            created_at=stripe_transaction.created_at.isoformat() if stripe_transaction.created_at else None,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming payment: {str(e)}")

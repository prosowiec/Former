"""Billing balance, transaction, and Stripe endpoints."""

from typing import Annotated, Dict

import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..models import StripeTransaction, UserBillingInfo
from ..schemas import (
    ConfirmPaymentRequest,
    CreatePaymentIntentRequest,
    CreatePaymentIntentResponse,
    StripeTransactionRequest,
    StripeTransactionResponse,
    UpdateFormFillsRequest,
    UserBillingInfoResponse,
)
from ...config import STRIPE_SECRET_KEY


router = APIRouter(prefix="/billing", tags=["billing"])


def _transaction_response(transaction: StripeTransaction) -> StripeTransactionResponse:
    return StripeTransactionResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        stripe_transaction_id=transaction.stripe_transaction_id,
        amount=transaction.amount,
        currency=transaction.currency,
        form_fills_purchased=transaction.form_fills_purchased,
        status=transaction.status,
        description=transaction.description,
        created_at=(
            transaction.created_at.isoformat() if transaction.created_at else None
        ),
    )


def _billing_for_user(db: Session, user_id: str) -> UserBillingInfo:
    billing_info = db.query(UserBillingInfo).filter_by(user_id=user_id).first()
    if not billing_info:
        raise HTTPException(status_code=404, detail="Billing information not found")
    return billing_info


@router.get("/info", response_model=UserBillingInfoResponse)
def get_billing_info(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    billing_info = _billing_for_user(db, current_user["id"])
    return UserBillingInfoResponse(
        id=billing_info.id,
        user_id=billing_info.user_id,
        total_amount_paid=billing_info.total_amount_paid,
        form_fills_remaining=billing_info.form_fills_remaining,
        form_fills_used=billing_info.form_fills_used,
        stripe_customer_id=billing_info.stripe_customer_id,
        stripe_subscription_id=billing_info.stripe_subscription_id,
        created_at=(billing_info.created_at.isoformat() if billing_info.created_at else None),
        updated_at=(billing_info.updated_at.isoformat() if billing_info.updated_at else None),
    )


@router.post("/transaction", response_model=StripeTransactionResponse)
def create_billing_transaction(
    transaction: StripeTransactionRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    existing = (
        db.query(StripeTransaction)
        .filter_by(stripe_transaction_id=transaction.stripe_transaction_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Transaction already recorded")

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

    if transaction.status == "succeeded":
        billing_info = _billing_for_user(db, current_user["id"])
        billing_info.total_amount_paid += transaction.amount
        billing_info.form_fills_remaining += transaction.form_fills_purchased

    db.commit()
    db.refresh(stripe_transaction)
    return _transaction_response(stripe_transaction)


@router.post("/deduct-form-fills")
def deduct_form_fills(
    request_data: UpdateFormFillsRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    billing_info = _billing_for_user(db, current_user["id"])
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


@router.get("/transactions", response_model=list[StripeTransactionResponse])
def get_transactions(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(StripeTransaction)
        .filter_by(user_id=current_user["id"])
        .order_by(StripeTransaction.created_at.desc())
        .all()
    )
    return [_transaction_response(transaction) for transaction in transactions]


@router.post("/create-payment-intent", response_model=CreatePaymentIntentResponse)
def create_payment_intent(
    request_data: CreatePaymentIntentRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")

    billing_info = _billing_for_user(db, current_user["id"])
    try:
        if not billing_info.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user["email"],
                name=f"{current_user.get('name', '')} {current_user.get('surname', '')}".strip(),
                metadata={"user_id": current_user["id"]},
            )
            billing_info.stripe_customer_id = customer.id
            db.commit()

        intent = stripe.PaymentIntent.create(
            amount=int(request_data.amount_eur * 100),
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
    except stripe.error.CardError as exc:
        raise HTTPException(status_code=400, detail=f"Card error: {exc.user_message}") from exc
    except stripe.error.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="Too many requests") from exc
    except stripe.error.AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Stripe authentication failed") from exc
    except stripe.error.APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="Stripe service unavailable") from exc
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=500, detail=f"Stripe error: {exc}") from exc


@router.post("/confirm-payment", response_model=StripeTransactionResponse)
def confirm_payment(
    request_data: ConfirmPaymentRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")

    try:
        intent = stripe.PaymentIntent.retrieve(request_data.payment_intent_id)
        if intent.status != "succeeded":
            raise HTTPException(
                status_code=400,
                detail=f"Payment not successful: {intent.status}",
            )

        billing_info = _billing_for_user(db, current_user["id"])
        existing = (
            db.query(StripeTransaction)
            .filter_by(stripe_transaction_id=intent.id)
            .first()
        )
        if existing:
            return _transaction_response(existing)

        metadata = intent.to_dict()["metadata"]
        raw_form_fills = metadata["form_fills_purchased"]
        try:
            form_fills = int(raw_form_fills)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid form_fills_purchased value in metadata: {raw_form_fills}"
            ) from exc

        stripe_transaction = StripeTransaction(
            user_id=current_user["id"],
            stripe_transaction_id=intent.id,
            amount=intent.amount / 100,
            currency=intent.currency.upper(),
            form_fills_purchased=form_fills,
            status="succeeded",
            description=f"{form_fills} form fills",
            stripe_metadata=(
                intent.to_dict_recursive()
                if hasattr(intent, "to_dict_recursive")
                else {}
            ),
        )
        db.add(stripe_transaction)
        billing_info.total_amount_paid += stripe_transaction.amount
        billing_info.form_fills_remaining += form_fills
        db.commit()
        db.refresh(stripe_transaction)
        return _transaction_response(stripe_transaction)
    except HTTPException:
        raise
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=500, detail=f"Stripe error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error confirming payment: {exc}",
        ) from exc

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from former.backend.models import AirflowTriggerInternalRequest, Base, User, UserBillingInfo
import former.backend.routers.airflow as airflow_router_module
import former.backend.routers.billing as billing_router_module
from former.backend.schemas import AirflowTriggerRequest, ChangePasswordRequest, ConfirmPaymentRequest


def test_form_destination_allowlist_blocks_ssrf_targets():
    request = AirflowTriggerRequest(
        form_url="https://docs.google.com/forms/d/e/form-id/viewform"
    )
    assert request.form_url.host == "docs.google.com"

    for url in (
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "https://example.com/form",
        "https://docs.google.com.evil.example/form",
    ):
        with pytest.raises(ValidationError):
            AirflowTriggerRequest(form_url=url)


def test_change_password_contract_uses_old_password():
    parsed = ChangePasswordRequest(
        old_password="old-password",
        new_password="new-password",
    )
    assert parsed.old_password == "old-password"
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="old-password",
            new_password="new-password",
        )


def test_trigger_reserves_full_quota_before_dispatch(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(id="user-1", email="person@example.com", email_verified=True)
    billing = UserBillingInfo(
        user_id="user-1", form_fills_remaining=3, form_fills_used=0
    )
    session.add_all((user, billing))
    session.commit()

    observed = {}

    def fake_dispatch(db, trigger):
        observed["remaining_at_dispatch"] = db.query(UserBillingInfo).filter_by(
            user_id="user-1"
        ).one().form_fills_remaining
        trigger.state = "active"
        db.commit()
        return {"dag_run_id": trigger.run_id, "state": "queued"}

    monkeypatch.setattr(airflow_router_module, "dispatch_trigger", fake_dispatch)
    payload = AirflowTriggerRequest(
        form_url="https://docs.google.com/forms/d/e/form-id/viewform",
        num_executions=3,
        base_interval_minutes=5,
    )
    response = airflow_router_module.airflow_trigger(
        payload,
        {"id": "user-1", "email": "person@example.com"},
        session,
    )

    assert response.num_executions == 3
    assert observed["remaining_at_dispatch"] == 0
    trigger = session.query(AirflowTriggerInternalRequest).one()
    assert trigger.quota_reserved == 3

    with pytest.raises(HTTPException) as exc:
        airflow_router_module.airflow_trigger(
            AirflowTriggerRequest(
                form_url="https://docs.google.com/forms/d/e/another/viewform"
            ),
            {"id": "user-1", "email": "person@example.com"},
            session,
        )
    assert exc.value.status_code == 409


def test_stripe_confirmation_credits_verified_payment_once(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(User(id="user-1", email="person@example.com", email_verified=True))
    session.add(UserBillingInfo(
        user_id="user-1",
        stripe_customer_id="cus_1",
        form_fills_remaining=0,
        form_fills_used=0,
    ))
    session.commit()

    class Intent:
        id = "pi_verified"
        status = "succeeded"
        customer = "cus_1"
        currency = "eur"
        amount = 500

        def to_dict(self):
            return {"metadata": {"user_id": "user-1", "form_fills_purchased": "50"}}

        def to_dict_recursive(self):
            return self.to_dict()

    monkeypatch.setattr(billing_router_module, "STRIPE_SECRET_KEY", "test-secret")
    monkeypatch.setattr(
        billing_router_module.stripe.PaymentIntent,
        "retrieve",
        lambda _intent_id: Intent(),
    )
    request = ConfirmPaymentRequest(payment_intent_id="pi_verified")
    user = {"id": "user-1", "email": "person@example.com"}

    first = billing_router_module.confirm_payment(request, user, session)
    second = billing_router_module.confirm_payment(request, user, session)
    billing = session.query(UserBillingInfo).filter_by(user_id="user-1").one()
    assert first.id == second.id
    assert billing.form_fills_remaining == 50
    assert float(billing.total_amount_paid) == 5.0

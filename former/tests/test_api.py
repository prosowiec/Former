from former.backend.api import app
from former.backend.routers.airflow import build_run_id, calculate_scheduler_jitter


def test_removed_client_writable_billing_routes():
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    assert ("/billing/transaction", "POST") not in routes
    assert ("/billing/deduct-form-fills", "POST") not in routes
    assert ("/auth/tokens", "GET") not in routes


def test_run_id_is_user_scoped_and_bounded():
    run_id = build_run_id("x" * 300, "user-1")
    assert len(run_id) <= 255
    assert run_id == build_run_id("x" * 300, "user-1")
    assert run_id != build_run_id("x" * 300, "user-2")


def test_server_controls_scheduler_jitter():
    assert calculate_scheduler_jitter(10) == 2

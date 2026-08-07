"""Quota outbox, cache isolation, and terminal idempotency."""

from alembic import op
import sqlalchemy as sa

revision = "20260807_0002"
down_revision = "20260807_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "user_billing_info", "total_amount_paid", type_=sa.Numeric(12, 2),
        postgresql_using="ROUND(total_amount_paid::numeric, 2)",
    )
    op.alter_column(
        "stripe_transactions", "amount", type_=sa.Numeric(12, 2),
        postgresql_using="ROUND(amount::numeric, 2)",
    )
    op.add_column("airflow_trigger_requests", sa.Column("user_id", sa.String(36), nullable=True))
    op.execute("""
        UPDATE airflow_trigger_requests AS r
        SET user_id = u.id FROM users AS u
        WHERE r.user_email = u.email
    """)
    # Old orphan audit rows cannot participate safely in reservation settlement.
    op.execute("DELETE FROM airflow_trigger_requests WHERE user_id IS NULL")
    op.alter_column("airflow_trigger_requests", "user_id", nullable=False)
    op.create_foreign_key("fk_trigger_user", "airflow_trigger_requests", "users", ["user_id"], ["id"])
    op.create_index("ix_trigger_user_id", "airflow_trigger_requests", ["user_id"])
    op.create_unique_constraint("uq_airflow_trigger_run_id", "airflow_trigger_requests", ["run_id"])
    for name in ("quota_reserved", "quota_settled", "quota_refunded", "dispatch_attempts"):
        op.add_column("airflow_trigger_requests", sa.Column(name, sa.Integer(), nullable=False, server_default="0"))
    op.add_column("airflow_trigger_requests", sa.Column("last_dispatch_error", sa.Text()))
    op.add_column("airflow_trigger_requests", sa.Column("dispatched_at", sa.DateTime(timezone=True)))

    # Existing cache entries lack user/personality identity and must not be reused.
    op.execute("DELETE FROM form_page_answers_cache")
    op.drop_constraint("form_page_answers_cache_form_url_page_index_key", "form_page_answers_cache", type_="unique")
    op.add_column("form_page_answers_cache", sa.Column("user_id", sa.String(36), nullable=False))
    op.add_column("form_page_answers_cache", sa.Column("question_hash", sa.String(64), nullable=False))
    op.add_column("form_page_answers_cache", sa.Column("personality_hash", sa.String(64), nullable=False))
    op.create_foreign_key("fk_cache_user", "form_page_answers_cache", "users", ["user_id"], ["id"])
    op.create_unique_constraint(
        "uq_form_answer_cache_identity", "form_page_answers_cache",
        ["user_id", "form_url", "page_index", "question_hash", "personality_hash"],
    )
    op.create_unique_constraint("uq_form_run_execution", "form_run_answers", ["run_id", "execution_index"])


def downgrade():
    raise RuntimeError("Integrity hardening migration is intentionally irreversible")

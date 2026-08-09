"""Baseline schema before integrity hardening."""

from alembic import op
import sqlalchemy as sa

revision = "20260807_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("name", sa.String(255)), sa.Column("surname", sa.String(255)),
        sa.Column("google_id", sa.String(255)), sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("email_verification_token", sa.String(255)), sa.Column("email_verification_token_expires", sa.DateTime()),
        sa.Column("password_reset_token", sa.String(255)), sa.Column("password_reset_token_expires", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"), sa.UniqueConstraint("username"),
    )
    op.create_table(
        "user_billing_info",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("total_amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("form_fills_remaining", sa.Integer(), nullable=False),
        sa.Column("form_fills_used", sa.Integer(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255)), sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "stripe_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stripe_transaction_id", sa.String(255), nullable=False, unique=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("form_fills_purchased", sa.Integer(), nullable=False), sa.Column("status", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("stripe_metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "airflow_trigger_requests",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("form_url", sa.String(2048), nullable=False), sa.Column("dag_id", sa.String(255), nullable=False),
        sa.Column("run_id", sa.String(255), nullable=False), sa.Column("run_name", sa.String(255)),
        sa.Column("num_executions", sa.Integer(), nullable=False), sa.Column("base_interval_minutes", sa.Float(), nullable=False),
        sa.Column("interval_jitter_minutes", sa.Float(), nullable=False), sa.Column("age_profile", sa.String(50)),
        sa.Column("political_leaning", sa.String(50)), sa.Column("risk_tolerance", sa.String(50)),
        sa.Column("verbosity", sa.String(50)), sa.Column("formality", sa.String(50)),
        sa.Column("state", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expected_end_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "airflow_progress", sa.Column("run_id", sa.String(255), primary_key=True),
        sa.Column("numberOfSuccessfulRuns", sa.Integer(), nullable=False), sa.Column("hasFailedRuns", sa.Boolean(), nullable=False),
        sa.Column("expectedTotalRuns", sa.Integer(), nullable=False),
    )
    op.create_table(
        "form_page_answers_cache", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("form_url", sa.String(2048), nullable=False), sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False), sa.Column("answers", sa.JSON(), nullable=False),
        sa.UniqueConstraint("form_url", "page_index"),
    )
    op.create_table(
        "form_run_answers", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(255), nullable=False), sa.Column("execution_index", sa.Integer(), nullable=False),
        sa.Column("form_url", sa.String(2048), nullable=False), sa.Column("cache_id", sa.String(36)),
        sa.Column("answers", sa.JSON(), nullable=False), sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("success", sa.Boolean()), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    for table in ("form_run_answers", "form_page_answers_cache", "airflow_progress", "airflow_trigger_requests", "stripe_transactions", "user_billing_info", "users"):
        op.drop_table(table)

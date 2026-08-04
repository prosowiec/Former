"""Copy Former application tables from MSSQL into an empty PostgreSQL database.

The application does not require MSSQL or ODBC after this one-time migration.
Install ``pyodbc`` and a SQL Server ODBC driver only in the environment where
this script is executed.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence

from sqlalchemy import MetaData, create_engine, func, select, text
from sqlalchemy.engine import Engine

from former.backend.db import Base
from former.backend import models  # noqa: F401 - registers tables on Base.metadata


TABLE_ORDER = (
    "users",
    "user_billing_info",
    "stripe_transactions",
    "airflow_trigger_requests",
    "airflow_progress",
    "form_page_answers_cache",
    "form_run_answers",
)


def _require_url(value: str | None, name: str) -> str:
    if not value or not value.strip():
        raise SystemExit(f"{name} must be provided")
    return value.strip()


def _validate_dialects(source: Engine, target: Engine) -> None:
    if source.dialect.name != "mssql":
        raise SystemExit("SOURCE_DATABASE_URL must point to MSSQL")
    if target.dialect.name != "postgresql":
        raise SystemExit("DATABASE_URL must point to PostgreSQL")


def _ensure_target_is_empty(target: Engine) -> None:
    with target.connect() as connection:
        populated = []
        for table_name in TABLE_ORDER:
            table = Base.metadata.tables[table_name]
            if connection.scalar(select(func.count()).select_from(table)):
                populated.append(table_name)
    if populated:
        names = ", ".join(populated)
        raise SystemExit(f"Target database is not empty; populated tables: {names}")


def migrate(source_url: str, target_url: str, batch_size: int = 500) -> None:
    source = create_engine(source_url, pool_pre_ping=True)
    target = create_engine(target_url, pool_pre_ping=True)
    _validate_dialects(source, target)

    Base.metadata.create_all(target)
    _ensure_target_is_empty(target)

    source_metadata = MetaData()
    source_metadata.reflect(bind=source, only=list(TABLE_ORDER))

    with source.connect() as source_connection, target.begin() as target_connection:
        for table_name in TABLE_ORDER:
            source_table = source_metadata.tables[table_name]
            target_table = Base.metadata.tables[table_name]
            copied = 0

            result = source_connection.execution_options(
                stream_results=True
            ).execute(select(source_table))
            while rows := result.mappings().fetchmany(batch_size):
                payload: Sequence[dict] = [dict(row) for row in rows]
                target_connection.execute(target_table.insert(), payload)
                copied += len(payload)

            print(f"{table_name}: copied {copied} rows")

        target_connection.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('form_page_answers_cache', 'id'),
                    COALESCE(MAX(id), 1),
                    MAX(id) IS NOT NULL
                )
                FROM form_page_answers_cache
                """
            )
        )

    source.dispose()
    target.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=os.getenv("SOURCE_DATABASE_URL"),
        help="MSSQL SQLAlchemy URL (or set SOURCE_DATABASE_URL)",
    )
    parser.add_argument(
        "--target",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL SQLAlchemy URL (or set DATABASE_URL)",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    migrate(
        _require_url(args.source, "SOURCE_DATABASE_URL"),
        _require_url(args.target, "DATABASE_URL"),
        args.batch_size,
    )


if __name__ == "__main__":
    main()


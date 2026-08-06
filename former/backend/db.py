from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from ..config import DATABASE_URL, SQLALCHEMY_ECHO

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from former.backend import models
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE airflow_trigger_requests
                ADD COLUMN IF NOT EXISTS expected_end_at TIMESTAMP WITH TIME ZONE
            """))
            connection.execute(text("""
                UPDATE airflow_trigger_requests
                SET expected_end_at =
                    (created_at AT TIME ZONE 'UTC')
                    + ((num_executions * base_interval_minutes) * INTERVAL '1 minute')
                WHERE expected_end_at IS NULL
            """))
            connection.execute(text("""
                ALTER TABLE airflow_trigger_requests
                ALTER COLUMN expected_end_at SET NOT NULL
            """))

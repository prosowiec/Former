from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

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

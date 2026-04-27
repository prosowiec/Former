import os
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"Missing environment variable: {name}")
    return value.strip()


AIRFLOW_HOST = os.getenv("AIRFLOW_HOST", "http://localhost:9090")
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", f"{AIRFLOW_HOST}/api/v2")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
DEFAULT_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "form_filler_pipeline")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-secret")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))  # 7 days

GOOGLE_CLIENT_ID = require_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = require_env("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT_URI = require_env("GOOGLE_OAUTH_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

AUTH_USERS_FILE = os.getenv("AUTH_USERS_FILE", os.path.join(os.path.dirname(__file__), "auth_users.json"))
DEFAULT_AUTH_USERNAME = os.getenv("DEFAULT_AUTH_USERNAME", "")
DEFAULT_AUTH_PASSWORD = os.getenv("DEFAULT_AUTH_PASSWORD", "")

# MSSQL Database Configuration
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YourPassword123!")
DB_HOST = os.getenv("DB_HOST", "host.docker.internal")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_NAME = os.getenv("DB_NAME", "former")

# Database URL for SQLAlchemy (MSSQL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
)

# SQLAlchemy settings
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"


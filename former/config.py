import os
from dotenv import find_dotenv, load_dotenv

# Load the nearest .env file from anywhere in the repo tree.
load_dotenv(find_dotenv())


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"Missing environment variable: {name}")
    return value.strip()


AIRFLOW_HOST = os.getenv("AIRFLOW_HOST", "http://localhost:9090")
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", f"{AIRFLOW_HOST}/api/v2")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
AIRFLOW_DB_URI = os.getenv("AIRFLOW_DB_URI", "postgresql+psycopg2://airflow:airflow@postgres/airflow")
DEFAULT_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "form_filler_plan")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-secret")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

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

MAX_SUBMISSIONS = 250
WAIT_BETWEEN = (30, 90)

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSftl5wRWwtjEhbeecNjaO880pn5vr3-25hqq7K06eEdjLY2nw/viewform?usp=header"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM


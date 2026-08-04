import os
from dotenv import find_dotenv, load_dotenv

# Load the nearest .env file from anywhere in the repo tree.
load_dotenv(find_dotenv())


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(f"Missing environment variable: {name}")
    return value.strip()


AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
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

APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
if APP_ENV not in {"local", "production", "test"}:
    raise RuntimeError(
        "APP_ENV must be one of: local, production, test "
        f"(received {APP_ENV!r})"
    )

IS_LOCAL = APP_ENV == "local"
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost" if IS_LOCAL else "https://former.com.pl",
)

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

AUTH_USERS_FILE = os.getenv("AUTH_USERS_FILE", os.path.join(os.path.dirname(__file__), "auth_users.json"))

# Every environment uses the same variable names. The deployment layer selects
# their values; application code never falls back from production to LOCAL_*.
DB_USER = os.getenv("DB_USER", "former")
DB_PASSWORD = os.getenv("DB_PASSWORD", "former")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "former")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)
AIRFLOW_DB_URI = os.getenv("AIRFLOW_DB_URI", DATABASE_URL)

AIRFLOW_HOST = os.getenv(
    "AIRFLOW_HOST",
    "http://localhost:9090" if IS_LOCAL else "http://localhost:8080",
)
AIRFLOW_BASE_URL = os.getenv(
    "AIRFLOW_BASE_URL",
    f"{AIRFLOW_HOST}/api/v2",
)

# SQLAlchemy settings
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

MAX_SUBMISSIONS = 250
WAIT_BETWEEN = (30, 90)

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSftl5wRWwtjEhbeecNjaO880pn5vr3-25hqq7K06eEdjLY2nw/viewform?usp=header"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM

# Email Configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-app-password")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@former.app")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Former App")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_TLS = os.getenv("MAIL_TLS", "true").lower() == "true"
MAIL_SSL = os.getenv("MAIL_SSL", "false").lower() == "true"

# Email verification and password reset URLs (for links sent in emails)
EMAIL_VERIFY_URL = os.getenv("EMAIL_VERIFY_URL", f"{FRONTEND_URL}/verify-email")
PASSWORD_RESET_URL = os.getenv("PASSWORD_RESET_URL", f"{FRONTEND_URL}/reset-password")

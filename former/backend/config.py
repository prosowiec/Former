import os
from dotenv import load_dotenv

load_dotenv()

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

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

AUTH_USERS_FILE = os.getenv("AUTH_USERS_FILE", os.path.join(os.path.dirname(__file__), "auth_users.json"))
DEFAULT_AUTH_USERNAME = os.getenv("DEFAULT_AUTH_USERNAME", "")
DEFAULT_AUTH_PASSWORD = os.getenv("DEFAULT_AUTH_PASSWORD", "")


from typing import Dict, Optional

from pydantic import BaseModel, Field, HttpUrl, constr

from .config import DEFAULT_DAG_ID


class AirflowTriggerRequest(BaseModel):
    form_url: HttpUrl
    dag_id: Optional[str] = DEFAULT_DAG_ID
    run_id: Optional[str] = None
    num_executions: int = Field(1, ge=1)
    base_interval_minutes: float = Field(10.0, ge=0.1)
    interval_jitter_minutes: float = Field(2.0, ge=0.0)


class AirflowTriggerResponse(BaseModel):
    dag_id: str
    dag_run_id: str
    state: str
    num_executions: int
    base_interval_minutes: float
    interval_jitter_minutes: float
    airflow_response: Dict


class AuthLoginRequest(BaseModel):
    email: str
    password: constr(min_length=8, max_length=256)


class AuthRegisterRequest(BaseModel):
    email: str
    password: constr(min_length=8, max_length=256)
    name: str
    surname: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None


class AuthLoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str

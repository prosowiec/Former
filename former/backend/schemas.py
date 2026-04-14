from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional
from .config import DEFAULT_DAG_ID

class AirflowTriggerRequest(BaseModel):
    form_url: HttpUrl
    dag_id: Optional[str] = DEFAULT_DAG_ID
    run_id: Optional[str] = None


class AirflowTriggerResponse(BaseModel):
    dag_id: str
    dag_run_id: str
    state: str
    airflow_response: Dict

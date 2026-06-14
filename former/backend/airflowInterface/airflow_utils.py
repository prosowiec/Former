import asyncio
from datetime import datetime, timezone
import os
from typing import Dict, Optional

import httpx
from sqlalchemy import create_engine, text
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

from former.config import AIRFLOW_DB_URI, AIRFLOW_HOST, AIRFLOW_PASSWORD, AIRFLOW_USERNAME


db_engine = create_engine(AIRFLOW_DB_URI)

def get_airflow_access_token() -> str:
    token_url = f"{AIRFLOW_HOST}/auth/token"
    payload = {"username": AIRFLOW_USERNAME, "password": AIRFLOW_PASSWORD}

    with httpx.Client(timeout=30) as client:
        response = client.post(token_url, json=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")


async def get_child_dag_runs(parent_run_id: str, client) -> list:
    """Get all child DAG runs by querying the Airflow database directly."""    
    # We use asyncio.to_thread to prevent the synchronous SQLAlchemy 
    # connection from blocking your async HTTP operations
    return await asyncio.to_thread(_fetch_child_runs_from_db, parent_run_id)

def _fetch_child_runs_from_db(parent_run_id: str) -> list:
    """Synchronous helper to execute the SQL query."""
    child_runs = []
    
    query = text("""
        SELECT dag_id, run_id, state 
        FROM dag_run 
        WHERE dag_id = 'form_filler_dag' 
          AND run_id LIKE :pattern
    """)
    
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {"pattern": f"{parent_run_id}__item_%"})
            
            for row in result:
                child_runs.append({
                    "dag_run_id": row.run_id,
                    "state": row.state
                })
    except Exception as e:
        print(f"Warning: Could not fetch child DAG runs from DB: {e}")
        
    return child_runs

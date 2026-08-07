"""Shared extraction, answer-cache, and child settlement helpers."""

import hashlib
import json
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller
from former.backend.models import (
    AirflowProgress,
    AirflowTriggerInternalRequest,
    FormPageAnswersCache,
    FormRunAnswers,
    UserBillingInfo,
)
from former.config import OPENAI_API_KEY
from former.fillWorkflow.detectors import detect_question_type
from former.fillWorkflow.extract import extract_options, extract_title, extract_question_items


def _stable_hash(value) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_form_url(form_url: str) -> str:
    parts = urlsplit(form_url)
    query = urlencode(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() != "usp"
    )
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, query, ""))


def get_or_create_page_answers(
    session,
    page_idx: int,
    extracted: list,
    personality: dict,
    form_url: str,
    user_id: str,
) -> list:
    identity = {
        "user_id": user_id,
        "form_url": _normalize_form_url(form_url),
        "page_index": page_idx,
        "question_hash": _stable_hash(extracted),
        "personality_hash": _stable_hash(personality),
    }
    cached = session.query(FormPageAnswersCache).filter_by(**identity).first()
    if cached:
        print(f"Page {page_idx}: cache hit")
        return cached.answers

    print(f"Page {page_idx}: cache miss - calling LLM")
    answers = chatgptFormFiller(OPENAI_API_KEY).get_selection(extracted, personality)
    session.add(FormPageAnswersCache(
        **identity,
        questions=extracted,
        answers=answers,
    ))
    session.commit()
    return answers


def extract_answers(page, platform, page_idx: int) -> tuple:
    seen, extracted, page_elements = set(), [], []
    for q in extract_question_items(page, platform):
        title = extract_title(q, platform)
        qtype = detect_question_type(q, platform)
        if qtype == "section_title":
            continue
        options = extract_options(q, qtype, platform)
        signature = (title.lower(), qtype, json.dumps(options, sort_keys=True, default=str))
        if signature in seen:
            continue
        seen.add(signature)
        extracted.append({
            "id": page_idx * 100 + len(extracted) + 1,
            "question": title,
            "type": qtype,
            "options": options,
        })
        page_elements.append((q, qtype))
    return extracted, page_elements


def record_terminal_child(conf: dict, result: dict) -> None:
    """Persist one terminal child and settle its reserved quota exactly once."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    session = sessionmaker(bind=engine)()
    try:
        run_id = conf["run_id"]
        execution_index = int(conf["execution_index"])
        if session.query(FormRunAnswers).filter_by(
            run_id=run_id, execution_index=execution_index
        ).first():
            return

        trigger = session.query(AirflowTriggerInternalRequest).filter_by(
            run_id=run_id
        ).with_for_update().first()
        if not trigger:
            raise RuntimeError(f"Missing trigger reservation for {run_id}")

        success = bool(result.get("success"))
        session.add(FormRunAnswers(
            run_id=run_id,
            execution_index=execution_index,
            form_url=conf["form_url"],
            answers=result.get("answers") or [],
            questions=result.get("questions") or [],
            success=success,
            error_message=result.get("error"),
        ))

        progress = session.query(AirflowProgress).filter_by(
            run_id=run_id
        ).with_for_update().first()
        if not progress:
            progress = AirflowProgress(
                run_id=run_id,
                numberOfSuccessfulRuns=0,
                hasFailedRuns=False,
                expectedTotalRuns=int(conf["num_executions"]),
            )
            session.add(progress)
        if success:
            progress.numberOfSuccessfulRuns += 1
        else:
            progress.hasFailedRuns = True

        if trigger.quota_settled + trigger.quota_refunded < trigger.quota_reserved:
            billing = session.query(UserBillingInfo).filter_by(
                user_id=trigger.user_id
            ).with_for_update().first()
            if not billing:
                raise RuntimeError(f"Missing billing record for {trigger.user_id}")
            if success:
                billing.form_fills_used += 1
                trigger.quota_settled += 1
            else:
                billing.form_fills_remaining += 1
                trigger.quota_refunded += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def record_task_failure(context) -> None:
    """Airflow callback for failures before the normal status task can run."""
    dag_run = context.get("dag_run")
    conf = dict((dag_run.conf if dag_run else {}) or {})
    required = {"run_id", "execution_index", "num_executions", "form_url"}
    if not required.issubset(conf):
        return
    record_terminal_child(conf, {
        "success": False,
        "error": str(context.get("exception") or "Airflow task failed"),
        "questions": [],
        "answers": [],
    })

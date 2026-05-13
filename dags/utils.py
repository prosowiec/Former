from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller
from former.backend.models import FormPageAnswersCache
from former.config import OPENAI_API_KEY
from former.fillWorkflow.detectors import detect_question_type
from former.fillWorkflow.extract import extract_options, extract_title, extract_question_items
import json

def get_or_create_page_answers(session, page_idx: int, extracted: list, personality: dict, form_url: str) -> list:
    cached = (
        session.query(FormPageAnswersCache)
        .filter_by(form_url=form_url, page_index=page_idx)
        .first()
    )
    if cached:
        print(f"  Page {page_idx}: cache hit")
        return cached.answers

    print(f"  Page {page_idx}: cache miss — calling LLM")
    answers = chatgptFormFiller(OPENAI_API_KEY).get_selection(extracted, personality)
    session.add(FormPageAnswersCache(
        form_url=form_url,
        page_index=page_idx,
        questions=extracted,
        answers=answers,
    ))
    session.commit()
    print(f"  Page {page_idx}: answers stored")
    return answers


def extract_answers(page, platform, page_idx: int) -> tuple:
    
    seen, extracted, page_elements = set(), [], []
    for q in extract_question_items(page, platform):
        title = extract_title(q, platform)
        qtype = detect_question_type(q, platform)
        if qtype == "section_title":
            continue
        options = extract_options(q, qtype, platform)
        sig = (title.lower(), qtype, json.dumps(options, sort_keys=True, default=str))
        if sig in seen:
            continue
        seen.add(sig)
        extracted.append({"id": page_idx * 100 + len(extracted) + 1,
                            "question": title, "type": qtype, "options": options})
        page_elements.append((q, qtype))

    return extracted, page_elements
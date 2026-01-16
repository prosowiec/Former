import time
import random
from browser import launch_browser
from detectors import detect_MS_question_type
from extractors.extractMS import *
from human import human_type, human_pause, human_mouse_move, human_scroll, human_before_question
from navigation import go_next_or_submit_MS
from fillers import fillMS
from ANSWERS import RANDOM_ANSWERS

FILLERS = {
    "text": fillMS.fill_text,
    "paragraph": fillMS.fill_paragraph,

    "radio": fillMS.fill_multiple_choice,
    "checkboxes": fillMS.fill_checkboxes,
    "dropdown": fillMS.fill_dropdown,

    "star_rating": fillMS.fill_star_rating,
    "linear_scale": fillMS.fill_linear_scale,
    "nps": fillMS.fill_nps,

    "date": fillMS.fill_date,
    "likert": fillMS.fill_likert,
    "hierarchical_ranking": fillMS.fill_ranking,
}

EXTRACTORS = {
    "text": extract_text,
    "paragraph": extract_paragraph,
    "radio": extract_checkboxes,
    "checkboxes": extract_multiple_choice,
    "dropdown": extract_dropdown,
    "star_rating": extract_star_rating,
    "linear_scale": extract_linear_scale,
    "nps": extract_nps,
    "date": extract_date,
    "likert": extract_likert,
    "hierarchical_ranking": extract_ranking,
}

FORM_URL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u"

OUTPUT_JSON = "form_data.json"
OUTPUT_CSV = "form_data.csv"


def extract_questions(page):
    extracted = []
    question_items = page.query_selector_all("div[data-automation-id='questionItem']")

    qid = 1
    for q in question_items:
        title_el = q.query_selector("span[data-automation-id='questionTitle']")
        title = title_el.inner_text().strip() if title_el else f"Question {qid}"

        q_type = detect_MS_question_type(q)
        qtype = detect_MS_question_type(q)
        extractor = EXTRACTORS.get(qtype)

        options = extractor(q) if extractor else None

        extracted.append({
            "id": qid,
            "question": title,
            "type": q_type,
            "options": options
        })
        qid += 1

    return extracted

def fill_question(page, q, qtype):
    human_before_question(page, q)

    answer_fn = RANDOM_ANSWERS.get(qtype)
    filler_fn = FILLERS.get(qtype)

    if answer_fn and filler_fn:
        answer = answer_fn(q)
        if answer is not None:
            filler_fn(q, answer)

    if random.random() < 0.3:
        human_scroll(page)
        
        
def fill_form(page):
    page.goto(FORM_URL, wait_until="networkidle")

    human_pause(2, 4)
    human_mouse_move(page)
    human_scroll(page)

    while True:
        page.wait_for_selector("div[data-automation-id='questionItem']", timeout=10000)

        questions = page.query_selector_all("div[data-automation-id='questionItem']")
        question_types = [detect_MS_question_type(q) for q in questions]
        extracted = extract_questions(page)
        print(extracted)
        for q, qtype in zip(questions, question_types):
            fill_question(page, q, qtype)

        human_pause(1.5, 3.0)

        if go_next_or_submit_MS(page) == "submitted":
            time.sleep(3)
            break
        
if __name__ == "__main__":
    for i in range(10):
        pw, browser, page = launch_browser()
        print(f"\n🔄 Submission {i + 1}/{10}")

        fill_form(page)

        wait = random.uniform(60, 120)
        print(f"⏳ Waiting {wait:.1f}s before next submission...")
        time.sleep(wait)

        browser.close()
        pw.stop()
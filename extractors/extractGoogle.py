def extract_title(q):
    title_el = (
        q.query_selector("div[role='heading']")
        or q.query_selector("div.freebirdFormviewerComponentsQuestionBaseTitle")
    )
    return title_el.inner_text().strip() if title_el else ""


def extract_radio(q):
    return {
        "type": "linear_scale_radio",
        "question": extract_title(q),
        "options": list(dict.fromkeys(
            r.get_attribute("data-value").strip()
            for r in q.query_selector_all("div[role='radio']")
            if r.get_attribute("data-value")
        ))
    }
    
def extract_checkboxes(q):
    return {
        "type": "checkboxes",
        "question": extract_title(q),
        "options": list(dict.fromkeys(
            c.get_attribute("data-answer-value").strip()
            for c in q.query_selector_all("div[role='checkbox']")
            if c.get_attribute("data-answer-value")
        ))
    }

def extract_dropdown(q):
    return {
        "type": "dropdown",
        "question": extract_title(q),
        "options": list(dict.fromkeys(
            o.get_attribute("data-value").strip()
            for o in q.query_selector_all("div[role='option']")
            if o.get_attribute("data-value")
        ))
    }

def extract_text(q, qtype):
    return {
        "type": qtype,
        "question": extract_title(q),
        "options": []
    }
    
    
def extract_radio_question(q):
    """
    Extracts a normal multiple-choice (radio) question
    Uses data-value instead of visible label text
    """

    title_el = (
        q.query_selector("div[role='heading']")
        or q.query_selector("div.freebirdFormviewerComponentsQuestionBaseTitle")
    )
    question = title_el.inner_text().strip() if title_el else ""

    options = []
    for radio in q.query_selector_all("div[role='radio']"):
        value = radio.get_attribute("data-value")
        if value:
            options.append(value.strip())

    return {
        "type": "linear_scale_radio",
        "question": question,
        "options": options,
    }
    
def extract_matrix_radio(q):
    questionRow = []

    # Row labels
    rows = [
        r.inner_text().strip()
        for r in q.query_selector_all("div[class='V4d7Ke wzWPxe OIC90c']")
    ]

    # Column labels (from first radiogroup)
    columns = []
    first_row_group = q.query_selector("div[role='radiogroup']")
    if first_row_group:
        for radio in first_row_group.query_selector_all("div[role='radio']"):
            val = radio.get_attribute("data-value")
            if val:
                columns.append(val.strip())

    # Build questions per row (same format as checkbox matrix)
    for row in rows:
        question = {
            "type": "radio",
            "question": row,
            "options": [columns]
        }
        questionRow.append(question)

    return {
        "type": "matrix_radio",
        "questionTitle": extract_title(q),
        "options": questionRow
    }
    
def extract_matrix_checkbox(q):
    questionRow = []

    rows = [
        r.inner_text().strip()
        for r in q.query_selector_all("div[class='V4d7Ke wzWPxe OIC90c']")
    ]

    first_row = q.query_selector("div[role='group']")
    if first_row:
        columns = []
        for i, box in enumerate(first_row.query_selector_all("div[role='checkbox']")):
            val = box.get_attribute("data-answer-value")
            if val:
                columns.append(val.strip())
        
        
    for row in rows:
        question = {
                "type": "checkboxes",
                "question": row,
                "options": [columns]
            }
        questionRow.append(question)


    return {
        "type": "matrix_checkbox",
        "questionTitle": extract_title(q),
        "options": questionRow
    }
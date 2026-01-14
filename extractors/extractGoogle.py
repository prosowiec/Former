def extract_title(q):
    title_el = (
        q.query_selector("div[role='heading']")
        or q.query_selector("div.freebirdFormviewerComponentsQuestionBaseTitle")
    )
    return title_el.inner_text().strip() if title_el else ""


def extract_radio(q):
    return {
        "type": "multiple_choice",
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
    
def extract_matrix_radio(q):
    """
    Extracts Google Forms Multiple Choice Grid
    Columns = data-value from radios
    Rows = row headers (questions)
    """

    title_el = (
        q.query_selector("div[role='heading']")
        or q.query_selector("div.freebirdFormviewerComponentsQuestionBaseTitle")
    )
    question = title_el.inner_text().strip() if title_el else ""

    # Rows (sub-questions)
    rows = []
    for row in q.query_selector_all("div[role='rowheader']"):
        text = row.inner_text().strip()
        if text:
            rows.append(text)

    # Columns (options) → from radio data-value
    columns = []

    # Use first row's radios as column source
    first_row = q.query_selector("div[role='radiogroup']")
    if first_row:
        for radio in first_row.query_selector_all("div[role='radio']"):
            value = radio.get_attribute("data-value")
            if value:
                columns.append(value.strip())

    # Deduplicate (safety)
    columns = list(dict.fromkeys(columns))

    return {
        "type": "matrix_radio",
        "question": question,
        "rows": rows,
        "columns": columns,
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
        "type": "multiple_choice",
        "question": question,
        "options": options,
    }
    
def extract_matrix_checkbox(q):
    qfiltered = q.query_selector_all(
        ":not([aria-hidden='true'])"
    )
    

    rows = [
        r.inner_text().strip()
        for r in q.query_selector_all("div[class='V4d7Ke wzWPxe OIC90c']")
        if not r.get_attribute("aria-hidden") 
    ]

    columns = []
    first_row = q.query_selector("div[role='group']")
    if first_row:
        for box in first_row.query_selector_all("div[role='checkbox']"):
            val = box.get_attribute("data-answer-value")
            if val:
                columns.append(val.strip())

    return {
        "type": "matrix_checkbox",
        "question": extract_title(q),
        "rows": rows,
        "columns": list(dict.fromkeys(columns))
    }
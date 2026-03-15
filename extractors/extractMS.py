# ---------- CHOICE ----------

def extract_multiple_choice(q):
    options = [
        c.inner_text().strip()
        for c in q.query_selector_all("div[data-automation-id='choiceItem']")
        if c.inner_text().strip()
    ]

    return options


def extract_checkboxes(q):
    options = [
        c.inner_text().strip()
        for c in q.query_selector_all("div[data-automation-id='choiceItem']")
        if c.inner_text().strip()
    ]

    return options


def extract_dropdown(q):
    select = q.query_selector("select")
    options = []

    if select:
        options = [
            opt.inner_text().strip()
            for opt in select.query_selector_all("option")
            if opt.inner_text().strip()
        ]

    return options

# ---------- TEXT ----------

def extract_text(q):
    el = q.query_selector("input[type='text'], input[data-automation-id='textInput']")
    return {"max_length": el.get_attribute("maxlength") if el else None}


def extract_paragraph(q):
    return []


# ---------- RATING / SCALE ----------

def extract_star_rating(q):
    
    stars = q.query_selector_all("span[role='radio']")
    labels = [
        s.get_attribute("aria-label")
        for s in stars
        if s.get_attribute("aria-label")
    ]

    return labels if labels else []


def extract_linear_scale(q):
    radios = q.query_selector_all("div[role='radio']")
    labels = [r.inner_text().strip() for r in radios if r.inner_text().strip()]

    return labels if labels else []


def extract_nps(q):
    radios = q.query_selector_all("td[role='presentation']")
    scale = [r.inner_text().strip() for r in radios if r.inner_text().strip()]

    return scale if scale else []
# ---------- DATE ----------

def extract_date(q):
    date_input = q.query_selector(
        "input[type='date'], input[role='combobox'][aria-haspopup='dialog']"
    )

    return {
        "format": "DD-YY-YYYY" if date_input else None
    }

# ---------- LIKERT ----------

def extract_likert(q):
    headers = [
        h.inner_text().strip()
        for h in q.query_selector_all('th[data-automation-id="likerTableTh"] span')
        if h.inner_text().strip()
    ]

    statements = [
        s.inner_text().strip()
        for s in q.query_selector_all('th[data-automation-id="likerStatementTd"] span')
        if s.inner_text().strip()
    ]

    questions = [
        {
            "type": "radio",
            "question": statement,
            "options": [headers]
        }
        for statement in statements
    ]

    return questions

# ---------- RANKING ----------

def extract_ranking(q):
    items = q.query_selector_all("div[data-automation-id='rankingItemContent']")
    labels = [
        item.inner_text().strip()
        for item in items
        if item.inner_text().strip()
    ]

    return labels if labels else []

def extract_title(q):
    title_el = q.query_selector("span[data-automation-id='questionTitle']")
    return title_el.inner_text().strip() if title_el else ""

def extract_question_items(page):
    """
    Docstring for extract_question_items
    
    :param page: Description
    """
    question_items = page.query_selector_all("div[data-automation-id='questionItem']")
    return question_items


MS_EXTRACTORS = {
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
    "title": extract_title,
}

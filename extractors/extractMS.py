def extract_options(q):
    options = []
    choice_items = q.query_selector_all("div[data-automation-id='choiceItem']")
    for c in choice_items:
        options.append(c.inner_text().strip())
    return options


def extract_dropdown_options(q):
    options = []
    select = q.query_selector("select")
    if not select:
        return options

    for opt in select.query_selector_all("option"):
        text = opt.inner_text().strip()
        if text:
            options.append(text)
    return options

def extract_star_count(q):
    return len(q.query_selector_all('span[role="radio"]'))


def extract_star_labels(q):
    stars = q.query_selector_all('span[role="radio"]')
    return [s.get_attribute("aria-label") for s in stars if s.get_attribute("aria-label")]


def extract_linear_scale(q):
    radios = q.query_selector_all("div[role='radio']")
    labels = [r.inner_text().strip() for r in radios]
    return {
        "min": labels[0] if labels else None,
        "max": labels[-1] if labels else None,
        "steps": len(labels)
    }


def extract_nps(q):
    radios = q.query_selector_all("td[role='presentation']")
    labels = [r.inner_text().strip() for r in radios]
    return {
        "scale": labels,  # ["0", "1", ..., "10"]
        "min": 0,
        "max": 10
    }
    
def extract_date(q):
    date_input = q.query_selector("input[type='date']")
    return {
        "type": "date",
        "format": "YYYY-MM-DD" if date_input else None
    }

def extract_text(q):
    return {
        "type": "short_text",
        "max_length": q.query_selector("input[type='text']").get_attribute("maxlength")
        if q.query_selector("input[type='text']") else None
    }


def extract_paragraph(q):
    return {
        "type": "paragraph"
    }


def extract_likert_options(q):
    headers = q.query_selector_all('th[data-automation-id="likerTableTh"] span')
    header_texts = [h.inner_text().strip() for h in headers]

    statements = q.query_selector_all('th[data-automation-id="likerStatementTd"] span')
    statement_texts = [s.inner_text().strip() for s in statements]

    return header_texts, statement_texts

def extract_ranking(q):
    items = q.query_selector_all("div[data-automation-id='rankItem']")
    labels = []

    for item in items:
        label = item.inner_text().strip()
        if label:
            labels.append(label)

    return {
        "items": labels,
        "positions": list(range(1, len(labels) + 1))
    }

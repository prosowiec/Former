def extract_options(q):
    options = []
    choice_items = q.query_selector_all("div[data-automation-id='choiceItem']")
    for c in choice_items:
        options.append(c.inner_text().strip())
    return options

def extract_star_count(q):
    stars = q.query_selector_all('span[role="radio"]')
    return len(stars)

def extract_star_labels(q):
    stars = q.query_selector_all('span[role="radio"]')
    return [s.get_attribute("aria-label") for s in stars]

def extract_likert_options(page):
    headers = page.locator('th[data-automation-id="likerTableTh"] span')
    header_texts = [header.text_content().strip() for header in headers.all()]
    
    instructions = page.locator('th[data-automation-id="likerStatementTd"] span')
    instructions_texts = [instruction.text_content().strip() for instruction in instructions.all()]

    return header_texts, instructions_texts

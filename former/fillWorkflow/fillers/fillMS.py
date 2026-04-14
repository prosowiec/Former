import random
import time
from former.fillWorkflow.human import human_type, human_pause


# ---------- TEXT ----------
def fill_text(q, answer):
    el = q.query_selector("input[data-automation-id='textInput']")
    if el:
        el.click()
        human_pause()
        human_type(el, answer)


def fill_paragraph(q, answer):
    el = q.query_selector("textarea")
    if el:
        el.click()
        human_pause()
        human_type(el, answer)


# ---------- CHOICE ----------
def fill_multiple_choice(q, answer):
    choices = q.query_selector_all("div[data-automation-id='choiceItem']")
    for c in choices:
        if c.inner_text().strip().lower() == answer.lower():
            human_pause()
            c.click()
            return


def fill_checkboxes(q, answers):
    choices = q.query_selector_all("div[data-automation-id='choiceItem']")
    for c in choices:
        label = c.inner_text().strip()
        if label in answers:
            human_pause(0.1, 0.3)
            c.click()


def fill_dropdown(q, answer):
    select = q.query_selector("select")
    if not select:
        return

    options = select.query_selector_all("option")
    for i, opt in enumerate(options):
        if opt.inner_text().strip().lower() == answer.lower():
            human_pause()
            select.select_option(index=i)
            return


# ---------- RATING / SCALE ----------
def fill_star_rating(q, answer):
    # answer = answer.lower()
    # answer = answer.replace(" stars", "").replace(" star", "")
    # answer = int(answer)
    radios = q.query_selector_all("span[role='radio']")
    for radio in radios:
        value = radio.get_attribute("aria-label")
        if value == answer:
            human_pause()
            radio.click()
            return
    


def fill_linear_scale(q, answer):
    radios = q.query_selector_all("div[role='radio']")
    if 1 <= answer <= len(radios):
        human_pause()
        radios[answer - 1].click()


def fill_nps(q, answer):
    # NPS is just a 0–10 linear scale
    radios = q.query_selector_all("td[role='presentation']")
    idx = min(int(answer), len(radios) - 1)
    human_pause()
    radios[idx].click()


# ---------- DATE ----------
def fill_date(q, answer):
    date_input = q.query_selector("input[role='combobox'][aria-haspopup='dialog']")
    if date_input:
        date_input.click()
        date_input.fill(answer)


# ---------- LIKERT ----------
def fill_likert(q, answer):
    rows = q.query_selector_all("tr[data-automation-id='likerTableTr']")
    headers = [
        h.inner_text().strip()
        for h in q.query_selector_all('th[data-automation-id="likerTableTh"] span')
        if h.inner_text().strip()
    ]
    for row in rows:
        radios = row.query_selector_all("input[type='radio']")
        row_header_el = row.query_selector('th[data-automation-id="likerStatementTd"]')
        row_header_el = row_header_el.inner_text().strip() if row_header_el else ""

        row_answer = answer.get(row_header_el)
        if row_answer is None:
            continue
        
        if row_answer in headers:
            header_index = headers.index(row_answer)
            human_pause(0.1, 0.3)
            radios[header_index].click()



# ---------- RANKING ----------
def fill_ranking(q, page, answer):
    import time

    def get_items_and_buttons():
        items = q.query_selector_all("div[data-automation-id='rankingItemContent']")
        buttons_areas = q.query_selector_all(".arrow-container")
        label_map = {
            i.query_selector("span").inner_text().strip(): i
            for i in items
        }
        button_map = {
            items[i].query_selector("span").inner_text().strip(): buttons_areas[i]
            for i in range(len(items))
        }
        return label_map, button_map, items



    while True:
        labels, buttons, items = get_items_and_buttons()
        if list(labels.keys()) == answer:
            break
        
        for idx, label in enumerate(labels.keys()):
            designated_index = answer.index(label)
            current_index = idx
            if designated_index == current_index:
                continue
            button = buttons.get(label)
            if not button:
                continue
            if designated_index > current_index:
                down_button = button.query_selector_all("button")[1]
                page.evaluate("(el) => el.click()", down_button)
            else:
                up_button = button.query_selector_all("button")[0]
                page.evaluate("(el) => el.click()", up_button)
            human_pause(0.2, 0.4)

MS_FILLERS = {
    "text": fill_text,
    "paragraph": fill_paragraph,

    "radio": fill_multiple_choice,
    "checkboxes": fill_checkboxes,
    "dropdown": fill_dropdown,

    "star_rating": fill_star_rating,
    "linear_scale": fill_linear_scale,
    "nps": fill_nps,

    "date": fill_date,
    "likert": fill_likert,
    "hierarchical_ranking": fill_ranking,
}


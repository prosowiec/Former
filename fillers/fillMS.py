import random
import time
from human import human_type, human_pause


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
    radios = q.query_selector_all("span[role='radio']")
    if 1 <= answer <= len(radios):
        human_pause()
        radios[answer - 1].click()


def fill_linear_scale(q, answer):
    radios = q.query_selector_all("div[role='radio']")
    if 1 <= answer <= len(radios):
        human_pause()
        radios[answer - 1].click()


def fill_nps(q, answer):
    # NPS is just a 0–10 linear scale
    radios = q.query_selector_all("td[role='presentation']")
    idx = min(answer, len(radios) - 1)
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
    rows = q.query_selector_all("tr")
    for row in rows:
        radios = row.query_selector_all("input[type='radio']")
        if radios and answer < len(radios):
            human_pause(0.1, 0.3)
            radios[answer].check()


# ---------- RANKING ----------
def fill_ranking(q, answer):
    """
    answer = ordered list of labels
    """
    items = q.query_selector_all("div[data-automation-id='rankingItemContent']")
    label_map = {
        i.query_selector("span").inner_text().strip(): i
        for i in items
    }

    for idx, label in enumerate(answer):
        item = label_map.get(label)
        if item:
            select = item.query_selector("select")
            if select:
                human_pause(0.2, 0.4)
                select.select_option(str(idx + 1))

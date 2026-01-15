import random
from config import ANSWERS
from human import human_type

def fill_short_text(q, answer):
    input_el = q.query_selector("input[type='text']")
    if input_el:
        input_el.click()
        human_type(input_el, answer)

def fill_paragraph(q, answer):
    textarea = q.query_selector("textarea")
    if textarea:
        textarea.click()
        human_type(textarea, answer)
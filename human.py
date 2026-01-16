import time
import random

def human_scroll(page):
    scroll_amount = random.randint(100, 400)
    page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
    time.sleep(random.uniform(0.3, 0.8))

def human_mouse_move(page):
    page.mouse.move(
        random.randint(200, 1200),
        random.randint(200, 800),
        steps=random.randint(10, 30)
    )

def human_type(el, text):
    for i, char in enumerate(text):
        if random.random() < 0.05 and i < len(text) - 1:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            el.type(wrong_char, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.1, 0.3))
            el.press('Backspace')
            time.sleep(random.uniform(0.05, 0.15))
        el.type(char, delay=random.randint(60, 180))
        if random.random() < 0.1:
            time.sleep(random.uniform(0.5, 2.0))

def human_pause(a=1.0, b=3.0):
    time.sleep(random.uniform(a, b))


def human_before_question(page, q):
    human_mouse_move(page)
    human_pause(0.8, 2.0)
    q.scroll_into_view_if_needed()
    human_pause(0.3, 0.7)
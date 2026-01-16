import random


RANDOM_ANSWERS = {
    # TEXT
    "text": lambda q: random.choice([
        "Good experience overall",
        "It was fine",
        "No major issues",
        "Pretty straightforward",
    ]),

    "paragraph": lambda q: random.choice([
        "Overall the experience was smooth and easy to understand.",
        "Everything worked as expected with no major problems.",
        "The process was intuitive and efficient.",
    ]),

    # CHOICE
    "radio": lambda q: random.choice([
        c.inner_text().strip()
        for c in q.query_selector_all("div[data-automation-id='choiceItem']")
    ]),

    "checkboxes": lambda q: random.sample(
        [c.inner_text().strip()
         for c in q.query_selector_all("div[data-automation-id='choiceItem']")],
        k=random.randint(1, 2)
    ),

    "dropdown": lambda q: random.choice([
        o.inner_text().strip()
        for o in q.query_selector_all("option")[1:]
    ]),

    # SCALE / RATING
    "star_rating": lambda q: random.randint(3, 5),
    "linear_scale": lambda q: random.randint(1, 5),
    "nps": lambda q: random.randint(6, 10),

    # DATE
    "date": lambda q: "2026-01-15",

    # LIKERT
    "likert": lambda q: random.randint(0, 2),

    # RANKING
    "ranking": lambda q: random.sample(
        [i.inner_text().strip()
         for i in q.query_selector_all("div[data-automation-id='rankingItemContent']")],
        k=len(q.query_selector_all("div[data-automation-id='rankingItemContent']"))
    )
}

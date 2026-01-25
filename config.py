import random
import dotenv
import os

dotenv.load_dotenv()

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSftl5wRWwtjEhbeecNjaO880pn5vr3-25hqq7K06eEdjLY2nw/viewform?usp=header"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

OUTPUT_JSON = "data/form_data.json"
OUTPUT_CSV = "data/form_data.csv"

MAX_SUBMISSIONS = 250
WAIT_BETWEEN = (30, 90)

ANSWERS = [
    "Good experience overall",
    "It was fine",
    "No major issues",
    "Pretty straightforward",
    "Everything went smoothly",
    "Satisfied with the service",
]

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
         for i in q.query_selector_all("div[data-automation-id='c']")],
        k=len(q.query_selector_all("div[data-automation-id='rankingItemContent']"))
    )
}


GOOGLE_ANSWERS = [
    {
        "id": 1,
        "question": "Matrix checkbox",
        "type": "matrix_checkbox",
        "options": {
        "type": "matrix_checkbox",
        "questionTitle": "Matrix checkbox",
        "options": [
            {
            "type": "checkboxes",
            "question": "Wiersz 1",
            "options": [["Kolumna 1", "aadada", "dada"]]
            },
            {
            "type": "checkboxes",
            "question": "Wiersz 2",
            "options": [["Kolumna 1", "aadada", "dada"]]
            },
            {
            "type": "checkboxes",
            "question": "Wiersz 3",
            "options": [["Kolumna 1", "aadada", "dada"]]
            }
        ]
        },
        "ANSWERS": {
        "Wiersz 1": ["Kolumna 1", "dada"],
        "Wiersz 2": ["aadada"],
        "Wiersz 3": ["Kolumna 1"]
        }
    },
    {
        "id": 2,
        "question": "dawdawdasdxzc",
        "type": "time",
        "options": [],
        "ANSWERS": "10:00"
    },
    {
        "id": 3,
        "question": "Tetuje radio",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Tetuje radio",
        "options": ["Opcja 1", "aaa", "Opcja 3"]
        },
        "ANSWERS": "aaa"
    },
    {
        "id": 4,
        "question": "Dropdown",
        "type": "dropdown",
        "options": {
        "type": "dropdown",
        "question": "Dropdown",
        "options": ["Opcja 1", "ab", "b"]
        },
        "ANSWERS": "ab"
    },
    {
        "id": 5,
        "question": "Linear scale",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Linear scale",
        "options": ["1", "2", "3", "4", "5"]
        },
        "ANSWERS": "4"
    },
    {
        "id": 6,
        "question": "Grade",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Grade",
        "options": ["1", "2", "3", "4", "5"]
        },
        "ANSWERS": "5"
    },
    {
        "id": 7,
        "question": "Matrix radio",
        "type": "matrix_radio",
        "options": {
        "type": "matrix_radio",
        "questionTitle": "Matrix radio",
        "options": [
            {
            "type": "radio",
            "question": "Wiersz 1",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "zzz",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "Wiersz 3",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "Wiersz 4",
            "options": [["Kolumna 1", "adad", "aad"]]
            }
        ]
        },
        "ANSWERS": {
        "Wiersz 1": "adad",
        "zzz": "Kolumna 1",
        "Wiersz 3": "aad",
        "Wiersz 4": "adad"
        }
    },
    {
        "id": 8,
        "question": "adawdadawdawda",
        "type": "date",
        "options": [],
        "ANSWERS": "2023-11-15"
    }
]

MS_ANSWERS = [
  {
    "id": 1,
    "question": "1.\nRadio",
    "type": "radio",
    "options": ["Opcja 1", "Opcja 2"],
    "ANSWERS": "Opcja 1"
  },
  {
    "id": 2,
    "question": "2.\nText",
    "type": "text",
    "options": { "max_length": "4000" },
    "ANSWERS": "To ."
  },
  {
    "id": 3,
    "question": "3.\nGrade",
    "type": "star_rating",
    "options": ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"],
    "ANSWERS": "4 Star"
  },
  {
    "id": 4,
    "question": "4.\nDate",
    "type": "date",
    "options": { "format": "DD-YY-YYYY" },
    "ANSWERS": "15-01-2026"
  },
  {
    "id": 5,
    "question": "5.\nCheckbox",
    "type": "hierarchical_ranking",
    "options": ["Opcja 1", "Opcja 2", "Opcja 3"],
    "ANSWERS": ["Opcja 3",  "Opcja 2", "Opcja 1"]
  },
  {
    "id": 6,
    "question": "6.\nLikerta/radio matrix",
    "type": "likert",
    "options": [
      {
        "type": "radio",
        "question": "Instrukcja 1",
        "options": [["Opcja 1", "Opcja 2", "Opcja 3", "Opcja 4", "Opcja 5"]]
      },
      {
        "type": "radio",
        "question": "Instrukcja 2",
        "options": [["Opcja 1", "Opcja 2", "Opcja 3", "Opcja 4", "Opcja 5"]]
      }
    ],
    "ANSWERS": {
      "Instrukcja 1": "Opcja 4",
      "Instrukcja 2": "Opcja 3"
    }
  },
  {
    "id": 7,
    "question": "7.\nNet scorer",
    "type": "nps",
    "options": [],
    "ANSWERS": "8"
  }
]

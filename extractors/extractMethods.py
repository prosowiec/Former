from extractors import extractGoogle
from extractors import extractMS

GOOGLE_EXTRACTORS = {
    "multiple_choice": extractGoogle.extract_radio,
    "checkboxes": extractGoogle.extract_checkboxes,
    "dropdown": extractGoogle.extract_dropdown,
    "short_text": lambda q: extractGoogle.extract_text(q, "short_text"),
    "paragraph": lambda q: extractGoogle.extract_text(q, "paragraph"),
    "matrix_radio": extractGoogle.extract_matrix_radio,
    "matrix_checkbox": extractGoogle.extract_matrix_checkbox,
    "title": extractGoogle.extract_title,
}

MS_EXTRACTORS = {
    "text": extractMS.extract_text,
    "paragraph": extractMS.extract_paragraph,
    "radio": extractMS.extract_checkboxes,
    "checkboxes": extractMS.extract_multiple_choice,
    "dropdown": extractMS.extract_dropdown,
    "star_rating": extractMS.extract_star_rating,
    "linear_scale": extractMS.extract_linear_scale,
    "nps": extractMS.extract_nps,
    "date": extractMS.extract_date,
    "likert": extractMS.extract_likert,
    "hierarchical_ranking": extractMS.extract_ranking,
    "title": extractMS.extract_title,
}

ITEMS_EXTRACTORS = {
    "GOOGLE": extractGoogle.extract_question_items,
    "MS": extractMS.extract_question_items,
}
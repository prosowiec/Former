from fillers import fillGoogle
from fillers import fillMS

GOOGLE_FILLERS = {
    "short_text": fillGoogle.fill_short_text,
    "paragraph": fillGoogle.fill_paragraph,
    "linear_scale_radio": fillGoogle.fill_linear_scale_radio,
    "checkboxes": fillGoogle.fill_checkboxes,
    "dropdown": fillGoogle.fill_dropdown,
    "matrix_radio": fillGoogle.fill_matrix_radio,
    'multiple_choice': fillGoogle.fill_checkboxes,
    "date": fillGoogle.fill_date,
    "time": fillGoogle.fill_time,
    'matrix_checkbox': fillGoogle.fill_matrix_checkbox,
}

MS_FILLERS = {
    "text": fillMS.fill_text,
    "paragraph": fillMS.fill_paragraph,

    "radio": fillMS.fill_multiple_choice,
    "checkboxes": fillMS.fill_checkboxes,
    "dropdown": fillMS.fill_dropdown,

    "star_rating": fillMS.fill_star_rating,
    "linear_scale": fillMS.fill_linear_scale,
    "nps": fillMS.fill_nps,

    "date": fillMS.fill_date,
    "likert": fillMS.fill_likert,
    "hierarchical_ranking": fillMS.fill_ranking,
}


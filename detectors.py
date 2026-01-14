def detect_question_type(q):
    # Section title
    if q.query_selector("div[role='heading']") and not q.query_selector(
        "input, textarea, select, div[role='radio'], div[role='checkbox'], div[role='listbox']"
    ):
        return "section_title"

    # Date
    if q.query_selector("input[type='date']"):
        return "date"

    # Time
    if q.query_selector_all("input[maxlength='2']"):
        return "time"

    # 🔹 MATRIX RADIO (multiple choice grid)
    radiogroups = q.query_selector_all("div[role='radiogroup']")
    if len(radiogroups) > 1:
        return "matrix_radio"

    # 🔹 MATRIX CHECKBOX (checkbox grid)
    groups = q.query_selector_all("div[role='group']")
    if len(groups) > 1:
        for g in groups:
            if len(g.query_selector_all("div[role='checkbox']")) > 1:
                return "matrix_checkbox"

    # Dropdown
    if q.query_selector("div[role='listbox']"):
        return "dropdown"

    # Checkboxes (non-matrix)
    if q.query_selector("div[role='checkbox']"):
        return "checkboxes"

    # Paragraph
    if q.query_selector("textarea"):
        return "paragraph"

    # Short text
    if q.query_selector("input[type='text']"):
        return "short_text"

    # Multiple choice
    if q.query_selector("div[role='radiogroup']"):
        return "multiple_choice"

    return "unknown"

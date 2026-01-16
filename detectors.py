def detect_GOOGLE_question_type(q):
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
        return "multiple_choice"

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

def is_likert(q):
    return (
        q.query_selector("table") is not None and
        q.query_selector("input[type='radio']") is not None
    )
    
def is_ms_date_input(q):
    el = q.query_selector("input[role='combobox'][aria-haspopup='dialog']")
    if not el:
        return False

    placeholder = (el.get_attribute("placeholder") or "").lower()
    return "dd" in placeholder and "mm" in placeholder

def detect_MS_question_type(q):
    if q.query_selector("div[data-automation-id='npsContainer']"):
        return "nps"

    
    if is_likert(q):
        return "likert"

    # ---------- RANKING ----------
    # Ranking questions contain rank items with dropdowns per row
    if q.query_selector("div[data-automation-id='rankItem']"):
        return "ranking"

    # ---------- NPS (0–10 scale) ----------
    # NPS is a linear scale with exactly 11 radios (0–10)
    radios = q.query_selector_all("div[role='radio']")
    # ---------- LINEAR SCALE (non-NPS rating) ----------
    if radios and 2 <= len(radios) <= 10:
        return "linear_scale"

    # ---------- STAR RATING ----------
    if q.query_selector("div[role='radiogroup'] span[role='radio']"):
        return "star_rating"
    
    # data-automation-id="rankingItemContent"
    # ---------- MULTIPLE CHOICE (radio / checkbox) ----------
    if q.query_selector("div[data-automation-id='choiceItem']"):
        return "radio"
    
    if q.query_selector("div[data-automation-id='rankingItemContent']"):
        return "hierarchical_ranking"
    # ---------- DROPDOWN ----------
    if q.query_selector("select"):
        return "dropdown"

    # ---------- DATE ----------
    if is_ms_date_input(q):
        return "date"

    # ---------- SHORT TEXT ----------
    if q.query_selector("input[data-automation-id='textInput']"):
        return "text"

    # ---------- PARAGRAPH ----------
    if q.query_selector("textarea"):
        return "paragraph"

    return "unknown"
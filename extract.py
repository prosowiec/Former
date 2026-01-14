from extractors import extractGoogle

EXTRACTORS = {
    "multiple_choice": extractGoogle.extract_radio,
    "checkboxes": extractGoogle.extract_checkboxes,
    "dropdown": extractGoogle.extract_dropdown,
    "short_text": lambda q: extractGoogle.extract_text(q, "short_text"),
    "paragraph": lambda q: extractGoogle.extract_text(q, "paragraph"),
    "matrix_radio": extractGoogle.extract_matrix_radio,
    "matrix_checkbox": extractGoogle.extract_matrix_checkbox,
}

def remove_aria_hidden_children(q):
    """
    Removes all child elements with aria-hidden='true' from the element.
    Returns the cleaned element.
    """
    # Find all children with aria-hidden="true" and remove them
    hidden_elements = q.query_selector_all("[aria-hidden='true']")
    for elem in hidden_elements:
        elem.evaluate("el => el.remove()")
    
    return q

def extract_options(q, qtype):
    """
    Dispatch extractor based on detected question type
    Returns structured extraction dict or None
    """
    
    # Remove all aria-hidden children
    q = remove_aria_hidden_children(q)
    
    extractor = EXTRACTORS.get(qtype)
    if not extractor:
        return []
    
    return extractor(q)
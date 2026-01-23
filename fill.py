from fillers.fillMethods import GOOGLE_FILLERS, MS_FILLERS

def fill_question(page, q, platform, qtype, answer):
    if platform == "GOOGLE":
        filler = GOOGLE_FILLERS.get(qtype)
    elif platform == "MS":
        filler = MS_FILLERS.get(qtype)
    else:
        filler = None

    if filler:
        filler(q, page, answer['ANSWERS']) if qtype == "dropdown" else filler(q, answer['ANSWERS'])
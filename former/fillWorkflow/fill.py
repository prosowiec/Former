from former.fillWorkflow.fillers.fillGoogle import GOOGLE_FILLERS
from former.fillWorkflow.fillers.fillMS import MS_FILLERS

def fill_question(page, q, platform, qtype, answer):
    if platform == "GOOGLE":
        filler = GOOGLE_FILLERS.get(qtype)
    elif platform == "MS":
        filler = MS_FILLERS.get(qtype)
    else:
        filler = None

    if filler:
        #, "hierarchical_ranking"
        filler(q, page, answer['ANSWERS']) if qtype in ["dropdown", "hierarchical_ranking"] else filler(q, answer['ANSWERS'])
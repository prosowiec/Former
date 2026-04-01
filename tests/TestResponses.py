import random
from datetime import datetime, timedelta
from former.LLM_interface.ChatInterface import chatInterface

class testResponses(chatInterface):
    ANSWERS = [
        "Good experience overall",
        "It was fine",
        "No major issues",
        "Pretty straightforward",
        "Everything went smoothly",
        "Satisfied with the service",
    ]


    def get_selection(self, form_data: dict) -> dict:
        return [self.generate_answer(question) for question in form_data]

    def generate_answer(self, question):
        qtype = question["type"]
        options = question.get("options")

        answer = None

        if qtype in ["radio", "multiple_choice", "dropdown"]:
            if isinstance(options, dict):
                answer = random.choice(options.get("options", []))
            elif isinstance(options, list):
                answer = random.choice(options)

        elif qtype in ["checkbox", "multiple_checkbox"]:
            try:
                answer = random.sample(options, random.randint(1, len(options)))
            except:
                answer = random.choice(options.get("options", []))
                answer = [answer] if isinstance(answer, str) else answer
        elif qtype == "matrix_radio":
            answer = {}
            for row in options["options"]:
                cols = row["options"][0]
                answer[row["question"]] = random.choice(cols)

        elif qtype == "matrix_checkbox":
            answer = {}
            for row in options["options"]:
                cols = row["options"][0]
                k = random.randint(1, len(cols))
                answer[row["question"]] = random.sample(cols, k)

        elif qtype == "likert":
            answer = {}
            for row in options:
                cols = row["options"][0]
                answer[row["question"]] = random.choice(cols)

        elif qtype == "hierarchical_ranking":
            answer = options[:]
            random.shuffle(answer)

        elif qtype == "star_rating":
            answer = random.choice(options)

        elif qtype == "nps":
            answer = str(random.randint(0, 10))

        elif qtype in ["text", "paragraph"]:
            answer = random.choice(self.ANSWERS)

        elif qtype == "time":
            h = random.randint(0, 23)
            m = random.randint(0, 59)
            answer = f"{h:02d}:{m:02d}"

        elif qtype == "date":
            start = datetime(2023, 1, 1)
            end = datetime(2026, 12, 31)
            d = start + timedelta(days=random.randint(0, (end - start).days))
            answer = d.strftime("%Y-%m-%d")
            
        result = question.copy()
        result["ANSWERS"] = answer
        return result
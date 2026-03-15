from abc import ABC, abstractmethod
import json

class chatInterface(ABC):

    def get_promt(self, form_data: dict) -> str:
        prompt = f"""
            You are an automated form filler. Based on the following form structure,
            provide a realistic or logical answer.

            Form Data:
            {json.dumps(form_data, indent=2)}

            Return the answer ONLY as a JSON object.

            For EACH question object:
            - Preserve all original fields: id, question, type, options
            - ADD a new field called "ANSWERS"

            Rules:
            - "ANSWERS" must contain the selected option(s)
            - For single-choice questions, use a string
            - For multiple-choice or checkbox questions, use a list of strings
            - For matrix questions, use an object mapping row names to selected column(s)

            Example output format:
            {{
            "id": "qid",
            "question": "title",
            "type": "qtype",
            "options": "options",
            "ANSWERS": ["Selected Option 1", "Selected Option 2"]
            }}

            Do NOT include explanations, comments, or extra text.
            Return JSON ONLY.
            """
        return prompt

    @abstractmethod
    def get_selection(self, form_data: dict):
        pass

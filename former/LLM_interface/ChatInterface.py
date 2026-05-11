from abc import ABC, abstractmethod
import json

class chatInterface(ABC):
    
    def generate__personality(self, personal_info: dict) -> str:
        personality = f"""
        You are a person filling out a form. Here is some information about you:
        personal_info = {json.dumps(personal_info, indent=0)}
        Imagine that you are this person, add personal story, make sure that if I write the same promtt again, you will generate the same personality 
        with different details and you will give diffrent answers. Remember this information
        and use this information to answer the questions in a consistent way.
        """
        return personality

    def get_promt(self, form_data: dict, personal_info: dict = None) -> str:
        prompt = f"""
            You are an automated form filler. Based on the following form structure,
            provide a realistic or logical answer.

            Form Data:
            {json.dumps(form_data, indent=0)}

            Personal Information:
            {json.dumps(self.generate__personality(personal_info), indent=0)}

            Return the answer ONLY as a JSON object.

            For EACH question object:
            - Preserve all original fields: id, question, type, options
            - ADD a new field called "ANSWERS"

            Rules:
            - "ANSWERS" must contain the selected option(s)
            - For single-choice questions, use a string
            - For multiple-choice or checkbox questions, use a list of strings
            - For matrix questions, use an object mapping row names to selected column(s)
            
            YOU NEED TO ANSWER ALL QUESTIONS. If you don't know, make a reasonable guess. 
            MAKE SURE TO THAT NUMBER OF ASNWERS MATCHES THE NUMBER OF QUESTIONS.


            Example output format:
            [
            {{
                "id": 1,
                "question": "Question 1",
                "type": "multiple_choice",
                "options": ["A", "B"],
                "ANSWERS": "A"
            }},
            {{
                "id": 2,
                "question": "Question 2",
                "type": "paragraph",
                "options": [],
                "ANSWERS": "Some text"
            }}
            ]

            Do NOT include explanations, comments, or extra text.
            Return JSON ONLY.
            """
        return prompt

    @abstractmethod
    def get_selection(self, form_data: dict, personal_info: dict = None):
        pass

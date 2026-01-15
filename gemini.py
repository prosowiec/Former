import json
import google.generativeai as genai

class GeminiFormFiller:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
        """
        Initializes the Gemini API connection and model instance once.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        print(f"Gemini initialized with model: {model_name}")

    def get_selection(self, form_data: dict) -> dict:
        """
        Sends form structure to Gemini and returns selected answers as a dict.
        """
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
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean response text to extract only the JSON part
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"Error getting Gemini selection: {e}")
            return {}
        
    def selector_test(self, dummy):
        return [
    {
        "id": 1,
        "question": "Matrix checkbox",
        "type": "matrix_checkbox",
        "options": {
        "type": "matrix_checkbox",
        "questionTitle": "Matrix checkbox",
        "options": [
            {
            "type": "checkboxes",
            "question": "Wiersz 1",
            "options": [["Kolumna 1", "aadada", "dada"]]
            },
            {
            "type": "checkboxes",
            "question": "Wiersz 2",
            "options": [["Kolumna 1", "aadada", "dada"]]
            },
            {
            "type": "checkboxes",
            "question": "Wiersz 3",
            "options": [["Kolumna 1", "aadada", "dada"]]
            }
        ]
        },
        "ANSWERS": {
        "Wiersz 1": ["Kolumna 1", "dada"],
        "Wiersz 2": ["aadada"],
        "Wiersz 3": ["Kolumna 1"]
        }
    },
    {
        "id": 2,
        "question": "dawdawdasdxzc",
        "type": "time",
        "options": [],
        "ANSWERS": "10:00"
    },
    {
        "id": 3,
        "question": "Tetuje radio",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Tetuje radio",
        "options": ["Opcja 1", "aaa", "Opcja 3"]
        },
        "ANSWERS": "aaa"
    },
    {
        "id": 4,
        "question": "Dropdown",
        "type": "dropdown",
        "options": {
        "type": "dropdown",
        "question": "Dropdown",
        "options": ["Opcja 1", "ab", "b"]
        },
        "ANSWERS": "ab"
    },
    {
        "id": 5,
        "question": "Linear scale",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Linear scale",
        "options": ["1", "2", "3", "4", "5"]
        },
        "ANSWERS": "4"
    },
    {
        "id": 6,
        "question": "Grade",
        "type": "multiple_choice",
        "options": {
        "type": "linear_scale_radio",
        "question": "Grade",
        "options": ["1", "2", "3", "4", "5"]
        },
        "ANSWERS": "5"
    },
    {
        "id": 7,
        "question": "Matrix radio",
        "type": "matrix_radio",
        "options": {
        "type": "matrix_radio",
        "questionTitle": "Matrix radio",
        "options": [
            {
            "type": "radio",
            "question": "Wiersz 1",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "zzz",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "Wiersz 3",
            "options": [["Kolumna 1", "adad", "aad"]]
            },
            {
            "type": "radio",
            "question": "Wiersz 4",
            "options": [["Kolumna 1", "adad", "aad"]]
            }
        ]
        },
        "ANSWERS": {
        "Wiersz 1": "adad",
        "zzz": "Kolumna 1",
        "Wiersz 3": "aad",
        "Wiersz 4": "adad"
        }
    },
    {
        "id": 8,
        "question": "adawdadawdawda",
        "type": "date",
        "options": [],
        "ANSWERS": "2023-11-15"
    }
    ]

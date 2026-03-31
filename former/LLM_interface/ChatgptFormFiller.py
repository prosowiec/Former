import json
from openai import OpenAI

from former.LLM_interface.ChatInterface import chatInterface


class chatgptFormFiller(chatInterface):
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "form_answers",
            "schema": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "number"},
                                "question": {"type": "string"},
                                "type": {"type": "string"},
                                "options": {},
                                "ANSWERS": {}
                            },
                            "required": ["id", "question", "type", "options", "ANSWERS"]
                        }
                    }
                },
                "required": ["answers"]
            }
        }
    }        
    def __init__(self, api_key: str, model_name: str = "gpt-4.1-mini"):
        """
        Initializes the OpenAI API connection and model instance once.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model_name
        print(f"ChatGPT initialized with model: {model_name}")
        

    def get_selection(self, form_data: dict) -> dict:
        """
        Sends form structure to ChatGPT and returns selected answers as a dict.
        """
        prompt = self.get_promt(form_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format=self.response_format,  # Forces valid JSON
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an assistant that fills forms. "
                            "Return the answers as a JSON ARRAY of objects (one per question)."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            text = response.choices[0].message.content
            print("Raw ChatGPT response:", text)
            return json.loads(text)['answers']
        except Exception as e:
            print(f"Error getting ChatGPT selection: {e}")
            raise Exception(f"ChatGPT API error: {e}")
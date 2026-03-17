import json
import google.generativeai as genai

from former.LLM_interface.ChatInterface import chatInterface

class geminiFormFiller(chatInterface):
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
        prompt = self.get_promt(self, form_data)
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
        
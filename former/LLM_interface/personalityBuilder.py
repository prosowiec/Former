import random
import pandas as pd
from typing import Dict, Any



class PersonalityBuilder:

    def __init__(self, axes_config: str = "former/LLM_interface/PERSONAS.json"):
        self.axes_config = pd.read_json(axes_config).to_dict(orient="records")

    def _find_step(self, axis_id: str, value: str):

        axis = next(
            (
                axis for axis in self.axes_config
                if axis["id"] == axis_id
            ),
            None
        )

        if not axis:
            return None

        return next(
            (
                step for step in axis["steps"]
                if step["value"] == value
            ),
            None
        )

    def build_personality(self, airflow_request) -> Dict[str, Any]:

        personality = {
            "selected_personality": {},
            "traits": [],
            "micro_variations": {}
        }

        axis_fields = ["age_profile", "political_leaning", "risk_tolerance", "verbosity", "formality"]

        for field in axis_fields:

            selected_value = getattr(airflow_request, field, None)

            if not selected_value:
                continue

            step = self._find_step(field, selected_value)

            if not step:
                continue

            personality["selected_personality"][field] = step["label"]


            num_traits = random.randint(2, 3)

            selected_traits = random.sample(
                step["traits"],
                min(num_traits, len(step["traits"]))
            )

            personality["traits"].extend(
                selected_traits
            )

        hobbies = ["reading", "fitness", "gaming", "photography", "traveling", "cycling", "music", "cooking"]

        communication_habits = [
            "Uses practical examples",
            "Prefers concise explanations",
            "Writes in a structured way",
            "Occasionally adds personal anecdotes",
            "Likes clear step-by-step answers"
        ]

        personality["micro_variations"] = {
            "hobby": random.choice(hobbies),
            "communication_style": random.choice(
                communication_habits
            ),
            "small_backstory": (
                f"Recently became more interested in "
                f"{random.choice(hobbies)}."
            )
        }

        return personality

        

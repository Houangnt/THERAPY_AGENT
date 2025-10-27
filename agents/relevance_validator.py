from strands.models import BedrockModel
from utils.prompts import PromptTemplates
from strands import Agent

class RelevanceValidationAgent(Agent):
    def __init__(self, model=None):
        if model is None:
            model = BedrockModel(
                model_id="mistral.mistral-large-2402-v1:0",
                region_name="ap-southeast-2",
                streaming=False,
            )
        
        super().__init__(
            system_prompt=PromptTemplates.relevance_check_prompt(),
            model=model
        )

    def execute(self, user_input: str) -> str:
        """
        Checks if the user input is relevant to a therapy session.
        Returns "RELEVANT" or a deflection message.
        """
        response = str(self(user_input))
        print("[DEBUG] RELEVANT RELEVANT")

        if "RELEVANT" in response:
            return "RELEVANT"
        else:
            return response.strip()

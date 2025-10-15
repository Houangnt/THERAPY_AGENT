from typing import Optional
from agents.base import BaseAgent
from utils.prompts import PromptTemplates
from strands.models import BedrockModel

class CrisisHandlerAgent(BaseAgent):
    """
    An agent specialized in detecting and handling crisis situations in user messages.
    Detects SUICIDAL IDEATION, SELF-HARM, SEXUAL ASSAULT, SUBSTANCE ABUSE, DOMESTIC VIOLENCE, etc.
    """

    def __init__(self):
        bedrock_model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        super().__init__(system_prompt=PromptTemplates.crisis_handler_prompt(), model=bedrock_model)

    def execute(self, message: str) -> Optional[str]:
        """
        Analyzes the user message for crisis content.

        Args:
            message (str): The user's message to analyze.

        Returns:
            str: "CRISIS_DETECTED\n<response>" if a crisis is found,
                 "NO_CRISIS" if not detected,
                 or None if model fails.
        """
        response = self._safe_execute(query=message)

        if not response:
            return None
        
        normalized = response.strip().lower()
        if any(keyword in normalized for keyword in [
            "suicidal", "self-harm", "kill myself", "end my life",
            "abuse", "assault", "violence", "rape", "overdose"
        ]) or normalized.startswith("crisis_detected"):
            if not response.startswith("CRISIS_DETECTED"):
                response = f"CRISIS_DETECTED\n{response}"
            return response
        
        return "NO_CRISIS"

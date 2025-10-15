from typing import Optional
from agents.base import BaseAgent
from utils.prompts import CRISIS_HANDLER_PROMPT
from strands.models import BedrockModel

class CrisisHandlerAgent(BaseAgent):
    """
    An agent specialized in detecting and handling crisis situations in user messages.
    """

    def __init__(self):
        bedrock_model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        super().__init__(system_prompt=CRISIS_HANDLER_PROMPT, model=bedrock_model)

    def execute(self, message: str) -> Optional[str]:
        """
        Analyzes the user message for crisis content.

        Args:
            message: The user's message to analyze.

        Returns:
            The crisis response if a crisis is detected, otherwise "NO_CRISIS".
        """
        response = self._safe_execute(query=message)
        return response

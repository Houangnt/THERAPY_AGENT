from abc import ABC, abstractmethod
from typing import Optional, List, Any
from strands import Agent
from strands.models import Model, BedrockModel


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        system_prompt: str,
        tools: Optional[List[Any]] = None,
        model: Optional[Model] = None
    ):
        """
        Initialize base agent.
        
        Args:
            system_prompt: System prompt for the agent.
            tools: Optional list of tools for the agent.
            model: Optional model instance (defaults to Bedrock Mistral).
        """
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model or BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        self.agent = Agent(
            system_prompt=self.system_prompt,
            tools=self.tools,
            model=self.model
        )
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Optional[str]:
        """Execute the agent's primary function."""
        pass
    
    def _safe_execute(self, query: str = "") -> str:
        """Safely execute agent with error handling."""
        try:
            response = self.agent(str(query))
            return str(response)
        except Exception as e:
            return f"Error in {self.__class__.__name__}: {e}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(model={self.model}, tools={len(self.tools)})>"
from abc import ABC, abstractmethod
from typing import Optional
from strands import Agent


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, system_prompt: str, tools: Optional[list] = None):
        """
        Initialize base agent.
        
        Args:
            system_prompt: System prompt for the agent
            tools: Optional list of tools for the agent
        """
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.agent = Agent(
            system_prompt=self.system_prompt,
            tools=self.tools
        )
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """Execute the agent's primary function."""
        pass
    
    def _safe_execute(self, query: str = "") -> str:
        """Safely execute agent with error handling."""
        try:
            response = self.agent(query)
            return str(response)
        except Exception as e:
            return f"Error in {self.__class__.__name__}: {str(e)}"
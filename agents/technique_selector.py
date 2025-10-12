from typing import List
from strands import Agent
from ..config import Config
from ..utils.prompts import PromptTemplates
from .base import BaseAgent


class TechniqueSelectorAgent(BaseAgent):
    """Agent responsible for selecting appropriate therapeutic techniques."""
    
    def __init__(self):
        """Initialize the technique selector agent."""
        self.config = Config()
        super().__init__(
            system_prompt="You are a CBT therapist selecting appropriate techniques.",
            tools=[]
        )
    
    def select_techniques(self, cbt_plan: str, history: str) -> List[str]:
        """
        Dynamically select appropriate therapeutic techniques for current turn.
        
        Args:
            cbt_plan: The CBT counseling plan
            history: Current dialogue history
            
        Returns:
            List of selected technique names
        """
        techniques_str = "\n".join(f"- {t}" for t in self.config.THERAPY_AGENTS)
        
        prompt = PromptTemplates.technique_selection_prompt(
            cbt_plan,
            history,
            techniques_str
        )
        
        # Create agent with Bedrock config
        agent = Agent(system_prompt=prompt, tools=[], model=self.model)
        response = str(agent(""))
        
        # Parse response to extract technique names
        techniques = [t.strip() for t in response.split(',')]
        
        # Validate and filter techniques
        valid_techniques = [
            t for t in techniques 
            if any(vt.lower() in t.lower() for vt in self.config.THERAPY_AGENTS)
        ]
        
        return valid_techniques if valid_techniques else ["Reflection"]
    
    def execute(self, cbt_plan: str, history: str) -> List[str]:
        """
        Execute the technique selection task.
        
        Args:
            cbt_plan: The CBT counseling plan
            history: Current dialogue history
            
        Returns:
            List of selected technique names
        """
        return self.select_techniques(cbt_plan, history)
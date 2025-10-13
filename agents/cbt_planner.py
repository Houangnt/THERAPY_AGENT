from strands import Agent
from ..config import Config
from ..utils.prompts import PromptTemplates
from .base import BaseAgent


class CBTPlannerAgent(BaseAgent):
    """Agent responsible for creating CBT-based counseling plans."""
    
    def __init__(self):
        """Initialize the CBT planner agent."""
        self.config = Config()
        super().__init__(
            system_prompt="You are a CBT therapist creating treatment plans.",
            tools=[]
        )
    
    def create_plan(self, client_info: str, reason: str, 
                   initial_dialogue: str) -> str:

        techniques_str = "\n".join(f"- {t}" for t in self.config.CBT_TECHNIQUES)
        
        prompt = PromptTemplates.cbt_planning_prompt(
            techniques_str,
            client_info,
            reason,
            initial_dialogue
        )
        
        agent = Agent(system_prompt=prompt, tools=[], model=self.model)
        return str(agent("Choose an appropriate CBT technique and create a comprehensive counseling plan that outlines behavioral goals and cognitive reframing strategies."))
    
    def execute(self, client_info: str, reason: str, initial_dialogue: str) -> str:
        """
        Execute the CBT planning task.
        
        Args:
            client_info: Client information
            reason: Reason for counseling
            initial_dialogue: Initial dialogue
            
        Returns:
            CBT treatment plan
        """
        return self.create_plan(client_info, reason, initial_dialogue)
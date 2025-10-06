from strands import Agent
from ..config import Config
from ..utils.prompts import PromptTemplates


class CBTPlannerAgent:
    """Agent responsible for creating CBT-based counseling plans."""
    
    def __init__(self):
        """Initialize the CBT planner agent."""
        self.config = Config()
    
    def create_plan(self, client_info: str, reason: str, 
                   initial_dialogue: str) -> str:

        techniques_str = "\n".join(f"- {t}" for t in self.config.CBT_TECHNIQUES)
        
        prompt = PromptTemplates.cbt_planning_prompt(
            techniques_str,
            client_info,
            reason,
            initial_dialogue
        )
        
        agent = Agent(system_prompt=prompt, tools=[])
        return str(agent(""))
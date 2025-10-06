from typing import Dict, Optional
from strands import Agent
from ..models.client import ClientProfile
from ..models.session import CounselingSession
from ..config import Config
from ..utils.prompts import PromptTemplates
from ..utils.validators import validate_client_profile, validate_message
from .cbt_planner import CBTPlannerAgent
from .technique_selector import TechniqueSelectorAgent
from .specialized import (
    reflection_agent,
    questioning_agent,
    solution_agent,
    normalizing_agent,
    psychoeducation_agent
)


class CBTCounselingSystem:
    """
    Main orchestrator for the CBT multi-agent counseling system.
    """
    
    def __init__(self, client_profile: ClientProfile):
        """
        Initialize the CBT counseling system.
        
        Args:
            client_profile: Client information and intake data
        """
        # Validate client profile
        is_valid, error = validate_client_profile(client_profile)
        if not is_valid:
            raise ValueError(f"Invalid client profile: {error}")
        
        self.client_profile = client_profile
        self.session = CounselingSession()
        self.config = Config()
        
        # Initialize sub-agents
        self.cbt_planner = CBTPlannerAgent()
        self.technique_selector = TechniqueSelectorAgent()
        
        # Create response synthesis orchestrator
        self.orchestrator = Agent(
            system_prompt="""You are a counselor synthesizing responses from 
            specialized therapeutic agents. Generate empathetic, natural counselor responses 
            that build trust with the client. Combine the suggested responses based on 
            selected techniques into a single coherent utterance.""",
            tools=[
                reflection_agent,
                questioning_agent,
                solution_agent,
                normalizing_agent,
                psychoeducation_agent
            ]
        )
    
    def initialize_session(self, initial_client_message: str) -> str:
        """
        Initialize counseling session with CBT plan.
        
        Args:
            initial_client_message: Client's first message
            
        Returns:
            Initial counselor response
        """
        is_valid, error = validate_message(initial_client_message)
        if not is_valid:
            raise ValueError(f"Invalid message: {error}")
        
        # Create CBT plan
        self.session.cbt_plan = self.cbt_planner.create_plan(
            self.client_profile.to_string(),
            self.client_profile.reason_for_counseling,
            initial_client_message
        )
        
        # Add to history
        self.session.add_message("Client", initial_client_message)
        
        # Generate initial response
        return self._process_turn()
    
    def process_turn(self, client_message: str) -> str:
        """
        Process a single counseling turn.
        
        Args:
            client_message: Current client message
            
        Returns:
            Counselor response
        """
        is_valid, error = validate_message(client_message)
        if not is_valid:
            raise ValueError(f"Invalid message: {error}")
        
        self.session.add_message("Client", client_message)
        return self._process_turn()
    
    def _process_turn(self) -> str:
        """Internal method to process a counseling turn."""
        history_str = self.session.get_history_string(
            max_messages=self.config.MAX_HISTORY_LENGTH
        )
        
        # Select appropriate techniques
        techniques = self.technique_selector.select_techniques(
            self.session.cbt_plan,
            history_str
        )
        self.session.selected_techniques = techniques
        
        # Generate candidate responses from all specialized agents
        candidates = self._generate_candidate_responses(history_str)
        
        # Synthesize final response
        synthesis_prompt = PromptTemplates.synthesis_prompt(candidates, techniques)
        final_response = str(self.orchestrator(synthesis_prompt))
        
        # Add to history
        self.session.add_message("Counselor", final_response)
        
        return final_response
    
    def _generate_candidate_responses(self, history: str) -> Dict[str, str]:
        """Generate candidate responses from all specialized agents."""
        client_info = self.client_profile.to_string()
        reason = self.client_profile.reason_for_counseling
        
        return {
            'reflection': reflection_agent(client_info, reason, history),
            'questioning': questioning_agent(client_info, reason, history),
            'solution': solution_agent(client_info, reason, history),
            'normalizing': normalizing_agent(client_info, reason, history),
            'psychoeducation': psychoeducation_agent(client_info, reason, history)
        }
    
    def get_session_summary(self) -> Dict:
        """Get a summary of the current session."""
        return {
            'total_turns': len(self.session.messages) // 2,
            'cbt_plan': self.session.cbt_plan,
            'recent_techniques': self.session.selected_techniques,
            'message_count': len(self.session.messages)
        }
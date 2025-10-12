from typing import Dict, Optional
from strands import Agent
from ..config import Config
from ..utils.prompts import PromptTemplates
from ..models.client import ClientProfile
from ..models.session import CounselingSession
from .base import BaseAgent


class InitialAgent(BaseAgent):
    """Agent responsible for initial CBT session task: Setting Agenda."""
    
    def __init__(self):
        """Initialize the initial agent."""
        self.config = Config()
        super().__init__(
            system_prompt="You are a CBT therapist setting agendas for counseling sessions.",
            tools=[]
        )
    
    def set_agenda(self, client_profile: ClientProfile, initial_message: str) -> Dict[str, str]:
        """
        Set the agenda for the CBT session.
        
        Args:
            client_profile: Client information and intake data
            initial_message: Client's initial message
            
        Returns:
            Dictionary containing agenda items and session focus
        """
        client_info = client_profile.to_string()
        goal = client_profile.goal or "Not specified"
        client_schedule_technical = client_profile.client_schedule_technical or "No specific constraints"
        diagnosis = client_profile.diagnosis
        
        prompt = PromptTemplates.agenda_setting_prompt(
            client_info,
            goal,
            client_schedule_technical,
            diagnosis,
            initial_message
        )
        
        agent = Agent(system_prompt=prompt, tools=[], model=self.model)
        agenda_response = str(agent(""))
        
        # Parse agenda response to extract structured information
        agenda_data = self._parse_agenda_response(agenda_response)
        
        return agenda_data
    
    def conduct_initial_session(self, client_profile: ClientProfile, 
                              initial_message: str) -> Dict[str, str]:
        """
        Conduct the initial session task (agenda setting).
        
        Args:
            client_profile: Client information from backend
            initial_message: Client's initial message
            
        Returns:
            Agenda information for CBT planner
        """
        # Set agenda based on backend information
        agenda_data = self.set_agenda(client_profile, initial_message)
        
        # Create session data with agenda information
        session_data = {
            'agenda_items': agenda_data.get('agenda_items', []),
            'session_focus': agenda_data.get('session_focus', ''),
            'goals': agenda_data.get('goals', []),
            'priorities': agenda_data.get('priorities', []),
            'agenda_summary': agenda_data.get('agenda_summary', ''),
            'combined_context': self._create_agenda_context(agenda_data, client_profile)
        }
        
        return session_data
    
    def _create_agenda_context(self, agenda_data: Dict[str, str], 
                              client_profile: ClientProfile) -> str:
        """Create agenda context for CBT planner."""
        context_parts = []
        
        # Add agenda information
        if agenda_data.get('session_focus'):
            context_parts.append(f"Session Focus: {agenda_data['session_focus']}")
        
        if agenda_data.get('agenda_items'):
            context_parts.append(f"Agenda Items: {', '.join(agenda_data['agenda_items'])}")
        
        if agenda_data.get('goals'):
            context_parts.append(f"Session Goals: {', '.join(agenda_data['goals'])}")
        
        if agenda_data.get('priorities'):
            context_parts.append(f"Priorities: {', '.join(agenda_data['priorities'])}")
        
        # Add client context
        context_parts.append(f"Client Goal: {client_profile.goal or 'Not specified'}")
        context_parts.append(f"Diagnosis: {client_profile.diagnosis}")
        
        return " | ".join(context_parts)
    
    def execute(self, client_profile: ClientProfile, initial_message: str) -> Dict[str, str]:
        """
        Execute the initial session task (agenda setting).
        
        Args:
            client_profile: Client information from backend
            initial_message: Client's initial message
            
        Returns:
            Agenda information for CBT planner
        """
        return self.conduct_initial_session(client_profile, initial_message)
    
    def _parse_agenda_response(self, response: str) -> Dict[str, str]:
        """Parse the agenda setting response into structured data."""
        agenda_data = {
            'agenda_items': [],
            'session_focus': '',
            'goals': [],
            'priorities': []
        }
        
        lines = response.split('\n')
        for line in lines:
            if 'agenda' in line.lower() or 'focus' in line.lower():
                agenda_data['session_focus'] = line.strip()
            elif line.strip().startswith('-') or line.strip().startswith('•'):
                agenda_data['agenda_items'].append(line.strip())
        
        return agenda_data
    
    def _create_combined_context(self, agenda_data: Dict[str, str]) -> str:
        """Create combined context for the CBT planner."""
        context_parts = []
        
        # Add agenda information
        if agenda_data.get('session_focus'):
            context_parts.append(f"Session Focus: {agenda_data['session_focus']}")
        
        if agenda_data.get('agenda_items'):
            context_parts.append(f"Agenda Items: {', '.join(agenda_data['agenda_items'])}")
        
        if agenda_data.get('goals'):
            context_parts.append(f"Session Goals: {', '.join(agenda_data['goals'])}")
        
        if agenda_data.get('priorities'):
            context_parts.append(f"Priorities: {', '.join(agenda_data['priorities'])}")
        
        return " | ".join(context_parts)

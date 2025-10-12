from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientProfile:

    """Client information and intake data."""

    age: int
    gender: str
    history: str
    mood: str
    diagnosis: str
    reason_for_counseling: str
    goal: Optional[str] = None
    client_schedule_technical: Optional[str] = None
    additional_notes: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert client profile to formatted string for prompts."""
        profile = f"""
        Age: {self.age}
        Gender: {self.gender}
        History: {self.history}
        Mood: {self.mood}
        Diagnosis: {self.diagnosis}
        """.strip()
        
        if self.additional_notes:
            profile += f"\nAdditional Notes: {self.additional_notes}"
        
        return profile
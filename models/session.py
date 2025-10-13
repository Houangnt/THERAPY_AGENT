from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Message:
    """Represents a single message in the conversation."""
    speaker: str  # "Client" or "Counselor"
    content: str
    
    def __str__(self) -> str:
        return f"{self.speaker}: {self.content}"


@dataclass
class CounselingSession:
    """Manages the state of a counseling session."""
    
    cbt_plan: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    selected_techniques: List[str] = field(default_factory=list)
    agenda_items: List[str] = field(default_factory=list)
    session_focus: Optional[str] = None
    initial_session_data: Optional[Dict[str, str]] = None
    
    def add_message(self, speaker: str, content: str) -> None:
        """Add a message to the session history."""
        self.messages.append(Message(speaker, content))
    
    def get_history_string(self, max_messages: Optional[int] = None) -> str:
        """Get conversation history as formatted string."""
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]
        return "\n".join(str(msg) for msg in messages)
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """Retrieve last N messages from history."""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CounselingSession':
        """Create a session from a dictionary."""
        # Manually deserialize Message objects
        messages_data = data.get("messages", [])
        data["messages"] = [Message(**msg) for msg in messages_data]
        return cls(**data)
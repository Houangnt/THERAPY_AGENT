from typing import Optional
from ..models.client import ClientProfile


def validate_client_profile(profile: ClientProfile) -> tuple[bool, Optional[str]]:
    """
    Validate client profile data.
    """
    if not profile.age or profile.age < 0 or profile.age > 120:
        return False, "Invalid age"
    
    if not profile.gender or not profile.gender.strip():
        return False, "Gender is required"
    
    if not profile.mood or not profile.mood.strip():
        return False, "Mood is required"

    if not profile.diagnosis or not profile.diagnosis.strip():
        return False, "Diagnosis is required"
        
    if not profile.reason_for_counseling or not profile.reason_for_counseling.strip():
        return False, "Reason for counseling is required"
    
    return True, None


def validate_message(message: str) -> tuple[bool, Optional[str]]:
    """
    Validate a client message.
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"
    
    if len(message) > 3000:
        return False, "Message too long (max 3000 characters)"
    
    return True, None
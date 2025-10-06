from typing import List

class Config:    
    # CBT Techniques
    CBT_TECHNIQUES: List[str] = [
        "Cognitive Interventions",
        "Behavioural Interventions",
        "Emotion Regulation & Mindfulness",
        "Relapse Prevention",
        "Session Preparation and Reflection",
        "Distress Tolerance & Coping Skills",
        "CBT Foundations and Psychoeducation",
        "Values and Motivation Work"
    ]
    
    # Therapeutic agents
    THERAPY_AGENTS: List[str] = [
        "Reflection",
        "Questioning",
        "Providing solutions",
        "Normalization",
        "Psycho-education"
    ]
    
    # Model Configuration
    DEFAULT_MODEL = "mistral.mistral-large-2402-v1:0"
    MAX_HISTORY_LENGTH = 10  # Maximum conversation turns to keep
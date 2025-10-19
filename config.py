from typing import List, Set

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
    # CBT Sub-techniques
    CBT_SUB_TECHNIQUES: List[str] = [
        "Mindfulness Technique 1: The STOP Practice",
        "Mindfulness Technique 2: Five Senses Check-in",
        "Mindfulness Technique 3: Mindful Breathing",
        "Mindfulness Technique 4: Urge Surfing",
        "Mindfulness Technique 5: Defusion Techniques"
    ]
    CRITERIONS: Set[str] = {
        "Response richness",
        "Message reciprocity",
        "Time spent",
        "Opt-in behaviour",
        "Insight statement",
        "Self-reflection",
        "Curiosity or experimentation",
        "Emotional expression",
        "Containment",
        "Affective shift",
        "Clarity gained",
        "Values connection",
        "Therapeutic momentum",
        "Action step identified",
        "Follow-through",
        "Increased agency",
        "Warmth or rapport",
        "Collaboration",
        "Focused attention",
        "Perceived usefulness",
        "Willingness to return"
    }

    FLAGS: List[str] = [
        "Direct Suicidal Statement",
        "Indirect Suicidal Expression",
        "Hopeless/Pointless Statements",
        "Planning/Method Discussion",
        "Saying Goodbye/Finality"
    ]
    # Model Configuration
    DEFAULT_MODEL = "mistral.mistral-large-2402-v1:0"
    MAX_HISTORY_LENGTH = 10  # Maximum conversation turns to keep
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
        "Mindfulness Technique 2: Five Senses Check-in",
        "Mindfulness Technique 3: Mindful Breathing",
        "Mindfulness Technique 4: Urge Surfing",
    ]
    # CRITERIONS: Set[str] = {
    #     "Response richness",
    #     "Message reciprocity",
    #     "Time spent",
    #     "Opt-in behaviour",
    #     "Insight statement",
    #     "Self-reflection",
    #     "Curiosity or experimentation",
    #     "Emotional expression",
    #     "Containment",
    #     "Affective shift",
    #     "Clarity gained",
    #     "Values connection",
    #     "Therapeutic momentum",
    #     "Action step identified",
    #     "Follow-through",
    #     "Increased agency",
    #     "Warmth or rapport",
    #     "Collaboration",
    #     "Focused attention",
    #     "Perceived usefulness",
    #     "Willingness to return"
    # }
    CRITERIONS: Set[str] = {
        # 1) ENGAGEMENT QUALITY
        "response_richness",
        "message_reciprocity",
        "time_spent",
        "opt_in_behaviour",

        # 2) COGNITIVE / REFLECTIVE ACTIVITY
        "insight_statement",
        "self_reflection",
        "curiosity_experimentation",

        # 3) EMOTIONAL ACTIVATION & CONTAINMENT
        "emotional_expression",
        "containment",
        "affective_shift",

        # 4) GOAL & DIRECTION ALIGNMENT
        "clarity_gained",
        "values_connection",
        "therapeutic_momentum",

        # 5) MOTIVATION & BEHAVIOUR ACTIVATION
        "action_step_identified",
        "follow_through",
        "increased_agency",

        # 6) RELATIONAL / THERAPEUTIC ALLIANCE
        "warmth_or_rapport",
        "collaboration",
        "focused_attention",

        # 7) META-ENGAGEMENT
        "perceived_usefulness",
        "willingness_to_return",
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
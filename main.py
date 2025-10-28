<<<<<<< HEAD
from . import CBTCounselingSystem, ClientProfile


def main():
    """Example usage of the CBT counseling system."""
    
    # Create client profile
    client = ClientProfile(
        age=28,
        gender="Female",
        mood="Sad",
        diagnosis="Generalized Anxiety Disorder (GAD)",
        history="Experiencing workplace stress and anxiety about performance reviews",
        reason_for_counseling="Managing work-related anxiety and perfectionism",
        goal="Reduce anxiety and improve work performance",
        client_schedule_technical="Available for 50-minute sessions, prefers morning appointments",
        additional_notes="Reports difficulty sleeping and concentration issues"
    )
    
    # Initialize system
    print("Initializing CBT Counseling System...")
    initial_message = ("I've been feeling really overwhelmed at work lately. "
                      "I can't stop worrying about making mistakes.")
    counseling_system = CBTCounselingSystem(client, initial_message)
    
    # Start session
    print(f"\nCLIENT: {initial_message}")
    print(f"\nCOUNSELOR: {counseling_system.initial_response}")
    
    # Continue conversation
    next_message = "Yes, I keep thinking my boss will fire me if I'm not perfect."
    print(f"\n\nCLIENT: {next_message}")
    response = counseling_system.process_turn(next_message)
    print(f"\nCOUNSELOR: {response}")
    
    # Get session summary
    summary = counseling_system.get_session_summary()
    print(f"\n\n=== Session Summary ===")
    print(f"Total turns: {summary['total_turns']}")
    print(f"Recent techniques: {', '.join(summary['recent_techniques'])}")
    print(f"Session focus: {summary['session_focus']}")
    print(f"Agenda items: {', '.join(summary['agenda_items'])}")
    print(f"Goals: {', '.join(summary['goals'])}")
    print(f"Priorities: {', '.join(summary['priorities'])}")
    if summary['agenda_summary']:
        print(f"Agenda Summary: {summary['agenda_summary'][:200]}...")


if __name__ == "__main__":
    main()
=======
from . import CBTCounselingSystem, ClientProfile


def main():
    """Example usage of the CBT counseling system."""
    
    # Create client profile
    client = ClientProfile(
        age=28,
        gender="Female",
        mood="Sad",
        diagnosis="Generalized Anxiety Disorder (GAD)",
        history="Experiencing workplace stress and anxiety about performance reviews",
        reason_for_counseling="Managing work-related anxiety and perfectionism",
        additional_notes="Reports difficulty sleeping and concentration issues"
    )
    
    # Initialize system
    print("Initializing CBT Counseling System...")
    counseling_system = CBTCounselingSystem(client)
    
    # Start session
    initial_message = ("I've been feeling really overwhelmed at work lately. "
                      "I can't stop worrying about making mistakes.")
    
    print(f"\nCLIENT: {initial_message}")
    response = counseling_system.initialize_session(initial_message)
    print(f"\nCOUNSELOR: {response}")
    
    # Continue conversation
    next_message = "Yes, I keep thinking my boss will fire me if I'm not perfect."
    print(f"\n\nCLIENT: {next_message}")
    response = counseling_system.process_turn(next_message)
    print(f"\nCOUNSELOR: {response}")
    
    # Get session summary
    summary = counseling_system.get_session_summary()
    print(f"\n\n=== Session Summary ===")
    print(f"Total turns: {summary['total_turns']}")
    print(f"Recent techniques: {', '.join(summary['recent_techniques'])}")


if __name__ == "__main__":

    main()
>>>>>>> 05fe397810f435c0a60e7e60574017f6732ac71b

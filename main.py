from CBT import CBTCounselingSystem, ClientProfile


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
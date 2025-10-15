

import json
from lambda_function import start_session_handler, process_turn_handler


def main():
    """Example usage of the CBT counseling system with Lambda handlers."""
    
    client_profile = {
        "age": 28,
        "gender": "Female",
        "mood": "Sad",
        "diagnosis": "Generalized Anxiety Disorder (GAD)",
        "history": "Experiencing workplace stress and anxiety about performance reviews",
        "reason_for_counseling": "Managing work-related anxiety and perfectionism",
        "goal": "Reduce anxiety and improve work performance",
        "client_schedule_technical": "Available for 50-minute sessions, prefers morning appointments",
        "additional_notes": "Reports difficulty sleeping and concentration issues"
    }
    
    initial_client_message = ("I've been feeling really overwhelmed at work lately. "
                              "I can't stop worrying about making mistakes.")

    print("--- Starting Session ---")
    # 3. Turn 1
    print("\n" + "=" * 80)
    print("TURN 1")
    print("=" * 80)
    start_event = {
        "body": json.dumps({
            "client_profile": client_profile,
            "initial_client_message": initial_client_message
        })
    }
    
    start_response = start_session_handler(start_event, None)
    start_body = json.loads(start_response["body"])
    
    initial_response = start_body["initial_response"]
    session_state = start_body["session_state"]
    
    print(f"\nCLIENT: {initial_client_message}")
    print(f"\nCOUNSELOR: {initial_response}")

    
    print("\n--- Continuing Conversation ---")
    print("\n" + "=" * 80)
    print("TURN 1")
    print("=" * 80)
    message_1 = "Yes, I keep thinking my boss will fire me if I'm not perfect."
    
    turn_event_1 = {
        "body": json.dumps({
            "session_state": session_state,
            "client_message": message_1,
            "client_profile": client_profile
        })
    }
    
    turn_response_1 = process_turn_handler(turn_event_1, None)
    turn_body_1 = json.loads(turn_response_1["body"])
    
    response_1 = turn_body_1["response"]
    session_state = turn_body_1["session_state"]
    
    print(f"\n[CLIENT]: {message_1}")
    print(f"\n[COUNSELOR]: {response_1}")
    
    # 4. Turn 2
    print("\n" + "=" * 80)
    print("TURN 2")
    print("=" * 80)
    
    message_2 = "I want kill my self."
    
    turn_event_2 = {
        "body": json.dumps({
            "session_state": session_state,
            "client_message": message_2,
            "client_profile": client_profile
        })
    }
    
    turn_response_2 = process_turn_handler(turn_event_2, None)
    turn_body_2 = json.loads(turn_response_2["body"])
    
    response_2 = turn_body_2["response"]
    session_state = turn_body_2["session_state"] 
    
    print(f"\n[CLIENT]: {message_2}")
    print(f"\n[COUNSELOR]: {response_2}")
    
    print("\n" + "=" * 80)
    print("TURN 3")
    print("=" * 80)
    
    message_3 = "I often feel stressed whenever I face a difficult task."
    
    turn_event_3 = {
        "body": json.dumps({
            "session_state": session_state, 
            "client_message": message_3,
            "client_profile": client_profile
        })
    }
    
    turn_response_3 = process_turn_handler(turn_event_3, None)
    turn_body_3 = json.loads(turn_response_3["body"])
    
    response_3 = turn_body_3["response"]
    session_state = turn_body_3["session_state"]
    
    print(f"\n[CLIENT]: {message_3}")
    print(f"\n[COUNSELOR]: {response_3}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SESSION SUMMARY")
    print("=" * 80)
    print(f"Total turns: 3")
    print(f"Session can continue with the latest session_state")
    print("=" * 80)


if __name__ == "__main__":
    main()


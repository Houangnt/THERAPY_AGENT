import json
from lambda_function import start_session_handler, process_turn_handler, session_summary_handler


def print_turn(turn_num, client_msg, handler_func, body_key, session_state, client_profile):
    print("\n" + "=" * 80)
    print(f"TURN {turn_num}")
    print("=" * 80)
    
    event = {
        "body": json.dumps({
            "session_state": session_state,
            "client_message": client_msg,
            "client_profile": client_profile
        })
    }
    
    response = handler_func(event, None)
    body = json.loads(response["body"])
    
    # Tự động nhận đúng key (initial_response hoặc response)
    counselor_response = body.get("response") or body.get("initial_response")
    crisis_detected = body.get("crisis_detected", False)
    session_state = body["session_state"]
    
    print(f"\n[CLIENT]: {client_msg}")
    if crisis_detected:
        print(f"[COUNSELOR - CRISIS HANDLER]: {counselor_response}")
    else:
        print(f"[COUNSELOR]: {counselor_response}")
    
    return session_state


def main():
    """Run CBT counseling system locally (simulate Lambda flow)."""

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

    initial_client_message = ("I can't stop worrying about making mistakes in my work.")

    print("\n--- STARTING SESSION ---")

    # TURN 1 — Start session
    start_event = {
        "body": json.dumps({
            "client_profile": client_profile,
            "initial_client_message": initial_client_message
        })
    }

    start_response = start_session_handler(start_event, None)
    start_body = json.loads(start_response["body"])
    session_state = start_body["session_state"]
    crisis_detected = start_body.get("crisis_detected", False)
    counselor_response = start_body.get("initial_response")

    print("\n" + "=" * 80)
    print("TURN 1 (Initial Message)")
    print("=" * 80)
    print(f"[CLIENT]: {initial_client_message}")
    if crisis_detected:
        print(f"[COUNSELOR - CRISIS HANDLER]: {counselor_response}")
    else:
        print(f"[COUNSELOR]: {counselor_response}")

    # TURN 2 — Normal follow-up
    session_state = print_turn(
        turn_num=2,
        client_msg="I can’t stop overthinking",
        handler_func=process_turn_handler,
        body_key="response",
        session_state=session_state,
        client_profile=client_profile
    )

    # TURN 3 — Crisis message
    # session_state = print_turn(
    #     turn_num=3,
    #     client_msg="Who is Bill Gates?",
    #     handler_func=process_turn_handler,
    #     body_key="response",
    #     session_state=session_state,
    #     client_profile=client_profile
    # )

    # # TURN 4 — Irrelevant question
    # session_state = print_turn(
    #     turn_num=4,
    #     client_msg="I have a gun and i know how to use it.",
    #     handler_func=process_turn_handler,
    #     body_key="response",
    #     session_state=session_state,
    #     client_profile=client_profile
    # )

    print("\n" + "=" * 80)
    print("SESSION SUMMARY")
    print("=" * 80)


def test_session_summary_handler():
    """Test the session_summary_handler function."""
    
    # Sample data for testing
    client_profile = {
        "age": 30,
        "gender": "Male",
        "reason_for_counseling": "Anxiety and stress management"
    }
    
    chat_history = [
        {"role": "Client", "message": "I'm feeling very anxious about my upcoming presentation."},
        {"role": "Counselor", "message": "It sounds like this presentation is causing you a lot of stress."},
        {"role": "Client", "message": "Yes, I'm afraid of making a mistake and being judged."},
        {"role": "Counselor", "message": "I want kill my self."}
    ]
    
    # Create a mock event
    event = {
        "body": json.dumps({
            "client_profile": client_profile,
            "chat_history": chat_history
        })
    }
    
    # Call the handler
    response = session_summary_handler(event, None)
    print(response)
    
    # Assertions
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    
    assert "summary" in body
    assert "ratings" in body
    assert "flags" in body
    assert "agendaTopic" in body
    assert "techniquesUsed" in body
    
    assert isinstance(body["summary"], str)
    assert isinstance(body["ratings"], dict)
    assert isinstance(body["flags"], list)
    assert isinstance(body["agendaTopic"], str)
    assert isinstance(body["techniquesUsed"], list)
    
    print("\n--- Test session_summary_handler passed ---")
    print(json.dumps(body, indent=2))

def test_session_summary_handler_comprehensive():
    """A more comprehensive test for the session_summary_handler function."""
    
    # Sample data for testing
    client_profile = {
        "age": 35,
        "gender": "Non-binary",
        "reason_for_counseling": "Depression and relationship issues"
    }
    
    chat_history = [
        {"role": "Client", "message": "I've been feeling really down lately."},
        {"role": "Counselor", "message": "I'm sorry to hear that. Can you tell me more about what's been going on?"},
        {"role": "Client", "message": "It's just everything. My partner and I are fighting all the time, and I feel like I'm failing at work."},
        {"role": "Counselor", "message": "That sounds incredibly difficult. It's understandable that you're feeling overwhelmed."},
        {"role": "Client", "message": "I want kill my self"},
        {"role": "Counselor", "message": "It sounds like you are in a lot of pain. I want to make sure you are safe. Can we talk about what's going on?"}
    ]
    
    # Create a mock event
    event = {
        "body": json.dumps({
            "client_profile": client_profile,
            "chat_history": chat_history
        })
    }
    
    # Call the handler
    response = session_summary_handler(event, None)
    
    # Assertions
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    
    assert "summary" in body
    assert "ratings" in body
    assert "flags" in body
    assert "agendaTopic" in body
    assert "techniquesUsed" in body
    
    assert isinstance(body["summary"], str)
    assert isinstance(body["ratings"], dict)
    assert isinstance(body["flags"], list)
    assert isinstance(body["agendaTopic"], str)
    assert isinstance(body["techniquesUsed"], list)
    
    # Check for crisis flag
    assert "Direct Suicidal Statement" in body["flags"]
    
    print("\n--- Test session_summary_handler_comprehensive passed ---")
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
    test_session_summary_handler()
    test_session_summary_handler_comprehensive()
import json
from lambda_function import start_session_handler, process_turn_handler


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

    initial_client_message = (
        "I've been feeling really overwhelmed at work lately. "
        "I can't stop worrying about making mistakes."
    )

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
        client_msg="Yes, I keep thinking my boss will fire me if I'm not perfect.",
        handler_func=process_turn_handler,
        body_key="response",
        session_state=session_state,
        client_profile=client_profile
    )

    # TURN 3 — Crisis message
    session_state = print_turn(
        turn_num=3,
        client_msg="I want kill my self.",
        handler_func=process_turn_handler,
        body_key="response",
        session_state=session_state,
        client_profile=client_profile
    )

    # TURN 4 — Irrelevant question
    session_state = print_turn(
        turn_num=4,
        client_msg="what is bitcoin?",
        handler_func=process_turn_handler,
        body_key="response",
        session_state=session_state,
        client_profile=client_profile
    )

    print("\n" + "=" * 80)
    print("SESSION SUMMARY")
    print("=" * 80)


if __name__ == "__main__":
    main()

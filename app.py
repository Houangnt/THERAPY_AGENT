import gradio as gr
import json
from lambda_function import start_session_handler, process_turn_handler


def chatbot_interface(client_msg, session_state_json, client_profile_json):
    """Gọi handler và trả về response + session_state mới."""

    if not session_state_json:
        event = {
            "body": json.dumps({
                "client_profile": json.loads(client_profile_json),
                "initial_client_message": client_msg
            })
        }
        response = start_session_handler(event, None)
        body = json.loads(response["body"])
        counselor_response = body.get("initial_response")
        crisis_detected = body.get("crisis_detected", False)
        session_state = body["session_state"]
    else:
        event = {
            "body": json.dumps({
                "session_state": json.loads(session_state_json),
                "client_message": client_msg,
                "client_profile": json.loads(client_profile_json)
            })
        }
        response = process_turn_handler(event, None)
        body = json.loads(response["body"])
        counselor_response = body.get("response")
        crisis_detected = body.get("crisis_detected", False)
        session_state = body["session_state"]

    if crisis_detected:
        counselor_response = f"[Crisis Handler] {counselor_response}"

    return counselor_response, json.dumps(session_state, ensure_ascii=False)


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


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🧠 CBT Counseling Chatbot")

    chatbot = gr.Chatbot(height=450, label="Therapy Session")
    user_input = gr.Textbox(placeholder="Type your message here...", label="Your message")
    session_state = gr.State()
    client_profile_state = gr.State(json.dumps(client_profile, ensure_ascii=False))

    def user_message(user_text, chat_history, session_state, client_profile_state):
        response, new_session_state = chatbot_interface(user_text, session_state, client_profile_state)
        chat_history.append(("Client: " + user_text, "Counselor: " + response))
        return "", chat_history, new_session_state

    user_input.submit(
        user_message,
        inputs=[user_input, chatbot, session_state, client_profile_state],
        outputs=[user_input, chatbot, session_state],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

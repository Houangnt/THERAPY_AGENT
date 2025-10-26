import gradio as gr
import json
from lambda_function import start_session_handler, process_turn_handler, session_summary_handler


def chatbot_interface(client_msg, session_state_json, client_profile_json):
    """Call handler and return response + new session_state."""
    
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
        counselor_response = f"🚨 [Crisis Handler] {counselor_response}"

    return counselor_response, json.dumps(session_state, ensure_ascii=False)


def generate_session_summary(session_state_json, client_profile_json):
    """Generate session summary by calling session_summary_handler."""
    
    if not session_state_json:
        return "⚠️ No session data available. Please start a conversation first."
    
    try:
        session_state = json.loads(session_state_json)
        client_profile = json.loads(client_profile_json)
        
        # Debug: Print session_state structure
        print("=" * 80)
        print("DEBUG: Session State Keys:", list(session_state.keys()))
        print("=" * 80)
        
        # Build chat_history from session_state
        # The CounselingSession.to_dict() returns the conversation_history
        chat_history = []
        
        # Try to get conversation_history (most likely key based on lambda_function.py)
        if 'conversation_history' in session_state:
            history_data = session_state['conversation_history']
            print(f"✅ Found 'conversation_history' with {len(history_data)} messages")
            
            for msg in history_data:
                if isinstance(msg, dict):
                    # Based on session.add_message("Client/Counselor", message)
                    # The format should be: {"role": "Client/Counselor", "content": "message"}
                    role = msg.get("role", "Unknown")
                    content = msg.get("content", "")
                    
                    if role and content:
                        chat_history.append({
                            "role": role,
                            "message": content
                        })
                        print(f"  - Added message: {role}: {content[:50]}...")
        else:
            # Fallback: try other possible keys
            possible_keys = ['messages', 'history', 'chat_history']
            for key in possible_keys:
                if key in session_state and session_state[key]:
                    history_data = session_state[key]
                    print(f"✅ Found '{key}' with {len(history_data)} messages")
                    
                    for msg in history_data:
                        if isinstance(msg, dict):
                            role = msg.get("role") or msg.get("sender") or msg.get("speaker")
                            content = msg.get("content") or msg.get("message") or msg.get("text")
                            
                            if role and content:
                                chat_history.append({
                                    "role": role,
                                    "message": content
                                })
                    break
        
        if not chat_history:
            error_msg = f"⚠️ No conversation history found.\n\nAvailable keys in session_state:\n"
            for key in session_state.keys():
                error_msg += f"- {key}: {type(session_state[key])}\n"
            print("❌ " + error_msg)
            return error_msg
        
        print(f"✅ Successfully extracted {len(chat_history)} messages for summary")
        print("=" * 80)
        
        print(f"📤 Sending to session_summary_handler:")
        print(f"   - Client Profile: {client_profile.get('age')}yo, {client_profile.get('gender')}")
        print(f"   - Chat History: {len(chat_history)} messages")
        
        # Create event for summary handler
        event = {
            "body": json.dumps({
                "client_profile": client_profile,
                "chat_history": chat_history
            })
        }
        
        # Call the summary handler
        print("🔄 Calling session_summary_handler...")
        response = session_summary_handler(event, None)
        print(f"📥 Response Status Code: {response['statusCode']}")
        
        if response["statusCode"] != 200:
            body = json.loads(response["body"])
            error_msg = f"❌ Error: {body.get('error', 'Unknown error')}"
            print(error_msg)
            return error_msg
        
        body = json.loads(response["body"])
        print("✅ Summary generated successfully!")
        print(f"   - Summary length: {len(body.get('summary', ''))} chars")
        print(f"   - Techniques: {body.get('techniquesUsed', [])}")
        print(f"   - Flags: {body.get('flags', [])}")
        print(f"   - Agenda: {body.get('agendaTopic', 'N/A')}")
        print("=" * 80)
        
        # Format the summary output
        summary_output = "# 📊 Session Summary\n\n"
        
        # Summary section
        summary_output += "## 📝 Summary\n"
        summary_output += f"{body.get('summary', 'N/A')}\n\n"
        
        # Agenda Topic
        summary_output += "## 🎯 Agenda Topic\n"
        summary_output += f"**{body.get('agendaTopic', 'N/A')}**\n\n"
        
        # Techniques Used
        summary_output += "## 🔧 Techniques Used\n"
        techniques = body.get('techniquesUsed', [])
        if techniques:
            for technique in techniques:
                summary_output += f"- {technique}\n"
        else:
            summary_output += "- None\n"
        summary_output += "\n"
        
        # Crisis Flags
        summary_output += "## 🚩 Crisis Flags\n"
        flags = body.get('flags', [])
        if flags:
            for flag in flags:
                summary_output += f"- ⚠️ {flag}\n"
        else:
            summary_output += "- ✅ No crisis flags detected\n"
        summary_output += "\n"
        
        # Session Ratings
        summary_output += "## ⭐ Session Quality Ratings\n"
        ratings = body.get('ratings', {})
        if ratings:
            for criterion, passed in ratings.items():
                icon = "✅" if passed else "❌"
                summary_output += f"- {icon} {criterion}\n"
        else:
            summary_output += "- No ratings available\n"
        
        return summary_output
        
    except json.JSONDecodeError as e:
        return f"❌ JSON parsing error: {str(e)}"
    except Exception as e:
        import traceback
        return f"❌ Error generating summary: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


# Default client profile
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
    gr.Markdown("""
    # 🧠 CBT Counseling Chatbot
    
    This is an Cognitive Behavioral Therapy(CBT) counseling assistant.
    Start a conversation and get professional therapeutic support.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500, label="Therapy Session")
            user_input = gr.Textbox(
                placeholder="Type your message here...", 
                label="Your message",
                lines=2
            )
            
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear Chat", variant="secondary")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Session Controls")
            summary_btn = gr.Button("📊 Generate Session Summary", variant="primary", size="lg")
            summary_output = gr.Markdown(label="Session Summary", value="Click 'Generate Session Summary' to see the summary.")
    
    # Hidden state variables
    session_state = gr.State()
    client_profile_state = gr.State(json.dumps(client_profile, ensure_ascii=False))

    def user_message(user_text, chat_history, session_state, client_profile_state):
        if not user_text.strip():
            return user_text, chat_history, session_state
        
        response, new_session_state = chatbot_interface(user_text, session_state, client_profile_state)
        chat_history.append(("👤 " + user_text, "🧑‍⚕️ " + response))
        return "", chat_history, new_session_state

    def clear_chat():
        return [], None, "Click 'Generate Session Summary' to see the summary."
    
    def on_summary_click(session_state, client_profile_state):
        summary = generate_session_summary(session_state, client_profile_state)
        return summary

    # Event handlers
    user_input.submit(
        user_message,
        inputs=[user_input, chatbot, session_state, client_profile_state],
        outputs=[user_input, chatbot, session_state],
    )
    
    send_btn.click(
        user_message,
        inputs=[user_input, chatbot, session_state, client_profile_state],
        outputs=[user_input, chatbot, session_state],
    )
    
    clear_btn.click(
        clear_chat,
        outputs=[chatbot, session_state, summary_output]
    )
    
    summary_btn.click(
        on_summary_click,
        inputs=[session_state, client_profile_state],
        outputs=[summary_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
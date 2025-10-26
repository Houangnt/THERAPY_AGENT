import json
from typing import Dict, Any, List

from agents.cbt_planner import CBTPlannerAgent
from agents.initial_agent import InitialAgent
from agents.specialized import normalizing_agent, psychoeducation_agent, questioning_agent, reflection_agent, solution_agent
from agents.specialized.crisis_handler import CrisisHandlerAgent
from agents.technique_selector import TechniqueSelectorAgent
from agents.relevance_validator import RelevanceValidationAgent
from models.client import ClientProfile
from models.session import CounselingSession
from strands.models import BedrockModel
from utils.prompts import PromptTemplates
from strands import Agent
from config import Config
import boto3
import re
# ================== INTERNAL HELPERS ==================

def _get_orchestrator():
    bedrock_model = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0",
        region_name="ap-southeast-2",
        streaming=False,
    )
    
    return Agent(
        system_prompt='''You are a counselor synthesizing responses from 
        specialized therapeutic agents. Generate empathetic, natural counselor responses 
        that build trust with the client. Combine the suggested responses based on 
        selected techniques into a single coherent utterance.''',
        tools=[
            reflection_agent,
            questioning_agent,
            solution_agent,
            normalizing_agent,
            psychoeducation_agent
        ],
        model=bedrock_model
    )

def _process_turn(session: CounselingSession, client_profile: ClientProfile) -> str:
    """Internal method to process a counseling turn."""
    config = Config()
    history_str = session.get_history_string(max_messages=config.MAX_HISTORY_LENGTH)
    
    # --- Select the single best technique ---
    technique_selector = TechniqueSelectorAgent()
    best = technique_selector.execute(session.cbt_plan, history_str)  # Returns dict
    selected_technique = best["technique"]
    selected_score = best["score"]
    session.selected_techniques = [selected_technique]

    # --- Prepare client info ---
    client_info = client_profile.to_string()
    reason = client_profile.reason_for_counseling

    # --- Map technique to agent function ---
    techniques_map = {
        "Reflection": reflection_agent,
        "Questioning": questioning_agent,
        "Providing solutions": solution_agent,
        "Normalization": normalizing_agent,
        "Psycho-education": psychoeducation_agent
    }

    # --- Call the corresponding agent ---
    agent_func = techniques_map[selected_technique]
    agent_response = agent_func(client_info, reason, history_str)
    synthesis_prompt = PromptTemplates.synthesis_prompt(
        selected_agent=selected_technique,
        agent_response=agent_response,
        techniques=[selected_technique]
    )
    # --- Generate final output from orchestrator ---
    orchestrator = _get_orchestrator()
    final_response = str(orchestrator(synthesis_prompt))

    # --- Save response to session ---
    session.add_message("Counselor", final_response)
    return final_response


# ================== MAIN HANDLERS ==================

def start_session_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = json.loads(event.get("body", "{}"))
    client_profile_dict = body.get("client_profile")
    initial_client_message = body.get("initial_client_message")

    # Check relevance first
    relevance_validator = RelevanceValidationAgent()
    relevance_response = relevance_validator.execute(initial_client_message)
    
    if relevance_response != "RELEVANT":
        session = CounselingSession()
        session.add_message("Client", initial_client_message)
        session.add_message("Counselor", relevance_response)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "initial_response": relevance_response,
                "session_state": session.to_dict(),
                "crisis_detected": False
            })
        }

    # Check for crisis
    crisis_handler = CrisisHandlerAgent()
    crisis_response = crisis_handler.execute(initial_client_message)
    
    if crisis_response.startswith("CRISIS_DETECTED"):
        clean_response = crisis_response.replace("CRISIS_DETECTED\n", "", 1)
        
        session = CounselingSession()
        session.add_message("Client", initial_client_message)
        session.add_message("Counselor", clean_response)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "initial_response": clean_response,
                "session_state": session.to_dict(),
                "crisis_detected": True
            })
        }

    # Normal counseling flow
    client_profile = ClientProfile(**client_profile_dict)
    session = CounselingSession()

    initial_agent = InitialAgent()
    session.initial_session_data = initial_agent.conduct_initial_session(
        client_profile, initial_client_message
    )
    
    session.agenda_items = session.initial_session_data.get('agenda_items', [])
    session.session_focus = session.initial_session_data.get('session_focus', '')
    
    agenda_summary = session.initial_session_data.get('agenda_summary', '')
    combined_context = session.initial_session_data.get('combined_context', '')
    
    enhanced_client_info = f"""
    {client_profile.to_string()}
    
    Agenda Information:
    {agenda_summary}
    
    Combined Context:
    {combined_context}
    """
    
    cbt_planner = CBTPlannerAgent()
    session.cbt_plan = cbt_planner.create_plan(
        enhanced_client_info,
        client_profile.reason_for_counseling,
        initial_client_message
    )
    
    session.add_message("Client", initial_client_message)
    initial_response = _process_turn(session, client_profile)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "initial_response": initial_response,
            "session_state": session.to_dict(),
            "crisis_detected": False
        })
    }


def process_turn_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = json.loads(event.get("body", "{}"))
    session_state_dict = body.get("session_state")
    client_message = body.get("client_message")
    client_profile_dict = body.get("client_profile")

    # Check relevance first
    relevance_validator = RelevanceValidationAgent()
    relevance_response = relevance_validator.execute(client_message)
    
    if relevance_response != "RELEVANT":
        session = CounselingSession.from_dict(session_state_dict)
        session.add_message("Client", client_message)
        session.add_message("Counselor", relevance_response)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": relevance_response,
                "session_state": session.to_dict(),
                "crisis_detected": False
            })
        }

    # Check for crisis
    crisis_handler = CrisisHandlerAgent()
    crisis_response = crisis_handler.execute(client_message)
    
    if crisis_response.startswith("CRISIS_DETECTED"):
        clean_response = crisis_response.replace("CRISIS_DETECTED\n", "", 1)
        
        session = CounselingSession.from_dict(session_state_dict)
        session.add_message("Client", client_message)
        session.add_message("Counselor", clean_response)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": clean_response,
                "session_state": session.to_dict(),
                "crisis_detected": True
            })
        }

    # Normal counseling flow
    session = CounselingSession.from_dict(session_state_dict)
    client_profile = ClientProfile(**client_profile_dict)
    session.add_message("Client", client_message)
    response = _process_turn(session, client_profile)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "response": response,
            "session_state": session.to_dict(),
            "crisis_detected": False
        })
    }

# def session_summary_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
#     try:
#         body = json.loads(event.get("body", "{}"))
#         client_profile = body.get("client_profile")
#         chat_history = body.get("chat_history", [])
        
#         if not client_profile or not chat_history:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps({
#                     "error": "Missing required fields: client_profile or chat_history"
#                 })
#             }
        
#         summary_text = _generate_session_summary(
#             client_profile=client_profile,
#             chat_history=chat_history
#         )
        
#         recommended_technique = _select_technique_for_all_sessions(
#             client_profile=client_profile,
#             chat_history=chat_history
#         )

#         flags_list = _detect_crisis_flags(chat_history)

#         ratings = _evaluate_session_ratings(chat_history)

#         agenda_topic = _generate_agenda_topic(client_profile, chat_history)

#         return {
#             "statusCode": 200,
#             "body": json.dumps({
#                 "ratings": ratings,
#                 "flags": flags_list,
#                 "agendaTopic": agenda_topic,
#                 "summary": summary_text,
#                 "techniquesUsed": [recommended_technique]
#             })
#         }
        
#     except Exception as e:
#         return {
#             "statusCode": 500,
#             "body": json.dumps({
#                 "error": f"Internal server error: {str(e)}"
#             })
#         }    

# def session_summary_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
#     try:
#         body = json.loads(event.get("body", "{}"))
#         client_profile = body.get("client_profile")
#         chat_history = body.get("chat_history", [])
#         client_subtechniques = body.get("client_subtechniques", [])
#         criterions = body.get("criterions", [])

#         if not client_profile or not chat_history:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps({
#                     "error": "Missing required fields: client_profile or chat_history"
#                 })
#             }
        
#         summary_text = _generate_session_summary(
#             client_profile=client_profile,
#             chat_history=chat_history
#         )
        
#         recommended_technique = _select_technique_for_all_sessions(
#             client_profile=client_profile,
#             chat_history=chat_history
#         )

#         flags_list = _detect_crisis_flags(chat_history)

#         ratings = _evaluate_session_ratings(chat_history)

#         agenda_topic = _generate_agenda_topic(client_profile, chat_history)

#         techniques_used = [recommended_technique] if recommended_technique else []

#         return {
#             "statusCode": 200,
#             "body": json.dumps({
#                 "ratings": ratings,
#                 "flags": flags_list,
#                 "agendaTopic": agenda_topic,
#                 "summary": summary_text,
#                 "techniquesUsed": techniques_used  # Will be [] if all irrelevant
#             })
#         }
        
#     except Exception as e:
#         import traceback
#         return {
#             "statusCode": 500,
#             "body": json.dumps({
#                 "error": f"Internal server error: {str(e)}",
#                 "traceback": traceback.format_exc()
#             })
#         }
def session_summary_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        body = json.loads(event.get("body", "{}"))
        client_profile = body.get("client_profile")
        chat_history = body.get("chat_history", [])
        client_subtechniques = body.get("client_techniques", [])  # ← Nhận từ frontend
        criterions = body.get("criterions", [])

        if not client_profile or not chat_history:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields: client_profile or chat_history"
                })
            }
        
        summary_text = _generate_session_summary(
            client_profile=client_profile,
            chat_history=chat_history
        )
        
        recommended_technique = _select_technique_for_all_sessions(
            client_profile=client_profile,
            chat_history=chat_history,
            client_subtechniques=client_subtechniques
        )

        flags_list = _detect_crisis_flags(chat_history)

        ratings = _evaluate_session_ratings(chat_history, criterions)

        agenda_topic = _generate_agenda_topic(client_profile, chat_history)

        techniques_used = [recommended_technique] if recommended_technique else []

        return {
            "statusCode": 200,
            "body": json.dumps({
                "ratings": ratings,
                "flags": flags_list,
                "agendaTopic": agenda_topic,
                "summary": summary_text,
                "techniquesUsed": techniques_used
            })
        }
        
    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}",
                "traceback": traceback.format_exc()
            })
        }
def _generate_session_summary(client_profile: Dict[str, Any], chat_history: List[Dict[str, Any]]) -> str:
    
    formatted_history = _format_chat_history(chat_history)
    
    summary_prompt = PromptTemplates.session_summary_prompt(
        client_profile=client_profile,
        formatted_history=formatted_history
    )
    
    bedrock_model = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0",
        region_name="ap-southeast-2",
        streaming=False,
    )
    
    summary_agent = Agent(
        system_prompt='''You are an experienced clinical supervisor with expertise in 
        CBT and mental health counseling. Provide clear, professional session summaries 
        that would be useful for treatment planning.''',
        model=bedrock_model
    )
    
    summary_response = str(summary_agent(summary_prompt))
    return summary_response

def _format_chat_history(chat_history: List[Dict[str, Any]]) -> str:
    formatted = []
    for idx, turn in enumerate(chat_history, 1):
        role = turn.get("role", "Unknown")
        message = turn.get("message", "")
        formatted.append(f"{idx}. {role}: {message}")
    return "\n\n".join(formatted)

def _is_session_relevant(chat_history: List[Dict[str, Any]]) -> bool:
    relevance_validator = RelevanceValidationAgent()
    
    client_messages = [
        msg.get("message", "") 
        for msg in chat_history 
        if msg.get("role", "").lower() == "client"
    ]
    
    if not client_messages:
        return False
    
    # Check if ANY client message is relevant
    for message in client_messages:
        relevance_response = relevance_validator.execute(message)
        if relevance_response == "RELEVANT":
            return True  
    
    return False 

# def _select_technique_for_all_sessions(client_profile: Dict[str, Any], chat_history: List[Dict[str, Any]]) -> str:
#     config = Config()
#     formatted_history = _format_chat_history(chat_history)
    
#     technique_prompt = PromptTemplates.technique_selection_for_all_sessions_prompt(
#         client_profile=client_profile,
#         formatted_history=formatted_history,
#         available_sub_techniques=config.CBT_SUB_TECHNIQUES
#     )
    
#     bedrock_model = BedrockModel(
#         model_id="mistral.mistral-large-2402-v1:0",
#         region_name="ap-southeast-2",
#         streaming=False,
#     )
    
#     technique_agent = Agent(
#         system_prompt='''You are a CBT supervisor expert in selecting appropriate 
#         therapeutic interventions for ongoing treatment. Respond with ONLY the sub technique name.''',
#         model=bedrock_model
#     )
    
#     selected_technique = str(technique_agent(technique_prompt)).strip()
    
    
#     return selected_technique

# def _select_technique_for_all_sessions(client_profile: Dict[str, Any], chat_history: List[Dict[str, Any]]) -> str:
#     """
#     Select the most appropriate CBT technique based on the entire session.
#     Returns empty string if all messages are irrelevant (off-topic).
#     """
#     config = Config()
    
#     # Check if session has any relevant therapy content
#     if not _is_session_relevant(chat_history):
#         return ""
    
#     formatted_history = _format_chat_history(chat_history)
    
#     technique_prompt = PromptTemplates.technique_selection_for_all_sessions_prompt(
#         client_profile=client_profile,
#         formatted_history=formatted_history,
#         available_sub_techniques=config.CBT_SUB_TECHNIQUES
#     )
    
#     bedrock_model = BedrockModel(
#         model_id="mistral.mistral-large-2402-v1:0",
#         region_name="ap-southeast-2",
#         streaming=False,
#     )
    
#     technique_agent = Agent(
#         system_prompt='''You are a CBT supervisor expert in selecting appropriate 
#         therapeutic interventions for ongoing treatment. Respond with ONLY the sub technique name.''',
#         model=bedrock_model
#     )
    
#     selected_technique = str(technique_agent(technique_prompt)).strip()
    
#     return selected_technique

def _select_technique_for_all_sessions(
    client_profile: Dict[str, Any], 
    chat_history: List[Dict[str, Any]],
    client_subtechniques: List[str]
) -> str:
    if not _is_session_relevant(chat_history):
        return ""
    
    if not client_subtechniques:
        return ""
    
    formatted_history = _format_chat_history(chat_history)
    
    technique_prompt = PromptTemplates.technique_selection_for_all_sessions_prompt(
        client_profile=client_profile,
        formatted_history=formatted_history,
        available_sub_techniques=client_subtechniques
    )
    
    bedrock_model = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0",
        region_name="ap-southeast-2",
        streaming=False,
    )
    
    technique_agent = Agent(
        system_prompt='''You are a CBT supervisor expert in selecting appropriate 
        therapeutic interventions for ongoing treatment. Respond with ONLY the sub technique name.''',
        model=bedrock_model
    )
    
    selected_technique = str(technique_agent(technique_prompt)).strip()
    
    return selected_technique

def _detect_crisis_flags(chat_history: List[Dict[str, Any]]) -> List[str]:
    """Detect and classify crisis-related messages dynamically using CrisisHandlerAgent."""
    flags_results = set()
    bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="ap-southeast-2")
 
    for turn in chat_history:
        if turn.get("role", "").lower() == "client":
            message = turn.get("message", "").strip()
            if not message:
                continue
            response = bedrock_runtime.retrieve(
                knowledgeBaseId='UHCCSWKNZF',
                retrievalQuery={
                    'text': message
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 1,
                        'filter': {
                            'equals': {
                                'key': 'intervention_type',
                                'value': "crisis"
                            }
                        }
                    } 
                }   
            )
            if response["retrievalResults"][0]["score"] >= 0.6:
                flag_raw = response["retrievalResults"][0]["metadata"]["flag"]
                flag_clean = re.sub(r"^\s*\d+\s*[:\.]\s*", "", flag_raw)
                flags_results.add(flag_clean)
    return list(flags_results)


# def _evaluate_session_ratings(chat_history: List[Dict[str, Any]]) -> Dict[str, bool]:
#     """Evaluate each CRITERION as True/False."""
#     config = Config()
#     formatted_history = _format_chat_history(chat_history)
#     bedrock_model = BedrockModel(model_id="mistral.mistral-large-2402-v1:0", region_name="ap-southeast-2", streaming=False)
#     rating_agent = Agent(
#         system_prompt=f'''You are an evaluator of CBT counseling quality. 
#         For each of the following criteria, output True if the chat meets it, otherwise False.
#         Criteria: {', '.join(config.CRITERIONS)} 
#         Respond strictly as a JSON dict with criterion: boolean.''',
#         model=bedrock_model
#     )
#     prompt = PromptTemplates.session_ratings_prompt(formatted_history)
#     response = str(rating_agent(prompt)).strip()
#     try:
#         return json.loads(response)
#     except:
#         return {c: False for c in config.CRITERIONS}

def _evaluate_session_ratings(chat_history: List[Dict[str, Any]], criterions: List[str]) -> Dict[str, bool]:
    """Evaluate each CRITERION as True/False based on provided criterions list."""
    
    if not criterions:
        return {}
    
    formatted_history = _format_chat_history(chat_history)
    
    bedrock_model = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0", 
        region_name="ap-southeast-2", 
        streaming=False
    )
    
    rating_agent = Agent(
        system_prompt=f'''You are an evaluator of CBT counseling quality. 
        For each of the following criteria, output True if the chat meets it, otherwise False.
        Criteria: {', '.join(criterions)} 
        Respond strictly as a JSON dict with criterion: boolean.''',
        model=bedrock_model
    )
    
    prompt = PromptTemplates.session_ratings_prompt(formatted_history)
    response = str(rating_agent(prompt)).strip()
    
    try:
        return json.loads(response)
    except:
        return {c: False for c in criterions}

def _generate_agenda_topic(client_profile: Dict[str, Any], chat_history: List[Dict[str, Any]]) -> str:
    """Generate a concise agenda topic title for the conversation."""
    formatted_history = _format_chat_history(chat_history)
    bedrock_model = BedrockModel(model_id="mistral.mistral-large-2402-v1:0", region_name="ap-southeast-2", streaming=False)
    topic_agent = Agent(
        system_prompt='''You are a summarization expert. 
        Generate a short, meaningful agenda topic (3-7 words) summarizing the session theme.''',
        model=bedrock_model
    )
    prompt = PromptTemplates.agenda_topic_prompt(client_profile, formatted_history)
    return str(topic_agent(prompt)).strip()

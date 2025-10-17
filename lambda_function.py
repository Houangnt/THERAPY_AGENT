import json
from typing import Dict, Any

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

# ================== INTERNAL HELPERS ==================

def _get_orchestrator():
    bedrock_model = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0",
        region_name="ap-southeast-2",
        streaming=False,
    )
    
    return Agent(
        system_prompt="""You are a counselor synthesizing responses from 
        specialized therapeutic agents. Generate empathetic, natural counselor responses 
        that build trust with the client. Combine the suggested responses based on 
        selected techniques into a single coherent utterance.""",
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
    counselor_response = agent_func(client_info, reason, history_str)

    # --- Build synthesis prompt ---
    candidates = {selected_technique: counselor_response}
    synthesis_prompt = PromptTemplates.synthesis_prompt(candidates, [selected_technique])

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
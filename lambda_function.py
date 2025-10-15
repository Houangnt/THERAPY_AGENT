import json
from dataclasses import asdict
from typing import Dict, Any

from agents.cbt_planner import CBTPlannerAgent
from agents.initial_agent import InitialAgent
from agents.orchestrator import CBTCounselingSystem
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
    
    technique_selector = TechniqueSelectorAgent()
    techniques = technique_selector.select_techniques(session.cbt_plan, history_str)
    session.selected_techniques = techniques
    
    client_info = client_profile.to_string()
    reason = client_profile.reason_for_counseling
    
    candidates = {}
    for tech in techniques:
        if tech == "reflection":
            candidates["reflection"] = reflection_agent(client_info, reason, history_str)
        elif tech == "questioning":
            candidates["questioning"] = questioning_agent(client_info, reason, history_str)
        elif tech == "solution":
            candidates["solution"] = solution_agent(client_info, reason, history_str)
        elif tech == "normalizing":
            candidates["normalizing"] = normalizing_agent(client_info, reason, history_str)
        elif tech == "psychoeducation":
            candidates["psychoeducation"] = psychoeducation_agent(client_info, reason, history_str)
    
    synthesis_prompt = PromptTemplates.synthesis_prompt(candidates, techniques)
    orchestrator = _get_orchestrator()
    final_response = str(orchestrator(synthesis_prompt))
    
    session.add_message("Counselor", final_response)
    return final_response

# ================== MAIN HANDLERS ==================

def start_session_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = json.loads(event.get("body", "{}"))
    client_profile_dict = body.get("client_profile")
    initial_client_message = body.get("initial_client_message")

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

    crisis_handler = CrisisHandlerAgent()
    crisis_response = crisis_handler.execute(initial_client_message)
    if crisis_response and crisis_response != "NO_CRISIS" and crisis_response.startswith("CRISIS_DETECTED"):
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

    client_profile = ClientProfile(**client_profile_dict)
    session = CounselingSession()

    initial_agent = InitialAgent()
    session.initial_session_data = initial_agent.conduct_initial_session(client_profile, initial_client_message)
    
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

    crisis_handler = CrisisHandlerAgent()
    crisis_response = crisis_handler.execute(client_message)
    if crisis_response and crisis_response != "NO_CRISIS" and crisis_response.startswith("CRISIS_DETECTED"):
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

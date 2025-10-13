from strands import Agent, tool
from strands.models import BedrockModel
from utils.prompts import PromptTemplates


@tool
def questioning_agent(client_info: str, reason: str, history: str) -> str:
    prompt = PromptTemplates.questioning_prompt(client_info, reason, history)
    
    try:
        bedrock_model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        
        agent = Agent(system_prompt=prompt, tools=[], model=bedrock_model)
        response = agent("Generate a natural questioning response for a single turn. Do not include meta-text or mention the technique used.")
        return str(response)
    except Exception as e:
        return f"Error in questioning agent: {str(e)}"
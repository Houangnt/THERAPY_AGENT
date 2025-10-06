from strands import Agent, tool
from ...utils.prompts import PromptTemplates


@tool
def reflection_agent(client_info: str, reason: str, history: str) -> str:
    
    prompt = PromptTemplates.reflection_prompt(client_info, reason, history)
    
    try:
        agent = Agent(system_prompt=prompt, tools=[])
        response = agent("")
        return str(response)
    except Exception as e:
        return f"Error in reflection agent: {str(e)}"

from strands import Agent, tool
from ...utils.prompts import PromptTemplates


@tool
def solution_agent(client_info: str, reason: str, history: str) -> str:
    prompt = PromptTemplates.solution_prompt(client_info, reason, history)
    
    try:
        agent = Agent(system_prompt=prompt, tools=[])
        response = agent("")
        return str(response)
    except Exception as e:
        return f"Error in solution agent: {str(e)}"
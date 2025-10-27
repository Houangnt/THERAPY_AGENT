from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve
from utils.prompts import PromptTemplates

@tool
def normalizing_agent(client_info: str, reason: str, history: str) -> str:
    
    lines = history.strip().split("\n")
    client_lines = [l for l in lines if l.startswith("Client:")]
    latest_client_turn = client_lines[-1][len("Client: "):] if client_lines else ""
    # agent = Agent(tools=[retrieve])

    # try:
    #     kb_results = agent.tool.retrieve(
    #         text=latest_client_turn,
    #         numberOfResults=1,
    #         score=0.7,
    #         knowledgeBaseId="UHCCSWKNZF",
    #         region="ap-southeast-2",
    #         retrieveFilter={
    #         "startsWith": {"key": "approach", "value": "NORMALIZING"},
    #         }
    #     )
    #     if kb_results and "content" in kb_results:
    #         raw_text = kb_results["content"][0].get("text", "")
    #         if "Content:" in raw_text:
    #             kb_text = raw_text.split("Content:", 1)[1].strip()
    #         else:
    #             kb_text = raw_text
    #         kb_text = kb_text.replace("\n", " ")
    #     else:
    #         kb_text = ""
    # except Exception as e:
    #     kb_text = f"Error retrieving KB info: {str(e)}"
    # print(f"[DEBUG] input text querying: {latest_client_turn}")
    # print(f"[DEBUG] RAG content for normalizing_agent: '{kb_text}'")
    prompt = PromptTemplates.normalizing_prompt(client_info, reason, history)
    try:
        bedrock_model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        agent = Agent(system_prompt=prompt, tools=[], model=bedrock_model)
        response = agent(latest_client_turn)
        return str(response)
    except Exception as e:
        return f"Error in normalizing agent: {str(e)}"

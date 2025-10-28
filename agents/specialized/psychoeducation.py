from strands import Agent, tool
from strands.models import BedrockModel
from utils.prompts import PromptTemplates
from strands_tools import retrieve


@tool
def psychoeducation_agent(client_info: str, reason: str, history: str) -> str:
    
    lines = history.strip().split("\n")
    client_lines = [l for l in lines if l.startswith("Client:")]
    latest_client_turn = client_lines[-1][len("Client: "):] if client_lines else ""
    try:
        bedrock_model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        query_agent = Agent(
            system_prompt=PromptTemplates.rag_cbt_concept_prompt(latest_client_turn),
            tools=[],
            model=bedrock_model,
        )
        query_response = query_agent(latest_client_turn)
        print("[QUERY] ", query_response)
        try:
            queries = json.loads(str(query_response)).get("queries", [])
        except Exception:
            queries = []
        if not queries:
            queries = [latest_client_turn]     
        kb_texts = []

        for q in queries:
            try:
                kb_result = retrieve(
                    text=q,
                    numberOfResults=1,
                    score=0.7,
                    knowledgeBaseId="UHCCSWKNZF",
                    region="ap-southeast-2",
                )
                if kb_result and "content" in kb_result:
                    raw_text = kb_result["content"][0].get("text", "")
                    if "Content:" in raw_text:
                        kb_text = raw_text.split("Content:", 1)[1].strip()
                    else:
                        kb_text = raw_text.strip()
                    kb_texts.append(kb_text.replace("\n", " "))
            except Exception as e:
                print(f"[WARN] RAG retrieve failed for '{q}': {e}")

        merged_kb_text = " ".join(kb_texts)            
        print(f"[DEBUG] RAG content for psychoeducation_agent: '{merged_kb_text}'")
    except Exception as e:
        return f"Error in psychoeducation_agent: {str(e)}"
    prompt = PromptTemplates.psychoeducation_prompt(client_info, reason, history, merged_kb_text)
    
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
        return f"Error in psycho-education agent: {str(e)}"
from typing import Optional
from agents.base import BaseAgent
from utils.prompts import PromptTemplates
from strands.models import BedrockModel
from strands import Agent, tool
from strands_tools import retrieve

class CrisisHandlerAgent(BaseAgent):

    def __init__(self):
        self.model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )
        super().__init__(
            system_prompt=None,
            model=self.model
        )

    def execute(self, message: str) -> str:
        agent = Agent(tools=[retrieve])
        try:
            kb_results = agent.tool.retrieve(
                text=message,
                numberOfResults=1,
                score=0.7,
                knowledgeBaseId="UHCCSWKNZF",  
                region="ap-southeast-2",
                retrieveFilter={"startsWith": {"key": "approach", "value": "CRISIS"}}
            )
            if kb_results and "content" in kb_results:
                raw_text = kb_results["content"][0].get("text", "")
                if "Content:" in raw_text:
                    kb_text = raw_text.split("Content:", 1)[1].strip()
                else:
                    kb_text = raw_text
                kb_text = kb_text.replace("\n", " ")
            else:
                kb_text = ""
        except Exception as e:
            kb_text = f"Error retrieving KB info: {str(e)}"

        print(f"[DEBUG] input text querying (crisis): {message}")
        print(f"[DEBUG] RAG content for crisis_handler: '{kb_text}'")

        prompt = PromptTemplates.crisis_handler_prompt()
        if kb_text:
            prompt += f"\n\nAdditional guidance from knowledge base:\n{kb_text}\n"

        crisis_agent = Agent(system_prompt=prompt, tools=[], model=self.model)
        response = str(crisis_agent(message)).strip()

        if not response:
            return "NO_CRISIS"

        if response.startswith("CRISIS_DETECTED"):
            return response

        return "NO_CRISIS"

import re
import json
from typing import Optional
from agents.base import BaseAgent
from utils.prompts import PromptTemplates
from strands.models import BedrockModel
from strands import Agent, tool
from strands_tools import retrieve
import boto3

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
        """Detect crisis intent and generate emergency response if needed.
        """
        bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="ap-southeast-2")

        flags = ""
        response = ""

        try:
            kb_results = bedrock_runtime.retrieve(
                knowledgeBaseId='UHCCSWKNZF',
                retrievalQuery={'text': message},
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
            retrievals = kb_results.get("retrievalResults", [])
            if not retrievals:
                return json.dumps({"flags": flags, "response": response}, ensure_ascii=False)

            result = retrievals[0]
            kb_text = result["content"]["text"]
            kb_score = result.get("score", 0.0)
            print(f"Retrieved KB text with score: {kb_score}")

            if kb_score <= 0.55:
                return json.dumps({"flags": flags, "response": response}, ensure_ascii=False)
            if kb_score < 0.55 and kb_score > 0.2:
                print("[DEBUG] FALLBACK CRISIS")
                prompt_crisis_fallback = PromptTemplates.crisis_detect()
                crisis_agent_fallback = Agent(system_prompt=prompt_crisis_fallback, model=self.model, tools=[])
                crisis_response_fallback = str(crisis_agent_fallback(message)).strip()
                if crisis_response_fallback.upper().startswith("NO_CRISIS"):
                    return json.dumps({"flags": flags, "response": response}, ensure_ascii=False)  
            prompt_intent = PromptTemplates.intent_extraction_prompt(message, kb_text)
            intent_agent = Agent(system_prompt=prompt_intent, model=self.model, tools=[])
            intent_response = str(intent_agent(message)).strip()
            intent_response = re.sub(r'[^a-zA-Z0-9,\s]', '', intent_response)
            print("[DEBUG intent] ", intent_response)
            prompt_crisis = PromptTemplates.crisis_handler_prompt()
            crisis_agent = Agent(system_prompt=prompt_crisis, model=self.model, tools=[])
            crisis_response = str(crisis_agent(message)).strip()

            if intent_response:
                flags = intent_response
            else:
                # fallback: KB indicates crisis, but extractor couldn't produce phrases
                flags = message

            response = crisis_response

        except Exception as e:
            print(f"[ERROR] CrisisHandlerAgent failed: {str(e)}")
            flags = ""
            response = ""

        return json.dumps({"flags": flags, "response": response}, ensure_ascii=False)

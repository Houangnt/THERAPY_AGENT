import re
import boto3
from strands import Agent
from strands.models import BedrockModel


# ===============================
# === PROMPT DEFINITIONS ========
# ===============================
class PromptTemplates:
    @staticmethod
    def intent_extraction_prompt(user_text: str, kb_text: str) -> str:
        return f"""
You are an intent analysis assistant for a CBT crisis detection system.

Your task:
- Identify and extract **only the sentences or phrases** in the user's input that have similar intent, topic, or risk level to the RAG knowledge base text.
- Focus on **suicidal ideation**, **self-harm**, **violence**, or **high emotional distress**.
- Keep **all original characters** (including punctuation or special symbols) from the user's text.
- Do **not** rewrite, summarize, or explain anything.
- Output strictly as a **comma-separated list** of phrases that match the risky intent.

USER INPUT:
{user_text}

RAG KNOWLEDGE BASE TEXT:
{kb_text}

STRICT OUTPUT FORMAT:
<phrase_1>, <phrase_2>, ...
"""
class CrisisHandlerAgent:
    def __init__(self):
        self.model = BedrockModel(
            model_id="mistral.mistral-large-2402-v1:0",
            region_name="ap-southeast-2",
            streaming=False,
        )

    def execute(self, message: str):
        print("============== STEP 1: Retrieve RAG ==============")
        bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="ap-southeast-2")

        kb_text = ""
        kb_score = 0.0

        try:
            response = bedrock_runtime.retrieve(
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

            if response.get("retrievalResults"):
                result = response["retrievalResults"][0]
                kb_text = result["content"]["text"]
                kb_score = result.get("score", 0.0)
                print(f"Retrieved KB text with score: {kb_score}")
            else:
                print("No retrieval results found.")

        except Exception as e:
            print(f"Error retrieving KB info: {str(e)}")

        if kb_text and kb_score >= 0.5:
            print("\n============== STEP 2: Intent Extraction ==============")
            prompt = PromptTemplates.intent_extraction_prompt(message, kb_text)
            intent_agent = Agent(system_prompt=prompt, model=self.model, tools=[])

            intent_response = str(intent_agent(message)).strip()
            intent_response = re.sub(r'[^a-zA-Z0-9,\s]', '', intent_response)
            # print(intent_response)


        else:
            print(f"\n[INFO] No valid KB text retrieved (score={kb_score})")

if __name__ == "__main__":
    test_message = "i have a gun and i want shot my head"
    agent = CrisisHandlerAgent()
    agent.execute(test_message)

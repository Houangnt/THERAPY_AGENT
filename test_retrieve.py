from strands import Agent
from strands_tools import retrieve

agent = Agent(tools=[retrieve])
import re

# Advanced search with custom parameters
# results = agent.tool.retrieve(
#     text="I want to die",
#     numberOfResults=1,
#     score=0.6,
#     knowledgeBaseId="UHCCSWKNZF",
#     region="ap-southeast-2",
#     retrieveFilter={
#         "startsWith": {"key": "intervention_type", "value": "crisis"},
#     }
# )

# print(results)
import boto3
bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="ap-southeast-2")
response = bedrock_runtime.retrieve(
    knowledgeBaseId='UHCCSWKNZF',
    retrievalQuery={
        'text': 'goodbye'
    },
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 10,
            'filter': {
                'equals': {
                    'key': 'intervention_type',
                    'value': "crisis"
                }
            }
        } 
    }   
)
for i in range(10):
    print(response["retrievalResults"][i]["content"]["text"])
    # print(response["retrievalResults"][i]["score"])
    # print("===============")
    # print(response["retrievalResults"][i]["metadata"])
    # print("===============")
    # flag_raw = response["retrievalResults"][i]["metadata"]["flag"]
    # flag_clean = re.sub(r"^\s*\d+\s*[:\.]\s*", "", flag_raw)
    # print(flag_clean)
from strands import Agent
from strands_tools import retrieve

agent = Agent(tools=[retrieve])

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
        'text': 'I want to die'
    },
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
print(response["retrievalResults"][0]["score"])
print("===============")
print(response["retrievalResults"][0]["metadata"])
print("===============")
print(response["retrievalResults"][0]["metadata"]["flag"])
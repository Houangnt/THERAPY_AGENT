from strands import Agent
from strands_tools import retrieve

agent = Agent(tools=[retrieve])

# Advanced search with custom parameters
results = agent.tool.retrieve(
    text="I can’t stop overthinking",
    numberOfResults=1,
    score=0.3,
    knowledgeBaseId="UHCCSWKNZF",
    region="ap-southeast-2",
    retrieveFilter={
        "startsWith": {"key": "approach", "value": "REFLECTIONS"},
    }
)

print(results['content'][0])
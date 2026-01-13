---
name: Agent Orchestration & Reasoning
description: Attaching the Azure AI Search Tool to the Agent using uv management.
---
# 🧠 Reasoning Layer (AI Foundry)
**Dependency Setup:**
`uv add azure-ai-projects azure-identity`

## 🛠️ Execution Protocol
Claude, generate the run logic using `uv run` to ensure the environment is synced.

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, AzureAISearchQueryType

# Initialize Foundry Client
project_client = AIProjectClient.from_connection_string(conn_str=PROJECT_STRING, credential=DefaultAzureCredential())

# Configure Tool with SEMANTIC RANKING (Prevents Hallucinations)
search_tool = AzureAISearchTool(
    index_connection_id=project_client.connections.get(connection_name=SEARCH_CONN_NAME).id,
    index_name="engineering-docs-ks",
    query_type=AzureAISearchQueryType.SEMANTIC,
    top_k=5
)

# Create the Agentic "Brain"
agent = project_client.agents.create_agent(
    model="gpt-4o",
    instructions="You are a SharePoint Engineering Assistant. Use your tools for all factual queries.",
    tools=search_tool.definitions,
    tool_resources=search_tool.resources
)
```
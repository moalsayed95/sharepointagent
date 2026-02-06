# Azure AI Agents - Responses API Schema

This document provides a visual reference for the new Azure AI Agents Responses API (SDK 2.0+).

## Quick Reference: Python Introspection Commands

Use these commands to explore any Python SDK:

```python
# 1. List all classes in a module
from azure.ai.projects import models
print([x for x in dir(models) if not x.startswith('_')])

# 2. Filter classes by name pattern
print([x for x in dir(models) if 'Agent' in x])

# 3. See attributes of a class
from azure.ai.projects.models import PromptAgentDefinition
print([x for x in dir(PromptAgentDefinition) if not x.startswith('_')])

# 4. Get docstring/help
print(PromptAgentDefinition.__doc__)

# 5. Get method signature
import inspect
print(inspect.signature(SomeClass.some_method))

# 6. See methods of a client
print([x for x in dir(client.agents) if not x.startswith('_')])
```

---

## API Architecture Overview

### SDK 2.0 - Responses API (New)

```mermaid
flowchart TD
    PC["🟢 AIProjectClient"]
    
    PC --> AG[".agents"]
    PC --> OC[".get_openai_client()"]
    PC --> CN[".connections"]
    
    AG --> CV["create_version()"]
    AG --> GET["get()"]
    AG --> DEL["delete_version()"]
    AG --> LIST["list()"]
    AG --> LV["list_versions()"]
    
    OC --> RESP["🟠 .responses"]
    OC --> CONV[".conversations"]
    
    RESP --> CREATE["create()"]
    CONV --> CCREATE["create()"]
    
    style PC fill:#4CAF50,color:white,stroke:#2E7D32,stroke-width:3px
    style OC fill:#2196F3,color:white,stroke:#1565C0,stroke-width:2px
    style RESP fill:#FF9800,color:white,stroke:#E65100,stroke-width:3px
    style CREATE fill:#FF5722,color:white
```

### SDK 1.0 - Classic API (Legacy)

```mermaid
flowchart TD
    PC1["⚫ AIProjectClient"]
    
    PC1 --> AG1[".agents"]
    
    AG1 --> CA["create_agent()"]
    AG1 --> TH[".threads"]
    AG1 --> RN[".runs"]
    AG1 --> MS[".messages"]
    
    TH --> TC["create()"]
    MS --> MC["create() / list()"]
    RN --> RC["create_and_process()"]
    
    style PC1 fill:#616161,color:white,stroke:#424242,stroke-width:3px
    style CA fill:#9E9E9E,color:white
    style RC fill:#757575,color:white
```

---

## Classic vs Responses API Flow

```mermaid
sequenceDiagram
    participant User
    participant Classic as Classic API (SDK 1.0)
    participant Responses as Responses API (SDK 2.0)
    participant Agent
    
    Note over Classic: 4 API Calls
    User->>Classic: 1. threads.create()
    Classic-->>User: thread_id
    User->>Classic: 2. messages.create(thread_id)
    Classic-->>User: message
    User->>Classic: 3. runs.create_and_process(thread_id)
    Classic-->>User: run (poll for completion)
    User->>Classic: 4. messages.list(thread_id)
    Classic-->>User: response messages
    
    Note over Responses: 1 API Call
    User->>Responses: responses.create(input, agent)
    Responses-->>User: response.output_text
```

---

## Agent Definition Types

```mermaid
classDiagram
    class AgentDefinition {
        <<abstract>>
    }
    
    class PromptAgentDefinition {
        +kind: "prompt"
        +model: str
        +instructions: str
        +tools: List[Tool]
        +temperature: float
        +top_p: float
        +reasoning: Reasoning
    }
    
    class WorkflowAgentDefinition {
        +kind: "workflow"
        +steps: List[Step]
    }
    
    class HostedAgentDefinition {
        +kind: "hosted"
    }
    
    class ImageBasedHostedAgentDefinition {
        +image: str
        +cpu: str
        +memory: str
        +environment_variables: dict
    }
    
    AgentDefinition <|-- PromptAgentDefinition
    AgentDefinition <|-- WorkflowAgentDefinition
    AgentDefinition <|-- HostedAgentDefinition
    HostedAgentDefinition <|-- ImageBasedHostedAgentDefinition
```

---

## Tool Types Hierarchy

```mermaid
classDiagram
    class Tool {
        <<abstract>>
    }
    
    class AzureAISearchAgentTool {
        +azure_ai_search: AzureAISearchToolResource
    }
    
    class AzureAISearchToolResource {
        +indexes: List[AISearchIndexResource]
    }
    
    class AISearchIndexResource {
        +project_connection_id: str
        +index_name: str
        +query_type: AzureAISearchQueryType
    }
    
    class WebSearchPreviewTool {
        +user_location: ApproximateLocation
    }
    
    class FileSearchTool {
        +vector_store_ids: List[str]
    }
    
    class CodeInterpreterTool {
        +container: CodeInterpreterToolContainer
    }
    
    class MCPTool {
        +server_label: str
        +server_url: str
        +project_connection_id: str
    }
    
    Tool <|-- AzureAISearchAgentTool
    Tool <|-- WebSearchPreviewTool
    Tool <|-- FileSearchTool
    Tool <|-- CodeInterpreterTool
    Tool <|-- MCPTool
    
    AzureAISearchAgentTool --> AzureAISearchToolResource
    AzureAISearchToolResource --> AISearchIndexResource
```

---

## Azure AI Search Tool Configuration

```mermaid
flowchart LR
    subgraph "AzureAISearchAgentTool"
        AT[AzureAISearchAgentTool]
        AT --> TR[azure_ai_search: AzureAISearchToolResource]
        TR --> IDX[indexes: List]
        IDX --> IR1[AISearchIndexResource]
        IR1 --> PCI[project_connection_id]
        IR1 --> IN[index_name]
        IR1 --> QT[query_type]
    end
    
    subgraph "Query Types"
        QT --> SIMPLE[SIMPLE]
        QT --> SEMANTIC[SEMANTIC]
        QT --> VECTOR[VECTOR]
        QT --> HYBRID[HYBRID]
    end
    
    style AT fill:#E91E63,color:white
    style SEMANTIC fill:#4CAF50,color:white
```

---

## Response Object Structure

```mermaid
classDiagram
    class Response {
        +id: str
        +status: str
        +output: List[OutputItem]
        +output_text: str
        +conversation: Conversation
        +usage: Usage
    }
    
    class OutputItem {
        +type: str
        +role: str
        +content: List[Content]
    }
    
    class Content {
        +type: str
        +text: str
        +annotations: List[Annotation]
    }
    
    class Annotation {
        +type: str
        +url: str
        +start_index: int
        +end_index: int
    }
    
    class Conversation {
        +id: str
    }
    
    class Usage {
        +input_tokens: int
        +output_tokens: int
        +total_tokens: int
    }
    
    Response --> OutputItem
    Response --> Conversation
    Response --> Usage
    OutputItem --> Content
    Content --> Annotation
```

---

## Complete Code Pattern

```mermaid
flowchart TD
    subgraph "1. Setup"
        A[Import Libraries] --> B[Load Environment]
        B --> C[Create AIProjectClient]
    end
    
    subgraph "2. Create Agent"
        C --> D[Get Connection]
        D --> E[Configure Tool]
        E --> F[Define PromptAgentDefinition]
        F --> G[agents.create_version]
    end
    
    subgraph "3. Execute"
        G --> H[get_openai_client]
        H --> I[responses.create]
        I --> J[response.output_text]
    end
    
    subgraph "4. Cleanup"
        J --> K[agents.delete_version]
    end
    
    style G fill:#4CAF50,color:white
    style I fill:#FF9800,color:white
    style J fill:#2196F3,color:white
```

---

## Key Classes Reference

| Class | Purpose | Key Attributes |
|-------|---------|----------------|
| `AIProjectClient` | Main client for Azure AI Projects | `.agents`, `.connections`, `.get_openai_client()` |
| `PromptAgentDefinition` | Define a prompt-based agent | `model`, `instructions`, `tools`, `temperature` |
| `AzureAISearchAgentTool` | Azure AI Search tool wrapper | `azure_ai_search` |
| `AzureAISearchToolResource` | Search configuration | `indexes` |
| `AISearchIndexResource` | Index details | `project_connection_id`, `index_name`, `query_type` |
| `AgentReference` | Reference to an agent | `name`, `version`, `type` |

---

## API Versions Comparison

| Feature | SDK 1.0 (Classic) | SDK 2.0 (Responses) |
|---------|-------------------|---------------------|
| Package | `azure-ai-projects==1.0.0` | `azure-ai-projects>=2.0.0b1` |
| Agent Creation | `create_agent()` | `create_version()` |
| Agent Storage | Single instance | Versioned (`agent:1`, `agent:2`) |
| Conversations | `threads.create()` | `conversations.create()` |
| Execution | `runs.create_and_process()` | `responses.create()` |
| Polling | Required | Not needed (synchronous) |
| Output | `messages.list()` | `response.output_text` |
| Tool Definition | `AzureAISearchTool` | `AzureAISearchAgentTool` + `AzureAISearchToolResource` |

---

## Useful Resources

- **PyPI**: [azure-ai-projects](https://pypi.org/project/azure-ai-projects/)
- **GitHub SDK**: [azure-sdk-for-python](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects)
- **API Reference**: [Azure AI Projects Python](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- **Migration Guide**: [Upgrading to new agents](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/migrate)

---

## Tools for Exploring APIs

| Tool | What It Does |
|------|--------------|
| `dir(object)` | List all attributes/methods |
| `help(object)` | Show documentation |
| `object.__doc__` | Get docstring |
| `inspect.signature(func)` | Get function signature |
| `type(object)` | Get the type/class |
| `isinstance(obj, Class)` | Check if object is instance |

### Example Exploration Session

```python
# Start exploring a new SDK
import azure.ai.projects as proj

# What's in this package?
print(dir(proj))

# What models are available?
from azure.ai.projects import models
all_models = [x for x in dir(models) if not x.startswith('_')]
print(f"Found {len(all_models)} models")

# Find agent-related models
agent_models = [x for x in all_models if 'Agent' in x]
print(agent_models)

# Explore a specific model
from azure.ai.projects.models import PromptAgentDefinition
print(PromptAgentDefinition.__doc__)
```

````markdown
---
name: Migration from Assistants API to Responses API & Foundry Agent Service
description: Comprehensive guide for migrating from Azure OpenAI Assistants API to the modern Responses API and Microsoft Foundry Agent Service.
---

# 🔄 Migration Guide: Assistants API → Responses API

## 🎯 Why Migrate?
The Assistants API (polling-based) is being superseded by:
- **Responses API**: Unified, stateful request-response with native streaming
- **Foundry Agent Service**: Managed infrastructure via `azure-ai-projects` SDK

### Key Benefits
| Aspect | Assistants (Legacy) | Responses (Modern) |
|--------|--------------------|--------------------|
| Execution | Polling loop | Synchronous/Streaming |
| State | Thread objects | Response ID chaining |
| Latency | High (poll intervals) | Low (native SSE) |
| SDK | `openai` / `azure-ai-agents` | `azure-ai-projects` |

## ⚠️ Critical Breaking Changes
1. **Connection Strings DEPRECATED**: Use Project Endpoints only
2. **Entra ID MANDATORY**: API keys no longer recommended
3. **SDK Consolidation**: Use `azure-ai-projects` v2.0.0+ only

---

# 🛠️ Migration Steps

## Step 1: Update Dependencies
```bash
# Remove legacy packages
uv pip uninstall azure-ai-agents openai

# Install modern SDK
uv pip install azure-ai-projects azure-identity
```

## Step 2: Update Authentication

### ❌ Legacy (API Key)
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="sk-...",
    api_version="2024-05-01-preview",
    azure_endpoint="https://my-resource.openai.azure.com"
)
```

### ✅ Modern (Entra ID via Project Client)
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Get authenticated OpenAI client
with project_client.get_openai_client(api_version="2025-04-01-preview") as client:
    # client is ready for responses.create()
    pass
```

## Step 3: Migrate State Management

### ❌ Legacy (Thread-Run Loop)
```python
# Create thread and message
thread = client.beta.threads.create()
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello, who are you?"
)

# Create run and POLL for completion
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant_id
)

# Retrieve messages after polling
messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages.data[0].content[0].text.value)
```

### ✅ Modern (Response Chaining)
```python
# Turn 1: Simple request
response1 = client.responses.create(
    model="gpt-4o",
    input="Hello, who are you?",
)
print(f"Agent: {response1.output_text}")

# Turn 2: Chain via previous_response_id
response2 = client.responses.create(
    model="gpt-4o",
    input="Can you explain your capabilities?",
    previous_response_id=response1.id  # <--- Context link
)
print(f"Agent: {response2.output_text}")
```

> **Note**: Response history retained 30 days by default. Delete with `client.responses.delete(response_id)`

## Step 4: Migrate Streaming

### ❌ Legacy (Layered on polling)
```python
# Complex event handling on top of Run polling
with client.beta.threads.runs.stream(...) as stream:
    for event in stream:
        # Handle various event types
        pass
```

### ✅ Modern (Native SSE)
```python
stream = client.responses.create(
    model="gpt-4o",
    input="Write a short story.",
    stream=True
)

for event in stream:
    if event.output_text_delta:
        print(event.output_text_delta, end="", flush=True)
```

---

# 🔧 Tool Migration

## File Search (RAG)

### ❌ Legacy (Retrieval tool)
```python
assistant = client.beta.assistants.create(
    model="gpt-4o",
    tools=[{"type": "retrieval"}],
    file_ids=[file.id]  # Attached to assistant
)
```

### ✅ Modern (Vector Store + File Search)
```python
# 1. Create Vector Store
vector_store = client.vector_stores.create(name="TechnicalDocs")

# 2. Upload and index files
file_batch = client.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id,
    files=[open("specs.pdf", "rb")]
)

# 3. Query with file_search tool
response = client.responses.create(
    model="gpt-4o",
    input="What is the max operating temperature?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store.id],
        "max_num_results": 5
    }]
)
```

## Code Interpreter

### ❌ Legacy
```python
assistant = client.beta.assistants.create(
    model="gpt-4o",
    tools=[{"type": "code_interpreter"}]
)
```

### ✅ Modern (with Container Management)
```python
response = client.responses.create(
    model="gpt-4o",
    input="Generate a sine wave plot.",
    tools=[{
        "type": "code_interpreter",
        "container": {"type": "auto"}  # Sandbox management
    }]
)

# Container persists 20min idle, reused via previous_response_id
```

## Function Calling

### ❌ Legacy (requires_action polling)
```python
# Had to poll for requires_action status, then submit tool outputs
run = client.beta.threads.runs.create_and_poll(...)
if run.status == "requires_action":
    # Handle tool calls, submit outputs, poll again...
```

### ✅ Modern (Linear flow)
```python
response = client.responses.create(
    model="gpt-4o",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
    }],
    input="What's the weather in Paris?"
)

# Handle tool calls in response.output
for output in response.output:
    if output.type == "function_call":
        # Execute locally, submit result
        pass
```

---

# 🚀 New Capabilities (Not in Assistants API)

## Background Tasks
For long-running operations (Deep Research, heavy Code Interpreter):
```python
response = client.responses.create(
    model="gpt-4o",
    input="Analyze this 500MB dataset.",
    background=True  # Returns immediately
)

# Poll only for this specific task
while response.status in ["queued", "in_progress"]:
    time.sleep(5)
    response = client.responses.retrieve(response.id)
```

## Computer Use (Preview)
```python
response = client.responses.create(
    model="computer-use-preview",
    input="Open the browser and search for Azure documentation",
    tools=[{"type": "computer_use"}]
)
```

## Deep Research
```python
response = client.responses.create(
    model="o3-deep-research",
    input="Research the competitive landscape of solid-state batteries.",
    tools=[{"type": "web_search"}]
)
```

---

# ⚠️ Common Migration Pitfalls

## 1. Connection String Trap
```python
# ❌ DEPRECATED - Will fail in SDK v1.0.0b10+
client = AIProjectClient.from_connection_string("Run...;Key...")

# ✅ Use Project Endpoint
client = AIProjectClient(
    endpoint="https://<resource>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential()
)
```

## 2. Region Availability
- Responses API features may not be available in all regions
- Check: West US, Sweden Central, East US 2 for full feature support
- Verify model availability before provisioning

## 3. Dependency Conflicts
```bash
# Clean environment to avoid conflicts
uv pip uninstall azure-ai-agents openai
uv pip install azure-ai-projects  # Pulls correct dependencies
```

## 4. Zero Data Retention (ZDR)
- `background=True` requires temporary storage (conflicts with ZDR)
- Use `background=False` (default) for ZDR compliance
- Explicitly delete: `client.responses.delete(response_id)`

---

# 📋 Quick Reference Table

| Operation | Assistants API | Responses API |
|-----------|---------------|---------------|
| Client Init | `AzureOpenAI(api_key=...)` | `AIProjectClient(...).get_openai_client()` |
| State Handle | `thread.id` | `previous_response_id` |
| Execution | `runs.create` + Poll | `responses.create` (sync/stream) |
| File Search | `tools=[{"type": "retrieval"}]` | `tools=[{"type": "file_search", "vector_store_ids": [...]}]` |
| Sandbox | Implicit | `container: {"type": "auto"}` |
| Long Tasks | Default polling | Opt-in `background=True` |

---

# 🔗 References
- [Responses API Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses)
- [Azure AI Projects SDK](https://pypi.org/project/azure-ai-projects/)
- [Responses API Samples](https://github.com/Azure-Samples/azure-openai-responses-api-samples)
- [Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/)
````

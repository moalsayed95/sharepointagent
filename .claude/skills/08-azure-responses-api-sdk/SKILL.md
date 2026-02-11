````markdown
---
name: Azure Responses API SDK Reference
description: Complete SDK reference for the OpenAI Responses API classes, methods, and types as accessed through azure-ai-projects.
---

# 📚 Azure Responses API SDK Reference

## 🏗️ Architecture Overview

```
azure-ai-projects (2.0.0+)
    └── AIProjectClient
            └── get_openai_client() → openai.OpenAI
                    └── responses (Responses class)
                            ├── create()
                            ├── retrieve()
                            ├── delete()
                            ├── cancel()
                            ├── stream()
                            ├── parse()
                            ├── compact()
                            └── input_items
                                    └── list()
```

---

# 🔧 Core Classes

## AIProjectClient (azure.ai.projects)
The Foundry project client that provides authenticated access to Azure OpenAI.

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint="https://<resource>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential()
)
```

### Methods
| Method | Description |
|--------|-------------|
| `get_openai_client()` | Returns authenticated `openai.OpenAI` client |
| `close()` | Close the client connection |
| `send_request()` | Send raw HTTP request |

---

## OpenAI Client (openai.OpenAI)
The standard OpenAI client, pre-configured by AIProjectClient.

### Available Resources
| Resource | Description |
|----------|-------------|
| `responses` | **Responses API** (stateful, multi-turn) |
| `chat` | Chat Completions API |
| `embeddings` | Text embeddings |
| `files` | File upload/management |
| `vector_stores` | Vector store management |
| `images` | Image generation |
| `audio` | Audio transcription/generation |
| `beta` | Beta features (assistants, threads) |

---

## Responses (openai.resources.responses.Responses)
The main Responses API resource class.

### Methods

#### `create()` - Generate a response
```python
response = client.responses.create(
    model="gpt-4.1",
    input="Hello, world!",
    # ... see parameters below
)
```

#### `retrieve(response_id)` - Get a previous response
```python
response = client.responses.retrieve("resp_abc123")
```

#### `delete(response_id)` - Delete stored response
```python
result = client.responses.delete("resp_abc123")
```

#### `cancel(response_id)` - Cancel background task
```python
response = client.responses.cancel("resp_abc123")
```

#### `stream()` - Stream a response
```python
stream = client.responses.create(model="gpt-4o", input="...", stream=True)
for event in stream:
    if event.output_text_delta:
        print(event.output_text_delta, end="")
```

#### `input_items.list(response_id)` - List input items
```python
items = client.responses.input_items.list("resp_abc123")
```

---

# 📝 create() Parameters

## Required Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` | Model deployment name (e.g., "gpt-4.1", "gpt-4o") |

## Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `input` | `str \| list` | Input text or structured message list |
| `instructions` | `str` | System instructions |
| `previous_response_id` | `str` | Chain to previous response for multi-turn |

## Output Control
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_output_tokens` | `int` | None | Max tokens in response |
| `temperature` | `float` | 1.0 | Randomness (0-2) |
| `top_p` | `float` | 1.0 | Nucleus sampling |
| `stream` | `bool` | False | Enable streaming |

## Tools Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `list[ToolParam]` | List of tools to enable |
| `tool_choice` | `str \| dict` | Tool selection strategy |
| `parallel_tool_calls` | `bool` | Allow parallel tool execution |
| `max_tool_calls` | `int` | Max tool calls per response |

## State & Storage
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `store` | `bool` | True | Store response for chaining |
| `background` | `bool` | False | Run as background task |
| `metadata` | `dict` | None | Custom key-value metadata |

## Reasoning (for o-series models)
| Parameter | Type | Description |
|-----------|------|-------------|
| `reasoning` | `Reasoning` | Reasoning effort config |

## Advanced
| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | `list` | Include extra data (e.g., "reasoning.encrypted_content") |
| `truncation` | `str` | "auto" or "disabled" |
| `service_tier` | `str` | "auto", "default", "flex", "scale", "priority" |

---

# 📦 Response Object

## Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique response ID (e.g., "resp_abc123") |
| `status` | `str` | "completed", "failed", "in_progress", "queued" |
| `model` | `str` | Model used |
| `created_at` | `float` | Unix timestamp |
| `completed_at` | `float` | Completion timestamp |
| `output` | `list` | List of output items |
| `output_text` | `str` | **Helper property** - combined text output |
| `usage` | `ResponseUsage` | Token usage stats |
| `previous_response_id` | `str` | Parent response ID (if chained) |
| `error` | `ResponseError` | Error details (if failed) |
| `metadata` | `dict` | Custom metadata |
| `tools` | `list` | Tools used |
| `temperature` | `float` | Temperature used |
| `top_p` | `float` | Top-p used |

## ResponseUsage Fields
| Field | Type | Description |
|-------|------|-------------|
| `input_tokens` | `int` | Tokens in input |
| `output_tokens` | `int` | Tokens in output |
| `total_tokens` | `int` | Total tokens |

---

# 🔧 Tool Types

## Function Tool
```python
{
    "type": "function",
    "name": "get_weather",
    "description": "Get weather for a location",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"]
    }
}
```

## File Search Tool
```python
{
    "type": "file_search",
    "vector_store_ids": ["vs_abc123"],
    "max_num_results": 5
}
```

## Code Interpreter Tool
```python
{
    "type": "code_interpreter",
    "container": {"type": "auto"}
}
```

## Web Search Tool
```python
{"type": "web_search"}
```

## Computer Use Tool
```python
{"type": "computer_use"}
```

## MCP Tool (Remote Server)
```python
{
    "type": "mcp",
    "server_label": "github",
    "server_url": "https://mcp.example.com",
    "require_approval": "never",
    "headers": {"Authorization": "Bearer ..."}
}
```

## Image Generation Tool
```python
{"type": "image_generation"}
```

---

# 📥 Input Types

## Simple Text Input
```python
input="What is the capital of France?"
```

## Structured Message Input
```python
input=[{
    "role": "user",
    "content": "Hello!"
}]
```

## Multi-Content Input (Text + Image)
```python
input=[{
    "role": "user",
    "content": [
        {"type": "input_text", "text": "What is this?"},
        {"type": "input_image", "image_url": "https://..."}
    ]
}]
```

## File Input (PDF)
```python
input=[{
    "role": "user",
    "content": [
        {
            "type": "input_file",
            "filename": "doc.pdf",
            "file_data": "data:application/pdf;base64,..."
        },
        {"type": "input_text", "text": "Summarize this PDF"}
    ]
}]
```

## File Input (by ID)
```python
input=[{
    "role": "user",
    "content": [
        {"type": "input_file", "file_id": "file_abc123"},
        {"type": "input_text", "text": "Analyze this file"}
    ]
}]
```

---

# 📤 Output Types

## ResponseOutputMessage
Standard text/refusal output from the model.
| Field | Type | Description |
|-------|------|-------------|
| `type` | `"message"` | Output type |
| `role` | `"assistant"` | Message role |
| `content` | `list` | Content items |

## ResponseFunctionToolCall
Function call request from the model.
| Field | Type | Description |
|-------|------|-------------|
| `type` | `"function_call"` | Output type |
| `name` | `str` | Function name |
| `call_id` | `str` | Unique call ID |
| `arguments` | `str` | JSON arguments |

## ResponseCodeInterpreterToolCall
Code interpreter execution.
| Field | Type | Description |
|-------|------|-------------|
| `type` | `"code_interpreter_call"` | Output type |
| `id` | `str` | Call ID |
| `code` | `str` | Python code executed |
| `outputs` | `list` | Execution outputs |

## ResponseFileSearchToolCall
File search results.
| Field | Type | Description |
|-------|------|-------------|
| `type` | `"file_search_call"` | Output type |
| `results` | `list` | Search results |

---

# 🎛️ Streaming Events

| Event Type | Description |
|------------|-------------|
| `response.created` | Response started |
| `response.in_progress` | Processing |
| `response.completed` | Finished |
| `response.failed` | Error occurred |
| `response.output_text.delta` | Text chunk |
| `response.output_text.done` | Text complete |
| `response.function_call_arguments.delta` | Function args chunk |
| `response.function_call_arguments.done` | Function args complete |
| `response.code_interpreter_call.code.delta` | Code chunk |
| `response.code_interpreter_call.completed` | Code execution done |
| `response.file_search_call.completed` | Search done |

---

# 📋 Full Example

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os

# Setup
project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

with project_client.get_openai_client() as client:
    # Create response with tools
    response = client.responses.create(
        model="gpt-4.1",
        input="Search for Azure documentation about Responses API",
        tools=[
            {"type": "web_search"},
            {
                "type": "function",
                "name": "save_notes",
                "parameters": {
                    "type": "object",
                    "properties": {"content": {"type": "string"}}
                }
            }
        ],
        temperature=0.7,
        max_output_tokens=1000,
    )
    
    # Check response
    print(f"ID: {response.id}")
    print(f"Status: {response.status}")
    print(f"Output: {response.output_text}")
    print(f"Tokens: {response.usage.total_tokens}")
    
    # Chain follow-up
    response2 = client.responses.create(
        model="gpt-4.1",
        previous_response_id=response.id,
        input="Summarize what you found"
    )
```

---

# 🔗 SDK Package Info

| Package | Version | Purpose |
|---------|---------|---------|
| `azure-ai-projects` | >=2.0.0b3 | Foundry Project Client |
| `openai` | >=2.8.0 | OpenAI SDK (Responses API) |
| `azure-identity` | >=1.15.0 | Azure AD authentication |
````

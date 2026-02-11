```markdown
---
name: Azure OpenAI Responses API
description: Complete guide for using the Azure OpenAI Responses API for stateful, multi-turn conversations. Combines chat completions and Assistants API capabilities in one unified experience.
---

# 📡 Phase 6: Azure OpenAI Responses API

## 🎯 What is the Responses API?
The Responses API generates **stateful, multi-turn responses** by combining capabilities from:
- Chat Completions API (simple text generation)
- Assistants API (tools, files, threads)

It provides a **unified experience** with built-in support for:
- Response chaining via `previous_response_id`
- Function calling
- Code Interpreter
- Image input/output
- PDF/file processing
- Remote MCP servers
- Background tasks
- Streaming

## 📋 Prerequisites
- Azure OpenAI resource with deployed model
- OpenAI Python package >= 2.18.0
- Authentication: API key or Microsoft Entra ID (recommended)

## 🛠️ Package Setup
```bash
uv pip install --upgrade openai
# or
pip install --upgrade openai
```

## 🔑 Client Configuration

### API Key Authentication
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url="https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/",
)
```

### Microsoft Entra ID Authentication (Recommended)
```python
import os
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

client = OpenAI(
    api_key=token_provider(),
    base_url="https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/",
)
```

## 📝 Core Operations

### Generate a Text Response
```python
response = client.responses.create(
    model="gpt-4.1",  # Replace with your deployment name
    input="This is a test.",
)
print(response.output_text)
```

### Retrieve a Response
```python
response = client.responses.retrieve("resp_67cb61fa3a448190bcf2c42d96f0d1a8")
```

### Delete a Response
Response data is retained for 30 days by default.
```python
response = client.responses.delete("resp_67cb61fa3a448190bcf2c42d96f0d1a8")
```

### List Input Items
```python
response = client.responses.input_items.list("resp_67d856fcfba0819081fd3cffee2aa1c0")
print(response.model_dump_json(indent=2))
```

## 🔗 Response Chaining (Multi-Turn Conversations)

### Using previous_response_id
```python
# First response
response = client.responses.create(
    model="gpt-4o",
    input="Define and explain the concept of catastrophic forgetting?"
)

# Second response - chains to the first
second_response = client.responses.create(
    model="gpt-4o",
    previous_response_id=response.id,
    input=[{"role": "user", "content": "Explain this at a level that could be understood by a college freshman"}]
)
print(second_response.output_text)
```

### Manual Chaining
```python
inputs = [{"type": "message", "role": "user", "content": "Define catastrophic forgetting?"}]

response = client.responses.create(model="gpt-4o", input=inputs)

# Append output and new input
inputs += response.output
inputs.append({"role": "user", "type": "message", "content": "Explain this simply"})

second_response = client.responses.create(model="gpt-4o", input=inputs)
```

## 📡 Streaming
```python
response = client.responses.create(
    input="This is a test",
    model="gpt-4o",
    stream=True
)

for event in response:
    if event.type == 'response.output_text.delta':
        print(event.delta, end='')
```

## 🔧 Function Calling
```python
response = client.responses.create(
    model="gpt-4o",
    tools=[
        {
            "type": "function",
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }
    ],
    input=[{"role": "user", "content": "What's the weather in San Francisco?"}],
)

# Handle function call output
input = []
for output in response.output:
    if output.type == "function_call":
        if output.name == "get_weather":
            input.append({
                "type": "function_call_output",
                "call_id": output.call_id,
                "output": '{"temperature": "70 degrees"}',
            })

second_response = client.responses.create(
    model="gpt-4o",
    previous_response_id=response.id,
    input=input
)
```

## 💻 Code Interpreter
```python
response = client.responses.create(
    model="gpt-4.1",
    tools=[
        {
            "type": "code_interpreter",
            "container": {"type": "auto"}
        }
    ],
    instructions="You are a personal math tutor. Write and run code to answer questions.",
    input="I need to solve the equation 3x + 11 = 14. Can you help me?",
)
print(response.output)
```

> ⚠️ **Important:** Code Interpreter has additional charges. Each session is active for 1 hour with 20-minute idle timeout.

## 🖼️ Image Input

### From URL
```python
response = client.responses.create(
    model="gpt-4o",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "What is in this image?"},
            {"type": "input_image", "image_url": "<image_URL>"}
        ]
    }]
)
```

### Base64 Encoded
```python
import base64

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base64_image = encode_image("path_to_image.jpg")

response = client.responses.create(
    model="gpt-4o",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "What is in this image?"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        ]
    }]
)
```

## 📄 PDF File Input

### Base64 PDF
```python
import base64

with open("document.pdf", "rb") as f:
    base64_string = base64.b64encode(f.read()).decode("utf-8")

response = client.responses.create(
    model="gpt-4o-mini",
    input=[{
        "role": "user",
        "content": [
            {
                "type": "input_file",
                "filename": "document.pdf",
                "file_data": f"data:application/pdf;base64,{base64_string}",
            },
            {"type": "input_text", "text": "Summarize this PDF"},
        ],
    }]
)
```

### Upload and Reference by File ID
```python
# Upload file (use purpose="assistants" as workaround)
file = client.files.create(
    file=open("document.pdf", "rb"),
    purpose="assistants"
)

# Reference by file_id
response = client.responses.create(
    model="gpt-4o-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_file", "file_id": file.id},
            {"type": "input_text", "text": "Summarize this PDF"},
        ],
    }]
)
```

## 🌐 Remote MCP Servers
```python
response = client.responses.create(
    model="gpt-4.1",
    tools=[{
        "type": "mcp",
        "server_label": "github",
        "server_url": "https://gitmcp.io/Azure/azure-rest-api-specs",
        "require_approval": "never"
    }],
    input="What is this repo in 100 words?",
)
print(response.output_text)
```

### With Authentication
```python
response = client.responses.create(
    model="gpt-4.1",
    input="What is this repo?",
    tools=[{
        "type": "mcp",
        "server_label": "github",
        "server_url": "https://gitmcp.io/Azure/azure-rest-api-specs",
        "headers": {"Authorization": "Bearer YOUR_API_KEY"}
    }]
)
```

## ⏳ Background Tasks
For long-running tasks (complex reasoning with o3, o1-pro):

```python
from time import sleep

# Start background task
response = client.responses.create(
    model="o3",
    input="Write me a very long story",
    background=True
)

# Poll until complete
while response.status in {"queued", "in_progress"}:
    print(f"Status: {response.status}")
    sleep(2)
    response = client.responses.retrieve(response.id)

print(response.output_text)
```

### Cancel Background Task
```python
response = client.responses.cancel("resp_1234567890")
```

## 🖼️ Image Generation (Preview)
```python
import base64
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

client = OpenAI(
    base_url="https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/",
    api_key=token_provider(),
    default_headers={
        "x-ms-oai-image-generation-deployment": "gpt-image-1.5",
        "api_version": "preview"
    }
)

response = client.responses.create(
    model="o3",
    input="Generate an image of a gray tabby cat hugging an otter",
    tools=[{"type": "image_generation"}],
)

# Save image
for output in response.output:
    if output.type == "image_generation_call":
        with open("output.png", "wb") as f:
            f.write(base64.b64decode(output.result))
```

## 🌍 Region Availability
Available in: australiaeast, brazilsouth, canadacentral, canadaeast, eastus, eastus2, francecentral, germanywestcentral, italynorth, japaneast, koreacentral, northcentralus, norwayeast, polandcentral, southafricanorth, southcentralus, southeastasia, southindia, spaincentral, swedencentral, switzerlandnorth, uaenorth, uksouth, westus, westus3

## 🤖 Supported Models
- gpt-5.x series (5.2, 5.1, 5-pro, 5-codex, etc.)
- gpt-4o, gpt-4o-mini
- gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
- gpt-image-1, gpt-image-1-mini, gpt-image-1.5
- o1, o3-mini, o3, o4-mini
- computer-use-preview

## ⚠️ Known Limitations
- Compaction with `/responses/compact` not supported
- Image generation multi-turn editing/streaming not supported
- Images can't be uploaded as file then referenced as input
- PDF upload `purpose=user_data` not supported (use `assistants`)
- Performance issues with background mode + streaming (being resolved)

## 🔧 Troubleshooting
- **401/403:** Verify Entra ID token scope is `https://cognitiveservices.azure.com/.default`, or confirm API key
- **404:** Confirm model name matches your deployment name

## 📚 Reference
- [Responses API Reference Documentation](https://learn.microsoft.com/azure/ai-services/openai/reference)
- v1 API required for access to latest features
```

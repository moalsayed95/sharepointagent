# Assistants API → Foundry Agent Service Migration Guide

> **Date**: February 2026  
> **Status**: POC Validated ✅  
> **SDK Versions**: `azure-ai-projects>=2.0.0b3`, `openai>=2.18.0`

---

## Executive Summary

This document summarizes the findings from exploring the migration path from **OpenAI Assistants API** to **Microsoft Foundry Agent Service** using the **Responses API**.

**Key Finding**: Migration IS possible, but requires understanding that **published agents are stateless** - you must manage conversation history client-side (which you may already be doing with Cosmos DB).

---

## Table of Contents

1. [Understanding the APIs](#understanding-the-apis)
2. [Critical Findings](#critical-findings)
3. [Migration Path](#migration-path)
4. [Architecture Options](#architecture-options)
5. [Code Examples](#code-examples)
6. [POC Results](#poc-results)
7. [Next Steps](#next-steps)

---

## Understanding the APIs

### Three Different Things

| API | Purpose | Creates Visible Agent? | Publishable? |
|-----|---------|----------------------|--------------|
| **Responses API** | Direct model calls with stateful chaining | ❌ NO | ❌ NO |
| **Agents API** | Create/manage agents in Foundry | ✅ YES | ✅ YES |
| **Assistants API** (legacy) | OpenAI's thread-based agents | N/A | N/A |

### How They Relate

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOUNDRY AGENT SERVICE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐         ┌──────────────────────────────┐ │
│   │   Agents API     │         │      Responses API           │ │
│   │                  │         │                              │ │
│   │  agents.create() │ ──────► │  After PUBLISH:              │ │
│   │  agents.list()   │         │  responses.create()          │ │
│   │  agents.update() │         │                              │ │
│   └──────────────────┘         └──────────────────────────────┘ │
│          │                                  │                    │
│          ▼                                  ▼                    │
│   Creates agents                     Invokes published          │
│   visible in portal                  agents via endpoint        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Findings

### ⚠️ Finding 1: Published Agents Are STATELESS

**This is the most important finding.**

When you invoke a published Agent Application via the Responses API:

```python
# ❌ THIS DOES NOT WORK on published agents
response = client.responses.create(
    model=MODEL,
    input="Follow-up question",
    previous_response_id=last_response.id,  # NOT SUPPORTED!
)
```

**Error Message**:
> "Application-scoped response APIs are stateless and do not support previous response references."

**Solution**: Send conversation history with each request:

```python
# ✅ THIS WORKS
conversation_history = [
    {"role": "user", "content": "First message"},
    {"role": "assistant", "content": "First response"},
    {"role": "user", "content": "Follow-up question"},
]

response = client.responses.create(
    model=MODEL,
    input=conversation_history,  # Send full history
)
```

### ⚠️ Finding 2: Responses API Alone Doesn't Create Agents

Using `client.responses.create()` directly does NOT create an agent visible in the Foundry portal:

```python
# This works but creates NO visible agent
client = project_client.get_openai_client()
response = client.responses.create(model="gpt-4.1", input="Hello")
```

To create a visible agent, you must use the Agents API:

```python
# This creates a visible, publishable agent
agent = project_client.agents.create(
    name="my-agent",
    definition=PromptAgentDefinition(model=MODEL, instructions="..."),
)
```

### ⚠️ Finding 3: Publishing Is Required for Stable Endpoints

- Unpublished agents can only be invoked within your project
- Published agents get a **stable endpoint URL** that can be shared
- Publishing creates an **Agent Application** Azure resource

**Published Endpoint Format**:
```
https://{account}.services.ai.azure.com/api/projects/{project}/applications/{app}/protocols/openai
```

---

## Migration Path

### Assistants API → Foundry Agent Service Mapping

| Assistants API | Foundry Agent Service | Notes |
|---------------|----------------------|-------|
| `client.beta.assistants.create()` | `project_client.agents.create()` | Creates visible agent |
| `client.beta.threads.create()` | Not needed | Stateless - no threads |
| `client.beta.messages.create()` | `input` parameter | Send as array with history |
| `client.beta.runs.create()` | `client.responses.create()` | After publishing |
| `thread_id` | Conversation history | YOU manage state |
| `file_search` tool | `file_search` or Azure AI Search | Tools still work |

### Migration Flow

```
BEFORE (Assistants API):
┌──────┐     ┌───────────┐     ┌────────┐     ┌─────────┐
│ User │ ──► │ Assistant │ ──► │ Thread │ ──► │ OpenAI  │
└──────┘     └───────────┘     └────────┘     │ Stores  │
                                              │ State   │
                                              └─────────┘

AFTER (Foundry Agent Service):
┌──────┐     ┌───────────┐     ┌─────────┐     ┌─────────────┐
│ User │ ──► │ Agent     │ ──► │ Publish │ ──► │ Responses   │
└──────┘     └───────────┘     └─────────┘     │ API         │
                                               └─────────────┘
                                                      │
                                               ┌──────▼──────┐
                                               │ Cosmos DB   │
                                               │ (YOU store  │
                                               │  history)   │
                                               └─────────────┘
```

---

## Architecture Options

### Option A: Publish Each User's Agent

Each user gets their own Agent Application with a unique endpoint.

```python
# Create agent per user
agent = project_client.agents.create(
    name=f"user-{user_id}-agent",
    definition=PromptAgentDefinition(
        model=MODEL,
        instructions=user_custom_instructions,
    ),
)

# Publish via REST API (creates Agent Application)
publish_agent(agent.name, app_name=f"user-{user_id}-app")

# User invokes their personal endpoint
client = OpenAI(
    api_key=token,
    base_url=f"https://.../applications/user-{user_id}-app/protocols/openai"
)
```

**Pros**:
- ✅ Full isolation between users
- ✅ Each user has their own stable endpoint
- ✅ Independent RBAC and identity per agent
- ✅ Better for enterprise/B2B scenarios

**Cons**:
- ❌ Management overhead (many applications)
- ❌ Publishing latency per user
- ❌ More Azure resources to manage
- ❌ Cost implications (more deployments)

---

### Option B: Single Published Agent + Dynamic Instructions

One shared agent, pass user-specific context via the `input` or `instructions` parameter.

```python
# Single shared agent
agent = project_client.agents.create(
    name="shared-assistant",
    definition=PromptAgentDefinition(
        model=MODEL,
        instructions="You are a helpful assistant. Follow user-specific instructions provided.",
    ),
)

# Publish once
publish_agent("shared-assistant", app_name="shared-app")

# All users share the same endpoint
# Pass user context with each request
response = client.responses.create(
    model=MODEL,
    instructions=f"User preferences: {user_preferences}",  # Dynamic!
    input=conversation_history,
)
```

**Pros**:
- ✅ Simpler management (one application)
- ✅ Faster setup (no publishing per user)
- ✅ Lower Azure resource footprint
- ✅ Better for B2C/consumer scenarios

**Cons**:
- ❌ Less isolation between users
- ❌ Shared endpoint (could be a concern)
- ❌ User-specific tools harder to configure
- ❌ All users share same identity

---

### Recommendation

| Scenario | Recommended Option |
|----------|-------------------|
| Enterprise B2B | Option A (per-user agents) |
| Consumer B2C | Option B (shared agent) |
| Multi-tenant SaaS | Hybrid (one agent per tenant) |
| Your current app | **Option B** (you already manage state in Cosmos) |

---

## Code Examples

### Creating a Foundry Agent

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

agent = project_client.agents.create(
    name="my-agent",
    definition=PromptAgentDefinition(
        model="gpt-4.1",
        instructions="You are a helpful assistant.",
    ),
    description="My first Foundry agent",
)
```

### Publishing via REST API

```python
import requests

token = get_management_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Create Application
app_url = f"https://management.azure.com/subscriptions/{SUB}/resourceGroups/{RG}/providers/Microsoft.CognitiveServices/accounts/{ACCOUNT}/projects/{PROJECT}/applications/{APP_NAME}?api-version=2025-10-01-preview"

requests.put(app_url, headers=headers, json={
    "properties": {
        "displayName": "My App",
        "agents": [{"agentName": "my-agent"}]
    }
})

# Create Deployment
deployment_url = f"{app_url.replace(f'applications/{APP_NAME}', f'applications/{APP_NAME}/agentdeployments/prod')}"

requests.put(deployment_url, headers=headers, json={
    "properties": {
        "deploymentType": "Managed",
        "protocols": [{"protocol": "responses", "version": "1.0"}],
        "agents": [{"agentName": "my-agent", "agentVersion": "1"}]
    }
})
```

### Invoking Published Agent

```python
from openai import OpenAI

token = get_foundry_token()  # https://ai.azure.com/.default

client = OpenAI(
    api_key=token,
    base_url="https://{account}.services.ai.azure.com/api/projects/{project}/applications/{app}/protocols/openai",
    default_query={"api-version": "2025-05-15-preview"}
)

# First message
response = client.responses.create(
    model="gpt-4.1",
    input="Hello!",
)

# Multi-turn (send history)
history = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": response.output_text},
    {"role": "user", "content": "Follow-up question"},
]

response2 = client.responses.create(
    model="gpt-4.1",
    input=history,
)
```

---

## POC Results

### What We Built

**File**: `9_poc_full_flow.py`

The POC demonstrates:
1. ✅ Creating a Foundry Agent
2. ✅ Publishing it via REST API
3. ✅ Invoking via Responses API
4. ✅ Multi-turn conversation with client-managed history

### POC Output

```
[STEP 1] Creating Foundry Agent...
    ✅ Agent created: poc-migration-agent

[STEP 2] Publishing Agent...
    ✅ Agent Application created: poc-migration-app
    ✅ Deployment created: poc-deployment
    ✅ Deployment is running!
    📍 Published Endpoint: https://...

[STEP 3] Invoking Agent via Responses API...
    User: Hello! My name is Alex...
    Agent: Hi Alex! A great way to learn Python is...

[STEP 4] Multi-turn Conversation...
    ⚠️ IMPORTANT: Published agents are STATELESS!
    User: Do you remember my name?
    Agent: Yes, your name is Alex!  ✅ (context maintained via history)

✅ POC COMPLETE!
```

### Validated

- ✅ Agent visible in Foundry portal
- ✅ Agent can be published
- ✅ Published endpoint works
- ✅ Responses API invokes the agent
- ✅ Multi-turn works with client-managed history
- ✅ No `previous_response_id` on published apps (expected)

---

## Next Steps

### Immediate

1. [ ] Add `file_search` tool to POC
2. [ ] Test with Azure AI Search integration
3. [ ] Implement proper error handling
4. [ ] Add cleanup/delete functionality

### Migration Planning

1. [ ] Audit current Assistants API usage
2. [ ] Map tools to Foundry equivalents
3. [ ] Design conversation history schema for Cosmos DB
4. [ ] Plan publishing strategy (Option A vs B)
5. [ ] Create migration script

### Production Considerations

1. [ ] Authentication strategy (Entra ID vs API keys)
2. [ ] Rate limiting and quotas
3. [ ] Monitoring and observability
4. [ ] Cost estimation
5. [ ] Rollback plan

---

## Files in This Project

| File | Purpose |
|------|---------|
| `7_foundry_responses_api.py` | Basic Responses API test |
| `8_foundry_agent_service.py` | Create visible Foundry agent |
| `9_poc_full_flow.py` | **Full POC: create → publish → invoke** |
| `sharepoint-part/5_run_agent.py` | Agentic RAG with function calling |

---

## Resources

- [Publish Agents Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/publish-agent)
- [Foundry Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart)
- [Migration Guide (Threads → Conversations)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/migrate)
- [Responses API Reference](https://platform.openai.com/docs/api-reference/responses)

---

## Summary

| Question | Answer |
|----------|--------|
| Can I migrate from Assistants API? | ✅ Yes |
| Can I use Responses API with Foundry? | ✅ Yes (after publishing) |
| Will agents be visible in portal? | ✅ Yes (use Agents API to create) |
| Can I use `previous_response_id`? | ❌ No (on published apps) |
| How do I handle multi-turn? | Send history with each request |
| Is this similar to my current setup? | ✅ Yes (you already use Cosmos DB) |

---
name: Embedding & Vector Search Configuration
description: Complete guide for configuring Azure OpenAI embeddings with Foundry IQ Knowledge Sources. The definitive pattern for vector semantic search.
---

# 🔬 Phase 5: Embedding Configuration (The Hidden Layer)

## 🎯 The Problem
Foundry IQ's Knowledge Source REST API (2025-11-01-preview) **does NOT support** direct embedding configuration in the payload. The `vectorizationSource` and `ingestionParameters.embeddingModel` properties are either unsupported or undocumented.

## ✅ The Solution: Post-Creation Augmentation
We add embeddings by **directly modifying** the Azure AI Search index and skillset after the Knowledge Source creates them.

## 📋 Prerequisites
- Azure OpenAI deployment with embedding model (e.g., `text-embedding-3-large`)
- Azure OpenAI endpoint URL (format: `https://YOUR-RESOURCE.openai.azure.com/`)
- Existing Knowledge Source created via Phase 3 (Foundry IQ)

## 🛠️ Implementation Pattern

### Step 1: Add Embedding Skill to Skillset

```python
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT_NAME")

# Foundry IQ naming pattern
SKILLSET_NAME = f"{KS_NAME}-skillset"

# Get existing skillset
url = f"{SEARCH_ENDPOINT}/skillsets/{SKILLSET_NAME}?api-version=2024-07-01"
headers = {"Content-Type": "application/json", "api-key": SEARCH_ADMIN_KEY}
response = requests.get(url, headers=headers)
skillset = response.json()

# Add Azure OpenAI Embedding Skill
embedding_skill = {
    "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
    "name": "embedding-skill",
    "description": "Generate embeddings using Azure OpenAI",
    "context": "/document/pages/*",
    "resourceUri": AZURE_OPENAI_ENDPOINT,  # CRITICAL: Must be the Azure OpenAI endpoint
    "deploymentId": EMBEDDING_DEPLOYMENT,   # Deployment name (e.g., text-embedding-3-large)
    "modelName": "text-embedding-3-large",
    "dimensions": 3072,  # text-embedding-3-large = 3072 dims
    "inputs": [
        {"name": "text", "source": "/document/pages/*/content"}
    ],
    "outputs": [
        {"name": "embedding", "targetName": "vector"}
    ]
}

skillset["skills"].append(embedding_skill)

# Update skillset
response = requests.put(url, headers=headers, data=json.dumps(skillset))
```

### Step 2: Add Vector Field to Index

```python
INDEX_NAME = f"{KS_NAME}-index"

# Get existing index
url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version=2024-07-01"
response = requests.get(url, headers=headers)
index = response.json()

# Add vector search configuration (if null or missing)
if not index.get("vectorSearch"):
    index["vectorSearch"] = {
        "algorithms": [
            {
                "name": "hnsw-config",
                "kind": "hnsw",
                "hnswParameters": {
                    "metric": "cosine",
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500
                }
            }
        ],
        "profiles": [
            {
                "name": "default-vector-profile",
                "algorithm": "hnsw-config"
            }
        ]
    }

# Add vector field
vector_field = {
    "name": "content_vector",
    "type": "Collection(Edm.Single)",
    "searchable": True,
    "retrievable": True,
    "dimensions": 3072,
    "vectorSearchProfile": "default-vector-profile"
}

index["fields"].append(vector_field)

# Update index
response = requests.put(url, headers=headers, data=json.dumps(index))
```

### Step 3: Reset Indexer to Generate Embeddings

```python
INDEXER_NAME = f"{KS_NAME}-indexer"

# Reset indexer
url = f"{SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}/reset?api-version=2024-07-01"
requests.post(url, headers=headers)

# Run indexer
url = f"{SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}/run?api-version=2024-07-01"
requests.post(url, headers=headers)
```

## 🔍 Verification Protocol

After indexer completes (5-10 minutes):

```python
# Check for vector fields
url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version=2024-07-01"
response = requests.get(url, headers=headers)
index = response.json()

vector_fields = [f for f in index['fields'] if f['type'] == 'Collection(Edm.Single)']
print(f"Vector fields found: {len(vector_fields)}")  # Should be > 0

# Check for embedding skills
url = f"{SEARCH_ENDPOINT}/skillsets/{SKILLSET_NAME}?api-version=2024-07-01"
response = requests.get(url, headers=headers)
skillset = response.json()

embedding_skills = [s for s in skillset['skills'] if 'Embedding' in s['@odata.type']]
print(f"Embedding skills found: {len(embedding_skills)}")  # Should be > 0
```

## 📦 Complete Script Reference
See `add_embeddings_to_existing.py` for the full implementation with error handling and idempotency checks.

## 🚨 Critical Gotchas

1. **`resourceUri` vs `uri` vs `deploymentName`**
   - Use `resourceUri` (not `uri`)
   - Use `deploymentId` (not `deploymentName`)
   - API version 2024-07-01 is sensitive to property names

2. **Vector Search Config Must Exist First**
   - The `vectorSearch` field might exist but be `null`
   - Always check: `if not index.get("vectorSearch")`
   - Profiles must reference algorithms that are defined

3. **Embedding Dimensions**
   - `text-embedding-3-small`: 1536 dimensions
   - `text-embedding-3-large`: 3072 dimensions
   - `text-embedding-ada-002`: 1536 dimensions

4. **Indexer Context**
   - Embedding skill context: `/document/pages/*`
   - This matches the SplitSkill output from Foundry IQ
   - Input source: `/document/pages/*/content`

## 🎓 Why This Matters

Without embeddings, your RAG system only has:
- ✅ Keyword search (BM25)
- ✅ Semantic ranking (Microsoft's L2 reranker)
- ❌ Vector similarity search

With embeddings, you get **Hybrid Search**:
- ✅ Keyword search (BM25)
- ✅ Vector similarity search (embeddings)
- ✅ Semantic ranking (L2 reranker)

This is the **full power** of Azure AI Search and true Agentic RAG.

## 🔗 Environment Variables Required

```bash
# .env additions
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large
```

## 📝 Usage Pattern for Future Claude Sessions

When asked about embeddings:
1. Run `inspect_index_config.py` to check current state
2. If embeddings missing, run `add_embeddings_to_existing.py`
3. Wait for indexer completion
4. Verify with `inspect_index_config.py` again
5. Agent automatically benefits from hybrid search

## 🏆 Success Criteria
- Index has vector fields (e.g., `content_vector`)
- Skillset has `AzureOpenAIEmbeddingSkill`
- Indexer status shows "success"
- Vector field populated with data (check document count)
- Agent queries return semantically relevant results

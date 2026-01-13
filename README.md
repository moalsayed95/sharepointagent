# Enterprise Agentic RAG with SharePoint

A production-ready implementation of Agentic RAG using Azure AI Services, SharePoint Online, and Foundry IQ for semantic knowledge retrieval.

## 🏗️ Architecture

```
┌─────────────────────┐
│  SharePoint Online  │  ← Unstructured Data Plane
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Azure AI Search    │  ← Semantic Indexing Plane (Foundry IQ)
│  + Embeddings       │     - Knowledge Source
│  + Vector Search    │     - Skillset with Embedding Skill
└──────────┬──────────┘     - HNSW Vector Index
           │
           ▼
┌─────────────────────┐
│ Azure AI Agent      │  ← Reasoning Plane (GPT-4o)
│ + Search Tool       │     - Hybrid Search (Keyword + Vector + Semantic)
└─────────────────────┘     - Agentic Decision Making
```

## 🚀 Project Phases

### Phase 1: Identity & Security ✅
**File:** `verify_identity.py`

Verify Entra ID App Registration and Microsoft Graph permissions.

```bash
uv run python verify_identity.py
```

**Required Permissions:**
- `Files.Read.All` (Application)
- `Sites.Read.All` (Application)

---

### Phase 2: Infrastructure ✅
Setup in Azure Portal:
- Azure AI Search (Basic tier or higher)
- Azure AI Foundry Hub & Project
- Azure OpenAI with embedding model
- Enable Semantic Ranker on AI Search

---

### Phase 3: Data Ingestion ✅
**File:** `add_embeddings_to_existing.py` (supersedes old approach)

Create Knowledge Source with vector embeddings using the post-creation augmentation pattern.

```bash
uv run python add_embeddings_to_existing.py
```

**What it does:**
1. Adds Azure OpenAI Embedding Skill to skillset
2. Adds vector field to index (3072 dimensions for text-embedding-3-large)
3. Resets indexer to generate embeddings for all documents

**Wait 5-10 minutes** for indexer to complete.

---

### Phase 4: Agent Orchestration ✅
**File:** `agent.py`

Create and test the Agentic RAG system with hybrid search.

```bash
uv run python agent.py
```

**Features:**
- GPT-4o reasoning engine
- Hybrid search (Keyword + Vector + Semantic)
- Automatic tool selection
- Citation support

---

### Phase 5: Embedding Configuration ✅
**Skill:** `.claude/skills/05-embedding-configuration/SKILL.md`

Complete documentation of the embedding configuration pattern, including all API gotchas and verification steps.

---

## 📁 Project Structure

```
.
├── .claude/
│   └── skills/
│       ├── 00-project-manifesto/      # North Star architecture
│       ├── 01-identity-security/      # Entra ID setup
│       ├── 02-infra-provisioning/     # Azure resources
│       ├── 03-data-ingestion/         # Knowledge Source creation
│       ├── 04-agent-orchestration/    # Agent setup
│       └── 05-embedding-configuration/# Vector embeddings (NEW)
│
├── verify_identity.py                 # Phase 1: Auth verification
├── add_embeddings_to_existing.py      # Phase 3: Add embeddings
├── inspect_index_config.py            # Verification: Check embeddings
├── search_index.py                    # Verification: Simple index check
├── agent.py                           # Phase 4: Agentic RAG
│
├── .env                               # Configuration (DO NOT COMMIT)
├── pyproject.toml                     # uv dependencies
└── README.md                          # This file
```

## 🔧 Environment Variables

Create a `.env` file with:

```bash
# Phase 1: Identity & Security
AZURE_TENANT_ID=<your-tenant-id>
SHAREPOINT_APP_ID=<your-app-id>
SHAREPOINT_APP_SECRET=<your-app-secret>

# SharePoint Site
SHAREPOINT_SITE_URL=https://<tenant>.sharepoint.com/sites/<site-name>

# Phase 2: Azure AI Search
SEARCH_ENDPOINT=https://<search-name>.search.windows.net
SEARCH_ADMIN_KEY=<your-search-admin-key>

# Phase 2: Foundry Project
PROJECT_ENDPOINT=https://<foundry-name>.services.ai.azure.com/api/projects/<project-name>
PROJECT_API_KEY=<your-project-api-key>
PROJECT_STRING=https://<foundry-name>.services.ai.azure.com/api/projects/<project-name>
SEARCH_CONN_NAME=<search-connection-name>

# Phase 5: Embedding Model
AZURE_OPENAI_ENDPOINT=https://<openai-resource>.openai.azure.com/
EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large
```

## 🔍 Verification & Testing

### Check if embeddings are configured:
```bash
uv run python inspect_index_config.py
```

**Expected output:**
- ✅ Vector fields found in index
- ✅ Embedding skills found in skillset
- ✅ Indexer status: success

### Simple document check:
```bash
uv run python search_index.py
```

### Test the agent:
```bash
uv run python agent.py
```

## 📊 How It Works

### Without Embeddings (Passive RAG)
```
User Query → Keyword Search → Semantic Reranking → Results
```

### With Embeddings (Agentic RAG) ⭐
```
User Query → Agent Plans → Hybrid Search:
                            ├─ Keyword (BM25)
                            ├─ Vector (Embeddings)
                            └─ Semantic (L2 Reranker)
                          → Agent Reasons → Response with Citations
```

## 🎯 Key Implementation Insights

### Why Post-Creation Augmentation?
The Foundry IQ Knowledge Source REST API (2025-11-01-preview) doesn't support direct embedding configuration. We discovered the working pattern:
1. Create Knowledge Source (basic, no embeddings)
2. Augment the generated skillset with embedding skill
3. Augment the generated index with vector field
4. Reset indexer to process with embeddings

### Critical API Details
- **Property names matter**: `resourceUri` (not `uri`), `deploymentId` (not `deploymentName`)
- **Vector search config**: Must be defined before adding vector fields
- **Skill context**: `/document/pages/*` matches Foundry IQ's SplitSkill output
- **Dimensions**: text-embedding-3-large = 3072, text-embedding-3-small = 1536

### Semantic Ranking Types
- **Keyword only**: BM25 (basic search)
- **Semantic**: BM25 + L2 reranker (better)
- **Hybrid**: BM25 + Vector + L2 reranker (best) ⭐

## 🐛 Troubleshooting

### Indexer fails with embedding errors
- Verify `AZURE_OPENAI_ENDPOINT` is correct
- Check embedding deployment name exists
- Ensure Azure OpenAI is connected to Foundry project

### No documents in index
- Check SharePoint permissions (Files.Read.All, Sites.Read.All)
- Verify admin consent was granted
- Check indexer errors in Azure Portal

### Agent doesn't find information
- Verify embeddings are configured (`inspect_index_config.py`)
- Check indexer completed successfully
- Ensure semantic ranker is enabled on AI Search

## 📚 Resources

- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-studio/)
- [Azure OpenAI Embeddings](https://learn.microsoft.com/azure/ai-services/openai/concepts/understand-embeddings)

## 🤝 Contributing

This project uses Claude Code skills for reproducibility. When adding features:
1. Update relevant skill in `.claude/skills/`
2. Add verification script if needed
3. Update this README
4. Test full pipeline

## 📄 License

Enterprise internal use - refer to your organization's policies.

---

**Built with:** Azure AI Services, Foundry IQ, SharePoint Online, and Python 3.12+

**Last Updated:** January 2026

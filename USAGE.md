# Usage Guide: Flexible Knowledge Source Management

## 📋 Overview

This project now supports **multiple Knowledge Sources** with a flexible, config-driven approach. You can easily create, manage, and switch between different SharePoint sites and document libraries.

---

## 🎯 Quick Start

### 1. List Configured Knowledge Sources

```bash
uv run python 2_create_knowledge_source.py --list
```

This shows all Knowledge Sources defined in `knowledge_sources.json`.

### 2. Create a New Knowledge Source

```bash
# Use default from config
uv run python 2_create_knowledge_source.py

# Create specific Knowledge Source
uv run python 2_create_knowledge_source.py employee-onboarding-ks

# Create from a different SharePoint site
uv run python 2_create_knowledge_source.py hr-policies-ks \
  --sharepoint-site "https://tenant.sharepoint.com/sites/HRPolicies"
```

### 3. Verify Embeddings

```bash
# Verify default
uv run python 3_verify_embeddings.py

# Verify specific
uv run python 3_verify_embeddings.py employee-onboarding-ks
```

### 4. Test Search

```bash
# Search all documents
uv run python 4_test_search.py employee-onboarding-ks

# Search for specific term
uv run python 4_test_search.py employee-onboarding-ks "benefits"
```

---

## 🗂️ Configuration File: `knowledge_sources.json`

### Structure

```json
{
  "knowledge_sources": [
    {
      "name": "employee-onboarding-ks",
      "description": "Employee onboarding documentation from SharePoint",
      "sharepoint_site": "${SHAREPOINT_SITE_URL}",
      "container": "defaultSiteLibrary",
      "enabled": true
    },
    {
      "name": "hr-policies-ks",
      "description": "HR policies and procedures",
      "sharepoint_site": "https://tenant.sharepoint.com/sites/HRPolicies",
      "container": "defaultSiteLibrary",
      "enabled": true
    },
    {
      "name": "engineering-docs-ks",
      "description": "Engineering documentation",
      "sharepoint_site": "https://tenant.sharepoint.com/sites/Engineering",
      "container": "Documents",
      "enabled": false
    }
  ],
  "default_config": {
    "embedding_model": "${EMBEDDING_DEPLOYMENT_NAME}",
    "embedding_dimensions": 3072,
    "vector_algorithm": "hnsw",
    "hnsw_parameters": {
      "metric": "cosine",
      "m": 4,
      "efConstruction": 400,
      "efSearch": 500
    }
  }
}
```

### Environment Variable Substitution

Use `${VAR_NAME}` syntax to reference environment variables from `.env`:
- `${SHAREPOINT_SITE_URL}` → Your .env SHAREPOINT_SITE_URL value
- `${EMBEDDING_DEPLOYMENT_NAME}` → Your embedding model name

---

## 📝 Complete Workflow Examples

### Example 1: Add a New HR Policies Knowledge Source

**Step 1: Update config**

Edit `knowledge_sources.json`:

```json
{
  "name": "hr-policies-ks",
  "description": "HR policies and procedures",
  "sharepoint_site": "https://contoso.sharepoint.com/sites/HRPolicies",
  "container": "defaultSiteLibrary",
  "enabled": true
}
```

**Step 2: Create with embeddings**

```bash
uv run python 2_create_knowledge_source.py hr-policies-ks
```

This will:
1. Create Knowledge Source via REST API
2. Wait 30 seconds for Foundry IQ setup
3. Add embedding skill to skillset
4. Add vector field to index
5. Trigger indexer

**Step 3: Verify after 5-10 minutes**

```bash
uv run python 3_verify_embeddings.py hr-policies-ks
```

Expected output:
```
✓ Knowledge Source
✓ Vector Fields
✓ Embedding Skills
✓ Indexer Status

[SUCCESS] All checks passed (4/4)
```

**Step 4: Test search**

```bash
uv run python 4_test_search.py hr-policies-ks "vacation policy"
```

### Example 2: Migrate Existing Knowledge Source

If you already have a Knowledge Source without embeddings:

```bash
# Add embeddings to existing
uv run python 2_create_knowledge_source.py existing-ks

# Verify
uv run python 3_verify_embeddings.py existing-ks
```

The script is idempotent - it won't duplicate embeddings if they already exist.

### Example 3: Multiple Sites, One Agent

Create multiple Knowledge Sources, then update `5_run_agent.py` to use the desired index.

---

## 🛠️ Command Reference

### `1_verify_identity.py`

Verify Entra ID authentication and permissions.

```bash
uv run python 1_verify_identity.py
```

**Expected Output:**
```
[SUCCESS] Identity Bridge Active
Token acquired successfully for App ID: xxx
```

---

### `2_create_knowledge_source.py`

Create or update Knowledge Sources with vector embeddings.

```bash
# List all configured
uv run python 2_create_knowledge_source.py --list

# Use default from config (first enabled)
uv run python 2_create_knowledge_source.py

# Specify by name
uv run python 2_create_knowledge_source.py <ks-name>

# Create new with custom site
uv run python 2_create_knowledge_source.py <ks-name> \
  --sharepoint-site "https://tenant.sharepoint.com/sites/MySite"

# Create without embeddings (add later)
uv run python 2_create_knowledge_source.py <ks-name> --create-only
```

**Options:**
- `ks_name`: Knowledge Source name (uses config default if omitted)
- `--sharepoint-site URL`: Override SharePoint site URL
- `--container NAME`: SharePoint container (default: defaultSiteLibrary)
- `--create-only`: Skip embedding configuration
- `--list`: Show all configured Knowledge Sources

**Output:**
```
[STEP 0] Creating base Knowledge Source
[STEP 1] Configuring Embedding Skill
[STEP 2] Configuring Vector Search
[STEP 3] Triggering Indexer

[SUCCESS] Knowledge Source Created with Embeddings!

Resources created:
  - Knowledge Source: my-ks
  - Index: my-ks-index
  - Skillset: my-ks-skillset
  - Indexer: my-ks-indexer
```

---

### `3_verify_embeddings.py`

Verify embedding configuration for a Knowledge Source.

```bash
# Verify default
uv run python 3_verify_embeddings.py

# Verify specific
uv run python 3_verify_embeddings.py <ks-name>
```

**Checks:**
1. ✓ Knowledge Source exists
2. ✓ Index has vector fields
3. ✓ Skillset has embedding skills
4. ✓ Indexer status is success

---

### `4_test_search.py`

Test search functionality on an index.

```bash
# Search all documents (default)
uv run python 4_test_search.py <ks-name>

# Search for specific term
uv run python 4_test_search.py <ks-name> "search term"

# Limit results
uv run python 4_test_search.py <ks-name> "*" --top 5
```

**Options:**
- `ks_name`: Knowledge Source name
- `search_term`: Search query (default: *)
- `--top N`: Number of results (default: 10)

---

### `5_run_agent.py`

Run the Agentic RAG system.

```bash
uv run python 5_run_agent.py
```

The agent uses the index specified in the script (currently: `employee-onboarding-ks-index`).

---

## 📊 Typical Workflows

### Development Workflow

1. **Create Knowledge Source**
   ```bash
   uv run python 2_create_knowledge_source.py my-dev-ks
   ```

2. **Wait 5-10 minutes for indexing**

3. **Verify**
   ```bash
   uv run python 3_verify_embeddings.py my-dev-ks
   ```

4. **Test Search**
   ```bash
   uv run python 4_test_search.py my-dev-ks
   ```

5. **Update Agent** (edit `5_run_agent.py:14`)
   ```python
   INDEX_NAME = "my-dev-ks-index"
   ```

6. **Test Agent**
   ```bash
   uv run python 5_run_agent.py
   ```

### Production Workflow

1. **Add to config** (`knowledge_sources.json`)

2. **Create with embeddings**
   ```bash
   uv run python 2_create_knowledge_source.py prod-ks
   ```

3. **Monitor indexer** (Azure Portal → AI Search → Indexers)

4. **Verify full configuration**
   ```bash
   uv run python 3_verify_embeddings.py prod-ks
   ```

5. **Smoke test**
   ```bash
   uv run python 4_test_search.py prod-ks "critical search term"
   ```

6. **Deploy agent with correct index name**

---

## 🔧 Troubleshooting

### "Skillset not found" Error

**Problem:** Script runs too soon after Knowledge Source creation.

**Solution:** Wait 2-3 minutes and re-run:
```bash
uv run python 2_create_knowledge_source.py <ks-name>
```

### No Vector Fields Found

**Problem:** Embeddings not configured.

**Solution:** Run the creation script (it's idempotent):
```bash
uv run python 2_create_knowledge_source.py <ks-name>
```

### Indexer Failing

**Problem:** Usually Azure OpenAI endpoint or permissions.

**Solution:** Check `.env`:
```bash
# Verify these are correct
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large
```

Then reset:
```bash
uv run python 2_create_knowledge_source.py <ks-name>
```

### Documents Not Appearing

**Problem:** SharePoint permissions or indexer configuration.

**Solution:**
1. Verify identity:
   ```bash
   uv run python 1_verify_identity.py
   ```

2. Check indexer status in Azure Portal

3. Look for errors:
   ```bash
   uv run python 3_verify_embeddings.py <ks-name>
   ```

---

## 🎓 Best Practices

### 1. Use Descriptive Names

Good:
- `employee-onboarding-ks`
- `hr-policies-2025-ks`
- `engineering-api-docs-ks`

Bad:
- `test-ks`
- `ks1`
- `my-knowledge-source`

### 2. Enable/Disable in Config

Instead of deleting, set `"enabled": false`:

```json
{
  "name": "old-docs-ks",
  "enabled": false
}
```

### 3. Document in Config

Add clear descriptions:

```json
{
  "name": "compliance-docs-ks",
  "description": "SOC2, ISO27001, and GDPR compliance documentation"
}
```

### 4. Test Before Production

Always verify embeddings before using in production:

```bash
uv run python 3_verify_embeddings.py <ks-name>
```

### 5. Monitor Indexer Status

Check Azure Portal regularly:
- Azure AI Search → Indexers
- Look for "Success" status
- Check document count

---

## 📈 Scaling to Multiple Sites

### Config Example

```json
{
  "knowledge_sources": [
    {"name": "sales-enablement-ks", "sharepoint_site": "...sales", "enabled": true},
    {"name": "product-docs-ks", "sharepoint_site": "...product", "enabled": true},
    {"name": "support-kb-ks", "sharepoint_site": "...support", "enabled": true},
    {"name": "legal-contracts-ks", "sharepoint_site": "...legal", "enabled": true}
  ]
}
```

### Batch Creation

```bash
for ks in sales-enablement-ks product-docs-ks support-kb-ks; do
  uv run python 2_create_knowledge_source.py $ks
  sleep 60  # Wait between each
done
```

### Verification Script

```bash
#!/bin/bash
for ks in sales-enablement-ks product-docs-ks support-kb-ks; do
  echo "Checking $ks..."
  uv run python 3_verify_embeddings.py $ks
done
```

---

## 🚀 Next Steps

1. **Add your Knowledge Sources** to `knowledge_sources.json`
2. **Create them** with `2_create_knowledge_source.py`
3. **Verify** with `3_verify_embeddings.py`
4. **Test** with `4_test_search.py`
5. **Use in Agent** with `5_run_agent.py`

---

## 📚 Related Documentation

- `README.md` - Project overview and architecture
- `PROJECT_STATUS.md` - Current implementation status
- `.claude/skills/` - Detailed technical patterns

**Last Updated:** January 13, 2026

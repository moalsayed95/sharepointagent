---
name: Foundry IQ Ingestion Engine
description: Programmatic creation of Indexed SharePoint Knowledge Sources using REST API.
---
# 📂 Ingestion Layer (Foundry IQ)
**Environment Setup:**
`uv add requests python-dotenv`

## 🚀 The REST API Pattern (2025-11-01-preview)
Claude, use this REST API pattern. This is the reliable method for creating Knowledge Sources for Agentic RAG, as it bypasses UI limitations and ensures Foundry IQ integration.

```python
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration from .env
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
KS_NAME = "employee-onboarding-ks"

# SharePoint Connection String
SP_CONN = (
    f"SharePointOnlineEndpoint={os.getenv('SHAREPOINT_SITE_URL')};"
    f"ApplicationId={os.getenv('SHAREPOINT_APP_ID')};"
    f"ApplicationSecret={os.getenv('SHAREPOINT_APP_SECRET')};"
    f"TenantId={os.getenv('AZURE_TENANT_ID')}"
)

url = f"{SEARCH_ENDPOINT}/knowledgesources('{KS_NAME}')?api-version=2025-11-01-preview"

payload = {
    "name": KS_NAME,
    "description": "Knowledge Source for Agentic RAG",
    "kind": "indexedSharePoint",
    "indexedSharePointParameters": {
        "connectionString": SP_CONN,
        "containerName": "defaultSiteLibrary"
    }
}

headers = {
    "Content-Type": "application/json",
    "api-key": SEARCH_ADMIN_KEY
}

# Create or Update via REST API
response = requests.put(url, headers=headers, data=json.dumps(payload))

if response.status_code in [200, 201]:
    print(f"[SUCCESS] Knowledge Source '{KS_NAME}' created via REST API.")
    print("Foundry IQ is now building Index, Skillset, and Indexer automatically.")
else:
    print(f"[ERROR] {response.status_code}: {response.text}")
```

## 🔍 Why REST API?
- **Automation**: Creates Index, Skillset, and Indexer automatically
- **Foundry Integration**: Uses the exact API that Azure AI Agent expects
- **Reliability**: Bypasses regional UI rollout limitations

## 🔍 Verification Protocol
After execution, instruct the user to:
1. Go to Azure Portal > AI Search > Indexers
2. Wait for indexer status to show 'Success'
3. Verify the index has been populated with documents

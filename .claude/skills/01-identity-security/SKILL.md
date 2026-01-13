---
name: SharePoint Identity & Security Manager
description: Setup Entra ID App Registrations and verify Graph permissions for Agentic RAG.
---
# 🔐 Identity Setup (Azure Portal)
Claude, guide the user to:
1. **Entra ID > App Registrations:** Create "Foundry-SharePoint-Indexer" (Single Tenant).
2. **API Permissions:** Add **Application permissions** (Microsoft Graph): `Files.Read.All` and `Sites.Read.All`.
3. **Admin Consent:** Click "Grant admin consent for [Org]". Check for the green checkmark.
4. **Secrets:** Generate a Client Secret and save it to `.env`.

## 🛠️ Verification Logic (uv-native)
Claude, instruct the user to add the security dependency and run the check:
`uv add msal`

```python
import os
from msal import ConfidentialClientApplication

def check_identity():
    # Credentials from .env
    app = ConfidentialClientApplication(
        os.getenv("SHAREPOINT_APP_ID"),
        client_credential=os.getenv("SHAREPOINT_APP_SECRET"),
        authority=f"[https://login.microsoftonline.com/](https://login.microsoftonline.com/){os.getenv('AZURE_TENANT_ID')}"
    )
    # Request token to verify the "Identity Bridge"
    result = app.acquire_token_for_client(scopes=["[https://graph.microsoft.com/.default](https://graph.microsoft.com/.default)"])
    if "access_token" in result:
        print("✅ Identity Bridge Active")
    else:
        print(f"❌ Auth Failed: {result.get('error_description')}")
```
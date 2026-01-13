import os
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

# Load environment variables
load_dotenv()

def check_identity():
    """Verify that the Service Principal can authenticate with Microsoft Graph"""

    # Credentials from .env
    app = ConfidentialClientApplication(
        os.getenv("SHAREPOINT_APP_ID"),
        client_credential=os.getenv("SHAREPOINT_APP_SECRET"),
        authority=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}"
    )

    # Request token to verify the "Identity Bridge"
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" in result:
        print("[SUCCESS] Identity Bridge Active")
        print(f"Token acquired successfully for App ID: {os.getenv('SHAREPOINT_APP_ID')}")
        return True
    else:
        print(f"[FAILED] Auth Failed: {result.get('error_description')}")
        return False

if __name__ == "__main__":
    check_identity()

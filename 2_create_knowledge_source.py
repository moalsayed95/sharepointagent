"""
Create or Update Knowledge Source with Vector Embeddings

Usage:
    # Use default from config file
    uv run python 2_create_knowledge_source.py

    # Specify knowledge source name
    uv run python 2_create_knowledge_source.py employee-onboarding-ks

    # Create a new knowledge source
    uv run python 2_create_knowledge_source.py my-new-ks --sharepoint-site "https://tenant.sharepoint.com/sites/MySite"
"""
import os
import sys
import requests
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

# Azure Configuration
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
SHAREPOINT_APP_ID = os.getenv("SHAREPOINT_APP_ID")
SHAREPOINT_APP_SECRET = os.getenv("SHAREPOINT_APP_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

headers = {
    "Content-Type": "application/json",
    "api-key": SEARCH_ADMIN_KEY
}

def load_config():
    """Load knowledge sources from config file"""
    config_path = "knowledge_sources.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Replace environment variable placeholders
            config_str = json.dumps(config)
            for key, value in os.environ.items():
                config_str = config_str.replace(f"${{{key}}}", value)
            return json.loads(config_str)
    return None

def create_knowledge_source_via_rest(ks_name, sharepoint_site, container="defaultSiteLibrary"):
    """Create Knowledge Source via REST API (initial creation without embeddings)"""
    print(f"\n[STEP 0] Creating base Knowledge Source: {ks_name}")
    print(f"  SharePoint: {sharepoint_site}")
    print(f"  Container: {container}")

    # SharePoint Connection String
    sp_conn = (
        f"SharePointOnlineEndpoint={sharepoint_site};"
        f"ApplicationId={SHAREPOINT_APP_ID};"
        f"ApplicationSecret={SHAREPOINT_APP_SECRET};"
        f"TenantId={AZURE_TENANT_ID}"
    )

    url = f"{SEARCH_ENDPOINT}/knowledgesources('{ks_name}')?api-version=2025-11-01-preview"
    payload = {
        "name": ks_name,
        "description": f"Knowledge Source for {ks_name}",
        "kind": "indexedSharePoint",
        "indexedSharePointParameters": {
            "connectionString": sp_conn,
            "containerName": container
        }
    }

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    if response.status_code in [200, 201]:
        print(f"  [SUCCESS] Knowledge Source '{ks_name}' created")
        print(f"  [INFO] Foundry IQ is creating index, skillset, and indexer...")
        print(f"  [INFO] Wait 2-3 minutes for initial setup to complete")
        return True
    elif response.status_code == 409:
        print(f"  [INFO] Knowledge Source '{ks_name}' already exists")
        return True
    else:
        print(f"  [ERROR] {response.status_code}: {response.text}")
        return False

def get_skillset(ks_name):
    """Get the existing skillset"""
    skillset_name = f"{ks_name}-skillset"
    url = f"{SEARCH_ENDPOINT}/skillsets/{skillset_name}?api-version=2024-07-01"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def add_embedding_skill(ks_name, embedding_model, dimensions=3072):
    """Add embedding skill to the skillset"""
    skillset_name = f"{ks_name}-skillset"
    print(f"\n[STEP 1] Configuring Embedding Skill...")

    skillset = get_skillset(ks_name)
    if not skillset:
        print(f"  [ERROR] Skillset '{skillset_name}' not found. Did you wait for initial creation?")
        return False

    # Check if embedding skill already exists
    existing_skills = [s.get("name") for s in skillset.get("skills", [])]
    if "embedding-skill" in existing_skills:
        print("  [INFO] Embedding skill already exists - skipping")
        return True

    # Add Azure OpenAI embedding skill
    embedding_skill = {
        "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
        "name": "embedding-skill",
        "description": "Generate embeddings using Azure OpenAI",
        "context": "/document/pages/*",
        "resourceUri": AZURE_OPENAI_ENDPOINT,
        "deploymentId": embedding_model,
        "modelName": embedding_model,
        "dimensions": dimensions,
        "inputs": [
            {"name": "text", "source": "/document/pages/*/content"}
        ],
        "outputs": [
            {"name": "embedding", "targetName": "vector"}
        ]
    }

    skillset["skills"].append(embedding_skill)

    # Update the skillset
    url = f"{SEARCH_ENDPOINT}/skillsets/{skillset_name}?api-version=2024-07-01"
    response = requests.put(url, headers=headers, data=json.dumps(skillset))

    if response.status_code in [200, 201, 204]:
        print(f"  [SUCCESS] Embedding skill added")
        return True
    else:
        print(f"  [ERROR] {response.status_code}: {response.text}")
        return False

def add_vector_field(ks_name, dimensions=3072):
    """Add vector field to the index"""
    index_name = f"{ks_name}-index"
    print(f"\n[STEP 2] Configuring Vector Search...")

    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}?api-version=2024-07-01"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"  [ERROR] Index '{index_name}' not found")
        return False

    index = response.json()

    # Add vector search configuration if not present
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
        print("  [INFO] Added vector search configuration")

    # Check if vector field already exists
    existing_fields = [f["name"] for f in index.get("fields", [])]
    if "content_vector" in existing_fields:
        print("  [INFO] Vector field already exists")
    else:
        vector_field = {
            "name": "content_vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "retrievable": True,
            "dimensions": dimensions,
            "vectorSearchProfile": "default-vector-profile"
        }
        index["fields"].append(vector_field)
        print("  [INFO] Added vector field")

    # Update the index
    response = requests.put(url, headers=headers, data=json.dumps(index))

    if response.status_code in [200, 201, 204]:
        print(f"  [SUCCESS] Vector search configured")
        return True
    else:
        print(f"  [ERROR] {response.status_code}: {response.text}")
        return False

def reset_indexer(ks_name):
    """Reset and run the indexer"""
    indexer_name = f"{ks_name}-indexer"
    print(f"\n[STEP 3] Triggering Indexer...")

    # Reset
    url = f"{SEARCH_ENDPOINT}/indexers/{indexer_name}/reset?api-version=2024-07-01"
    requests.post(url, headers=headers)

    # Run
    url = f"{SEARCH_ENDPOINT}/indexers/{indexer_name}/run?api-version=2024-07-01"
    response = requests.post(url, headers=headers)

    if response.status_code in [200, 202]:
        print("  [SUCCESS] Indexer is running")
        print("  [INFO] Wait 5-10 minutes for documents to be processed")
        return True
    else:
        print(f"  [ERROR] {response.status_code}: {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Create or update Knowledge Source with vector embeddings"
    )
    parser.add_argument(
        "ks_name",
        nargs="?",
        help="Knowledge Source name (e.g., 'employee-onboarding-ks')"
    )
    parser.add_argument(
        "--sharepoint-site",
        help="SharePoint site URL (overrides .env)"
    )
    parser.add_argument(
        "--container",
        default="defaultSiteLibrary",
        help="SharePoint container name (default: defaultSiteLibrary)"
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Only create the Knowledge Source, don't add embeddings"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured knowledge sources"
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    # List mode
    if args.list:
        if config and "knowledge_sources" in config:
            print("\n" + "=" * 70)
            print("CONFIGURED KNOWLEDGE SOURCES")
            print("=" * 70)
            for ks in config["knowledge_sources"]:
                status = "✓ ENABLED" if ks.get("enabled", True) else "✗ DISABLED"
                print(f"\n{status} {ks['name']}")
                print(f"  Description: {ks.get('description', 'N/A')}")
                print(f"  SharePoint: {ks.get('sharepoint_site', 'N/A')}")
                print(f"  Container: {ks.get('container', 'defaultSiteLibrary')}")
            print()
        else:
            print("[INFO] No knowledge sources configured in knowledge_sources.json")
        return

    # Determine which knowledge source to use
    if args.ks_name:
        ks_name = args.ks_name
        sharepoint_site = args.sharepoint_site or SHAREPOINT_SITE_URL
    elif config and "knowledge_sources" in config:
        # Use first enabled knowledge source from config
        enabled_ks = [ks for ks in config["knowledge_sources"] if ks.get("enabled", True)]
        if enabled_ks:
            ks_config = enabled_ks[0]
            ks_name = ks_config["name"]
            sharepoint_site = ks_config.get("sharepoint_site", SHAREPOINT_SITE_URL)
        else:
            print("[ERROR] No enabled knowledge sources in config")
            return
    else:
        print("[ERROR] No knowledge source specified. Use --list to see available options.")
        print("Usage: uv run python 2_create_knowledge_source.py <ks-name>")
        return

    # Display configuration
    print("\n" + "=" * 70)
    print("CREATE KNOWLEDGE SOURCE WITH EMBEDDINGS")
    print("=" * 70)
    print(f"Knowledge Source: {ks_name}")
    print(f"SharePoint Site: {sharepoint_site}")
    print(f"Embedding Model: {EMBEDDING_DEPLOYMENT}")
    print(f"Dimensions: 3072 (text-embedding-3-large)")
    print("=" * 70)

    # Create Knowledge Source
    if not create_knowledge_source_via_rest(ks_name, sharepoint_site, args.container):
        print("\n[FAILED] Could not create Knowledge Source")
        return

    if args.create_only:
        print("\n[INFO] Knowledge Source created. Skipping embedding configuration.")
        print("[INFO] Run without --create-only to add embeddings later")
        return

    print("\n[INFO] Waiting 30 seconds for Foundry IQ to complete initial setup...")
    import time
    time.sleep(30)

    # Add embeddings
    if not add_embedding_skill(ks_name, EMBEDDING_DEPLOYMENT, dimensions=3072):
        print("\n[FAILED] Could not configure embedding skill")
        return

    if not add_vector_field(ks_name, dimensions=3072):
        print("\n[FAILED] Could not configure vector field")
        return

    if not reset_indexer(ks_name):
        print("\n[FAILED] Could not trigger indexer")
        return

    # Success
    print("\n" + "=" * 70)
    print("[SUCCESS] Knowledge Source Created with Embeddings!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print(f"1. Run: uv run python 3_verify_embeddings.py {ks_name}")
    print(f"2. Run: uv run python 4_test_search.py {ks_name}")
    print(f"3. Run: uv run python 5_run_agent.py")
    print()
    print("Resources created:")
    print(f"  - Knowledge Source: {ks_name}")
    print(f"  - Index: {ks_name}-index")
    print(f"  - Skillset: {ks_name}-skillset")
    print(f"  - Indexer: {ks_name}-indexer")
    print()

if __name__ == "__main__":
    main()

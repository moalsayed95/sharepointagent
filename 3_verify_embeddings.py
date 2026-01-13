"""
Verify Embedding Configuration for Knowledge Source

Usage:
    # Use default from config
    uv run python 3_verify_embeddings.py

    # Specify knowledge source
    uv run python 3_verify_embeddings.py employee-onboarding-ks
"""
import os
import sys
import requests
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")

def load_config():
    """Load knowledge sources from config file"""
    config_path = "knowledge_sources.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

def inspect_knowledge_source(ks_name):
    """Check the Knowledge Source configuration"""
    print("=" * 70)
    print("[1] KNOWLEDGE SOURCE CONFIGURATION")
    print("=" * 70)

    url = f"{SEARCH_ENDPOINT}/knowledgesources('{ks_name}')?api-version=2025-11-01-preview"
    headers = {"api-key": SEARCH_ADMIN_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        ks_config = response.json()
        print(f"Knowledge Source: {ks_config.get('name')}")
        print(f"Kind: {ks_config.get('kind')}")
        print(f"Description: {ks_config.get('description')}")
        print()
        return True
    else:
        print(f"[ERROR] Knowledge Source '{ks_name}' not found")
        print(f"Status: {response.status_code}")
        return False

def inspect_index_schema(ks_name):
    """Check if the index has vector fields"""
    index_name = f"{ks_name}-index"
    print("=" * 70)
    print("[2] INDEX SCHEMA (Vector Fields Check)")
    print("=" * 70)

    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}?api-version=2024-07-01"
    headers = {"api-key": SEARCH_ADMIN_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        index_def = response.json()

        # Check for vector fields
        vector_fields = [f for f in index_def.get('fields', [])
                        if f.get('type') == 'Collection(Edm.Single)']

        if vector_fields:
            print(f"[SUCCESS] Found {len(vector_fields)} vector field(s):")
            for field in vector_fields:
                print(f"  - {field['name']} (dimensions: {field.get('dimensions', 'unknown')})")
            print()
            return True
        else:
            print("[WARNING] No vector fields found in index")
            print("This means embeddings are NOT being generated")
            print()
            return False
    else:
        print(f"[ERROR] Index '{index_name}' not found")
        return False

def inspect_skillset(ks_name):
    """Check if there's an embedding skill in the skillset"""
    skillset_name = f"{ks_name}-skillset"
    print("=" * 70)
    print("[3] SKILLSET (Embedding Skill Check)")
    print("=" * 70)

    url = f"{SEARCH_ENDPOINT}/skillsets/{skillset_name}?api-version=2024-07-01"
    headers = {"api-key": SEARCH_ADMIN_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        skillset = response.json()

        # Check for embedding skill
        embedding_skills = [s for s in skillset.get('skills', [])
                           if 'Embedding' in s.get('@odata.type', '')]

        if embedding_skills:
            print(f"[SUCCESS] Found {len(embedding_skills)} embedding skill(s):")
            for skill in embedding_skills:
                print(f"  - Type: {skill['@odata.type']}")
                print(f"    Deployment: {skill.get('deploymentId', 'N/A')}")
                print(f"    Dimensions: {skill.get('dimensions', 'N/A')}")
            print()
            return True
        else:
            print("[WARNING] No embedding skills found in skillset")
            print("This means embeddings are NOT configured")
            print()
            return False
    else:
        print(f"[ERROR] Skillset '{skillset_name}' not found")
        return False

def inspect_indexer(ks_name):
    """Check the indexer configuration"""
    indexer_name = f"{ks_name}-indexer"
    print("=" * 70)
    print("[4] INDEXER STATUS")
    print("=" * 70)

    url = f"{SEARCH_ENDPOINT}/indexers/{indexer_name}/status?api-version=2024-07-01"
    headers = {"api-key": SEARCH_ADMIN_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        status = response.json()
        last_result = status.get('lastResult', {})

        print(f"Indexer: {indexer_name}")
        print(f"Status: {status.get('status')}")
        print(f"Last Result Status: {last_result.get('status')}")
        print(f"Items Processed: {last_result.get('itemsProcessed', 0)}")
        print(f"Items Failed: {last_result.get('itemsFailed', 0)}")

        if last_result.get('errors'):
            print("\nErrors:")
            for error in last_result['errors']:
                print(f"  - {error}")
            return False

        print()
        return last_result.get('status') == 'success'
    else:
        print(f"[ERROR] Indexer '{indexer_name}' not found")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Verify embedding configuration for a Knowledge Source"
    )
    parser.add_argument(
        "ks_name",
        nargs="?",
        help="Knowledge Source name to verify"
    )

    args = parser.parse_args()

    # Determine which knowledge source to verify
    if args.ks_name:
        ks_name = args.ks_name
    else:
        # Use first enabled knowledge source from config
        config = load_config()
        if config and "knowledge_sources" in config:
            enabled_ks = [ks for ks in config["knowledge_sources"] if ks.get("enabled", True)]
            if enabled_ks:
                ks_name = enabled_ks[0]["name"]
            else:
                print("[ERROR] No enabled knowledge sources in config")
                return
        else:
            print("[ERROR] No knowledge source specified")
            print("Usage: uv run python 3_verify_embeddings.py <ks-name>")
            return

    print("\n" + "=" * 70)
    print("EMBEDDING CONFIGURATION INSPECTOR")
    print("=" * 70)
    print(f"Knowledge Source: {ks_name}")
    print("=" * 70)
    print()

    # Run all inspections
    checks = []
    checks.append(("Knowledge Source", inspect_knowledge_source(ks_name)))
    checks.append(("Vector Fields", inspect_index_schema(ks_name)))
    checks.append(("Embedding Skills", inspect_skillset(ks_name)))
    checks.append(("Indexer Status", inspect_indexer(ks_name)))

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")

    print()
    if passed == total:
        print(f"[SUCCESS] All checks passed ({passed}/{total})")
        print("Your Knowledge Source is fully configured with embeddings!")
    else:
        print(f"[WARNING] {passed}/{total} checks passed")
        print()
        print("To fix:")
        print(f"  Run: uv run python 2_create_knowledge_source.py {ks_name}")
    print("=" * 70)

if __name__ == "__main__":
    main()

"""
Test Search on Knowledge Source Index

Usage:
    # Use default from config
    uv run python 4_test_search.py

    # Specify knowledge source
    uv run python 4_test_search.py employee-onboarding-ks

    # Search for specific term
    uv run python 4_test_search.py employee-onboarding-ks "onboarding"
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

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

def search_index(ks_name, search_term="*", top=10):
    """Search the index directly to see if there's any data"""
    index_name = f"{ks_name}-index"

    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(SEARCH_ADMIN_KEY)
    )

    print(f"[SEARCHING INDEX: {index_name}]")
    print(f"Search Term: {search_term}")
    print()

    try:
        # Search
        results = search_client.search(
            search_text=search_term,
            include_total_count=True,
            top=top
        )

        print(f"Total results: {results.get_count()}")
        print()

        doc_found = False
        for i, doc in enumerate(results, 1):
            doc_found = True
            print(f"--- Document {i} ---")
            for key, value in doc.items():
                if key.startswith('@'):  # Skip internal fields
                    continue
                # Truncate long text
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                print(f"{key}: {value}")
            print()

        if not doc_found:
            print("[INFO] No documents found")
            if search_term == "*":
                print("This could mean:")
                print("1. Documents are still being processed")
                print("2. The indexing pipeline has an issue")
                print(f"3. Run: uv run python 3_verify_embeddings.py {ks_name}")

        return doc_found

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Test search on a Knowledge Source index"
    )
    parser.add_argument(
        "ks_name",
        nargs="?",
        help="Knowledge Source name to search"
    )
    parser.add_argument(
        "search_term",
        nargs="?",
        default="*",
        help="Search term (default: * for all documents)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )

    args = parser.parse_args()

    # Determine which knowledge source to search
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
            print("Usage: uv run python 4_test_search.py <ks-name> [search-term]")
            return

    print("\n" + "=" * 70)
    print("KNOWLEDGE SOURCE SEARCH TEST")
    print("=" * 70)
    print(f"Knowledge Source: {ks_name}")
    print("=" * 70)
    print()

    search_index(ks_name, args.search_term, args.top)

if __name__ == "__main__":
    main()

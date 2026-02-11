"""
Run Agent with Azure AI Search (Responses API)

This script uses the Azure OpenAI Responses API with function calling
to query SharePoint-indexed documents via Azure AI Search.

SDK: azure-ai-projects 2.0.0+, openai 2.18.0+
API: Responses API (stateful, multi-turn)

Usage:
    uv run python sharepoint-part/5_run_agent.py
    uv run python sharepoint-part/5_run_agent.py --interactive
"""
import os
import json
import requests
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
INDEX_NAME = "employee-onboarding-ks-index"
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# System instructions for the agent
SYSTEM_INSTRUCTIONS = """You are a helpful SharePoint Assistant for employee onboarding.
ALWAYS use the search_documents function for ANY question about onboarding, policies, or procedures.
Provide clear, concise answers based on the documents you find.
If you cannot find relevant information, say so clearly."""

# Define the search function tool
SEARCH_TOOL = {
    "type": "function",
    "name": "search_documents",
    "description": "Search SharePoint documents for employee onboarding information, policies, and procedures",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documents"
            }
        },
        "required": ["query"]
    }
}


def search_azure_ai_search(query: str) -> str:
    """Execute a search against Azure AI Search and return results"""
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search?api-version=2024-07-01"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_ADMIN_KEY
    }
    
    # Use simple text search (the index fields are: snippet, doc_url, uid)
    payload = {
        "search": query,
        "queryType": "simple",
        "top": 5,
        "select": "snippet,doc_url"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json()
        
        # Format results for the model
        formatted = []
        for doc in results.get("value", []):
            doc_url = doc.get("doc_url", "Unknown source")
            snippet = doc.get("snippet", "")[:1500]  # Limit content length
            formatted.append(f"**Source: {doc_url}**\n{snippet}")
        
        if formatted:
            return "\n\n---\n\n".join(formatted)
        return "No relevant documents found."
        
    except Exception as e:
        return f"Search error: {str(e)}"


def create_client():
    """Create the AIProjectClient and get OpenAI client"""
    print("[SETUP] Initializing Foundry Project Client...")
    
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )
    
    # Get the OpenAI client from Foundry
    client = project_client.get_openai_client()
    
    print(f"    Project: {PROJECT_ENDPOINT}")
    print(f"    Model: {MODEL_DEPLOYMENT_NAME}")
    print(f"    Index: {INDEX_NAME}")
    print()
    
    return client


def chat_with_agent(client, user_question, previous_response_id=None):
    """
    Query the agent using the Responses API with Azure AI Search.
    
    Args:
        client: OpenAI client from AIProjectClient
        user_question: The user's question
        previous_response_id: Optional ID to chain responses for multi-turn
    
    Returns:
        tuple: (response_text, response_id) for chaining
    """
    print(f"\n[USER] {user_question}")
    print()
    
    # Build the request
    request_params = {
        "model": MODEL_DEPLOYMENT_NAME,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": user_question,
        "tools": [SEARCH_TOOL],
    }
    
    # Chain to previous response for multi-turn conversation
    if previous_response_id:
        request_params["previous_response_id"] = previous_response_id
    
    # Create response
    response = client.responses.create(**request_params)
    
    # Check if model wants to call a function
    while response.output and any(o.type == "function_call" for o in response.output):
        # Process function calls
        tool_outputs = []
        
        for output in response.output:
            if output.type == "function_call":
                if output.name == "search_documents":
                    # Parse arguments and execute search
                    args = json.loads(output.arguments)
                    query = args.get("query", user_question)
                    
                    print(f"[SEARCH] Querying: {query}")
                    search_results = search_azure_ai_search(query)
                    
                    tool_outputs.append({
                        "type": "function_call_output",
                        "call_id": output.call_id,
                        "output": search_results
                    })
        
        # Send function results back to get final response
        response = client.responses.create(
            model=MODEL_DEPLOYMENT_NAME,
            previous_response_id=response.id,
            input=tool_outputs
        )
    
    # Extract the text response
    response_text = response.output_text
    
    print(f"[AGENT] {response_text}")
    
    # Show usage stats
    if response.usage:
        print(f"\n[STATS] Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
    
    return response_text, response.id


def run_interactive_chat(client):
    """Run an interactive chat session with the agent"""
    print("\n" + "=" * 60)
    print("SHAREPOINT ASSISTANT (Responses API)")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'new' to start a fresh conversation.")
    print("=" * 60)
    
    previous_response_id = None
    
    while True:
        try:
            user_input = input("\n[YOU] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'new':
                previous_response_id = None
                print("\n[SYSTEM] Started new conversation.")
                continue
            
            _, previous_response_id = chat_with_agent(
                client, 
                user_input, 
                previous_response_id
            )
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


def run_test_questions(client):
    """Run test questions to verify the agent works"""
    test_questions = [
        "How many days are employees allowed to work from home?",
    ]
    
    print("\n" + "=" * 60)
    print("TESTING AGENTIC RAG (Responses API)")
    print("=" * 60)
    
    for question in test_questions:
        chat_with_agent(client, question)
        print("-" * 60)


if __name__ == "__main__":
    import sys
    
    # Create the client
    client = create_client()
    
    # Check for interactive mode flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '-i']:
        run_interactive_chat(client)
    else:
        # Run test questions
        run_test_questions(client)
        
        print("\n" + "=" * 60)
        print("Agent is ready! Run with --interactive for chat mode:")
        print("  uv run python sharepoint-part/5_run_agent.py --interactive")
        print("=" * 60)

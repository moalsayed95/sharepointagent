"""
Run Agent with Responses API (New Agents Experience)

This script uses the NEW Responses API to interact with agents:
- Uses `openai_client.responses.create()` instead of `runs`
- Simpler execution model (send input → get output)
- Creates agents with `create_version()` and `PromptAgentDefinition`

Requirements:
- azure-ai-projects >= 2.0.0b1
- Logged in via: az login

Usage:
    uv run python 6_run_with_responses.py
"""
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchAgentTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
SEARCH_CONN_NAME = os.getenv("SEARCH_CONN_NAME")
INDEX_NAME = "employee-onboarding-ks-index"
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")
AGENT_NAME = "sharepoint-assistant-responses"


def create_or_get_agent(project_client):
    """Create or get an agent using the NEW API with create_version()."""
    
    print("[1] Checking for existing agent...")
    try:
        agent = project_client.agents.get(agent_name=AGENT_NAME)
        print(f"    Found existing agent: {agent.name}")
        return agent
    except Exception:
        print(f"    Agent '{AGENT_NAME}' not found, creating new one...")

    print("\n[2] Getting Azure AI Search connection...")
    connection = project_client.connections.get(name=SEARCH_CONN_NAME)
    print(f"    Connected to: {SEARCH_CONN_NAME}")
    print(f"    Connection ID: {connection.id}")

    print("\n[3] Creating agent with create_version()...")
    
    # Configure the Azure AI Search tool (new format for SDK 2.0)
    search_tool = AzureAISearchAgentTool(
        azure_ai_search=AzureAISearchToolResource(
            indexes=[
                AISearchIndexResource(
                    project_connection_id=connection.id,
                    index_name=INDEX_NAME,
                    query_type=AzureAISearchQueryType.SEMANTIC,
                )
            ]
        )
    )
    
    # Create the agent using the NEW create_version() method
    agent = project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL_DEPLOYMENT_NAME,
            instructions="""You are a helpful SharePoint Assistant for employee onboarding.
            ALWAYS use your Azure AI Search tool for ANY question about onboarding, 
            policies, or procedures. Provide detailed answers.""",
            tools=[search_tool],
        ),
        description="SharePoint assistant using Responses API",
    )
    
    print(f"    Agent created: {agent.name}:{agent.version}")
    return agent


def run_with_responses_api():
    """Use the Responses API to interact with an agent."""
    
    print("=" * 70)
    print("RESPONSES API - NEW AGENTS EXPERIENCE")
    print("=" * 70)
    print()

    # Initialize the project client
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # Create or get the agent
    agent = create_or_get_agent(project_client)

    # Get the OpenAI client for Responses API
    print("\n[4] Getting OpenAI client...")
    openai_client = project_client.get_openai_client()
    print("    OpenAI client ready")

    # Test question
    user_question = "How many days are employees allowed to work from home?"
    
    print(f"\n[5] Sending question via Responses API...")
    print(f"\n[USER] {user_question}")
    print()

    # Use the Responses API - this is the NEW way!
    # No threads, no runs, just a simple request/response
    response = openai_client.responses.create(
        input=[{"role": "user", "content": user_question}],
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )

    print(f"[DEBUG] Response ID: {response.id}")
    print(f"[DEBUG] Response status: {response.status}")
    print()
    print(f"[AGENT] {response.output_text}")
    
    print()
    print("-" * 70)
    print()
    print("SUCCESS! The Responses API is working with Azure AI Search.")
    print()
    print("Key differences from classic API (5_run_agent.py):")
    print("  OLD: create_agent() → threads.create() → messages.create() → runs.create_and_process()")
    print("  NEW: create_version() → responses.create() → response.output_text")


if __name__ == "__main__":
    run_with_responses_api()

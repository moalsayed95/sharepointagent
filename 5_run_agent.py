"""
Run Agent with Azure AI Search

This script uses the Azure AI Agents SDK to create an agent with search capabilities.

Current SDK: azure-ai-projects 1.0.0, azure-ai-agents 1.1.0
API: Classic agents API (create_agent, threads, runs)

NOTE: The NEW agents API (create_version, conversations, responses) is documented
but not yet available in the public Python SDK. This code will be updated when
azure-ai-projects 2.0+ is released.

Usage:
    uv run python 5_run_agent.py
"""
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
SEARCH_CONN_NAME = os.getenv("SEARCH_CONN_NAME")
INDEX_NAME = "employee-onboarding-ks-index"
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

def create_agent():
    """Create or get the Agentic RAG agent with Azure AI Search tool"""

    print("[PHASE 4] Building Agentic RAG System...")
    print()

    # Initialize Foundry Project Client
    # Make sure you're logged in with: az login
    credential = DefaultAzureCredential()
    
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=credential
    )

    print("[1] Getting Azure AI Search connection...")
    # Get the search connection
    connection = project_client.connections.get(name=SEARCH_CONN_NAME)
    print(f"    Connected to: {SEARCH_CONN_NAME}")
    print(f"    Connection ID: {connection.id}")
    print()

    # Check if agent already exists
    agent_name = "sharepoint-assistant"
    existing_agent = None
    
    print("[2] Checking for existing agent...")
    try:
        agents = list(project_client.agents.list_agents())
        for a in agents:
            if a.name == agent_name:
                existing_agent = a
                print(f"    Found existing agent: {a.id}")
                break
    except Exception as e:
        print(f"    Could not list agents: {e}")

    if existing_agent:
        print(f"    Using existing agent: {existing_agent.id}")
        print()
        print("[SUCCESS] Agentic RAG system ready (using existing agent)!")
        print()
        return project_client, existing_agent

    print("[3] Configuring Azure AI Search Tool...")
    # Configure the search tool with semantic search
    search_tool = AzureAISearchTool(
        index_connection_id=connection.id,
        index_name=INDEX_NAME,
        query_type=AzureAISearchQueryType.SEMANTIC
    )
    print(f"    Index: {INDEX_NAME}")
    print(f"    Query Type: SEMANTIC")
    print()

    print("[4] Creating new agent with SharePoint search capability...")
    # Create the agent using the current SDK
    agent = project_client.agents.create_agent(
        model=MODEL_DEPLOYMENT_NAME,
        name=agent_name,
        instructions="""You are a helpful SharePoint Assistant for employee onboarding.
ALWAYS use your Azure AI Search tool for ANY question about onboarding, 
policies, or procedures.""",
        tools=search_tool.definitions,
        tool_resources=search_tool.resources
    )

    print(f"    Agent created: {agent.id}")
    print(f"    Model: {MODEL_DEPLOYMENT_NAME}")
    print()
    print("[SUCCESS] Agentic RAG system ready (new agent created)!")
    print()

    return project_client, agent

def chat_with_agent(project_client, agent, user_question):
    """Run a conversation with the agent"""

    print(f"\n[USER] {user_question}")
    print()

    # Create a thread (conversation)
    thread = project_client.agents.threads.create()

    # Add user message
    project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question
    )

    # Run the agent (it will use the search tool automatically)
    run = project_client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )
    
    print(f"[DEBUG] Run status: {run.status}")
    if run.status == "failed" or str(run.status) == "RunStatus.FAILED":
        print(f"[DEBUG] Last error: {run.last_error}")
        return None

    # Get the response - get ALL messages and find the last assistant message
    messages = list(project_client.agents.messages.list(thread_id=thread.id))
    
    print(f"[DEBUG] Total messages in thread: {len(messages)}")
    
    # Messages are returned in reverse chronological order, so iterate to find assistant responses
    assistant_responses = []
    for message in messages:
        print(f"[DEBUG] Message role: {message.role}")
        if message.role == "assistant":
            for content in message.content:
                if hasattr(content, 'text'):
                    text_content = content.text
                    if hasattr(text_content, 'value'):
                        assistant_responses.append(text_content.value)
                    elif isinstance(text_content, str):
                        assistant_responses.append(text_content)
    
    if assistant_responses:
        # Return the last (most complete) response
        final_response = assistant_responses[0]  # First in list is most recent
        print(f"\n[AGENT] {final_response}")
        return final_response

    print("[DEBUG] No assistant response found")
    return None


if __name__ == "__main__":
    # Create the agent
    project_client, agent = create_agent()

    # Test questions
    test_questions = [
        "How many days are employees allowed to work from home?",
    ]

    print("=" * 60)
    print("TESTING AGENTIC RAG")
    print("=" * 60)

    for question in test_questions:
        chat_with_agent(project_client, agent, question)
        print("-" * 60)

    print("\nAgent is ready! You can now query your SharePoint onboarding documents.")

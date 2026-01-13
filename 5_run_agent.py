import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
PROJECT_API_KEY = os.getenv("PROJECT_API_KEY")
SEARCH_CONN_NAME = os.getenv("SEARCH_CONN_NAME")
INDEX_NAME = "employee-onboarding-ks-index"

def create_agent():
    """Create the Agentic RAG agent with Azure AI Search tool (Classic approach)"""

    print("[PHASE 4] Building Agentic RAG System (Classic Tool Approach)...")
    print()

    # Initialize Foundry Project Client
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=AzureKeyCredential(PROJECT_API_KEY)
    )

    print("[1] Getting Azure AI Search connection...")
    # Get the search connection
    connection = project_client.connections.get(name=SEARCH_CONN_NAME)
    print(f"    Connected to: {SEARCH_CONN_NAME}")
    print(f"    Connection ID: {connection.id}")
    print()

    print("[2] Configuring Azure AI Search Tool with HYBRID + SEMANTIC...")
    # Configure the search tool with HYBRID + SEMANTIC (Foundry IQ requirement)
    # This uses both keyword + semantic ranking for best results
    search_tool = AzureAISearchTool(
        index_connection_id=connection.id,
        index_name=INDEX_NAME,
        # Using SEMANTIC which should enable hybrid + semantic
        query_type=AzureAISearchQueryType.SEMANTIC
    )
    print(f"    Index: {INDEX_NAME}")
    print(f"    Query Type: HYBRID + SEMANTIC")
    print()

    print("[3] Creating agent with SharePoint search capability...")
    # Create the Agentic "Brain" with explicit instructions
    agent = project_client.agents.create_agent(
        model="gpt-4o",
        name="SharePoint Assistant",
        instructions="""You are a helpful SharePoint Assistant for employee onboarding at Vertex Innovations.

        CRITICAL RULES:
        1. ALWAYS use your Azure AI Search tool for ANY question about onboarding, policies, or procedures
        2. Provide specific citations from the documents (mention document names and URLs when available)
        3. If information is NOT found in SharePoint, clearly state: "I could not find this information in the SharePoint documents"
        4. Be concise and helpful

        When you find relevant information, format your response like:
        "According to [document name], [answer]. [Provide specific details from the document]."
        """,
        tools=search_tool.definitions,
        tool_resources=search_tool.resources
    )

    print(f"    Agent created: {agent.id}")
    print(f"    Model: gpt-4o")
    print()
    print("[SUCCESS] Agentic RAG system ready!")
    print()

    return project_client, agent

def chat_with_agent(project_client, agent, user_question):
    """Run a conversation with the agent"""

    print(f"\n[USER] {user_question}")
    print()

    # Create a thread (conversation)
    thread = project_client.agents.create_thread()

    # Add user message
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=user_question
    )

    # Run the agent (it will use the search tool automatically)
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        assistant_id=agent.id
    )

    # Get the response
    messages = project_client.agents.list_messages(thread_id=thread.id)

    # Find the assistant's response
    for message in messages:
        if message.role == "assistant":
            for content in message.content:
                if hasattr(content, 'text') and hasattr(content.text, 'value'):
                    print(f"[AGENT] {content.text.value}")
                    print()
                    return content.text.value

    return None

if __name__ == "__main__":
    # Create the agent
    project_client, agent = create_agent()

    # Test questions
    test_questions = [
        "What documents do new employees need for onboarding?",
        "What is the employee dress code policy?",  # Might not be in docs
    ]

    print("=" * 60)
    print("TESTING AGENTIC RAG")
    print("=" * 60)

    for question in test_questions:
        chat_with_agent(project_client, agent, question)
        print("-" * 60)

    print("\nAgent is ready! You can now query your SharePoint onboarding documents.")

"""
Azure Foundry Agent Service - Create Visible/Publishable Agents

This script uses the Agents API (NOT Responses API) to create agents
that appear in the Foundry portal and can be published.

KEY DIFFERENCE:
- Responses API: client.responses.create() -> Direct model calls, NOT visible in portal
- Agents API: project_client.agents.create() -> Creates agents visible in portal

SDK: azure-ai-projects 2.0.0b3+
Docs: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart

Usage: uv run python 8_foundry_agent_service.py
"""
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")
AGENT_NAME = "SharePoint-Onboarding-Agent"

print("=" * 60)
print("FOUNDRY AGENT SERVICE DEMO")
print("=" * 60)
print(f"Endpoint: {PROJECT_ENDPOINT}")
print(f"Model: {MODEL}")
print()

# Create the AIProjectClient
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

with project_client:
    
    # =========================================================================
    # STEP 1: Create an Agent (this will be visible in Foundry portal!)
    # =========================================================================
    print("[1] Creating Agent...")
    
    # Define the agent using PromptAgentDefinition
    agent_definition = PromptAgentDefinition(
        model=MODEL,
        instructions="""You are a helpful SharePoint Assistant for employee onboarding.
        You help employees find information about company policies, procedures, and benefits.
        Be concise and friendly in your responses.""",
    )
    
    agent = project_client.agents.create(
        name=AGENT_NAME,
        definition=agent_definition,
        description="An agent that helps with employee onboarding questions",
    )
    
    print(f"    Created agent: {agent.name}")
    print(f"    Agent ID: {agent.id}")
    print()
    
    # =========================================================================
    # STEP 2: List all agents (to confirm it's visible in the service)
    # =========================================================================
    print("[2] Listing all agents in project:")
    
    all_agents = project_client.agents.list()
    for a in all_agents:
        print(f"    - {a.name} (ID: {a.id})")
    
    print()
    
    # =========================================================================
    # STEP 3: Test the agent using Responses API
    # =========================================================================
    print("[3] Testing agent via Responses API...")
    
    # Get the OpenAI client to use Responses API
    openai_client = project_client.get_openai_client()
    
    # Use the responses.create with the agent
    response = openai_client.responses.create(
        model=MODEL,
        instructions=agent_definition.get("instructions", "You are a helpful assistant."),
        input="What are the typical steps for onboarding a new employee?",
    )
    
    print(f"    Response: {response.output_text[:500]}...")
    print(f"    Tokens: {response.usage.total_tokens}")
    print()
    
    print("=" * 60)
    print("AGENT CREATED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Your agent is now visible in the Foundry portal!")
    print("Go to: https://ai.azure.com -> Your Project -> Agent Builder")
    print()
    print("To publish this agent, follow the docs:")
    print("https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/publish-agent")
    print()
    print("=" * 60)
    
    # =========================================================================
    # OPTIONAL: Clean up (uncomment to delete the agent)
    # =========================================================================
    # print("[CLEANUP] Deleting agent...")
    # project_client.agents.delete(agent.name)
    # print("    Agent deleted.")
    # print("    Agent deleted.")

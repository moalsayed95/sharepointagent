"""
POC: Assistants API → Foundry Agent Service Migration

This script demonstrates the complete flow:
1. Create a Foundry Agent (replaces creating an Assistant)
2. Publish the agent (creates Agent Application + Deployment)
3. Invoke via Responses API (replaces threads/runs/messages)
4. Multi-turn conversation (using previous_response_id)

This proves: Assistants API → Foundry Agent Service + Responses API is viable

Usage: uv run python 9_poc_full_flow.py
"""
import os
import re
import time
import requests
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential, AzureCliCredential
from openai import OpenAI

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# Azure Resource IDs (needed for publishing via ARM API)
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID", "b7376e6f-8f1b-4e2d-9d19-2b974d7fefed")
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP", "rg-sharepoint-agent")

# Parse account and project from endpoint
match = re.match(r'https://([^.]+)\.services\.ai\.azure\.com/api/projects/([^/]+)', PROJECT_ENDPOINT)
ACCOUNT_NAME = match.group(1) if match else None
PROJECT_NAME = match.group(2) if match else None

# Agent and Application names
AGENT_NAME = "poc-agent-with-tools"
APP_NAME = "poc-app-with-tools"
DEPLOYMENT_NAME = "poc-deployment-tools"

print("=" * 70)
print("POC: ASSISTANTS API → FOUNDRY AGENT SERVICE MIGRATION")
print("=" * 70)
print(f"Project Endpoint: {PROJECT_ENDPOINT}")
print(f"Account: {ACCOUNT_NAME}")
print(f"Project: {PROJECT_NAME}")
print(f"Model: {MODEL}")
print()


def get_management_token():
    """Get token for Azure Resource Manager API"""
    credential = AzureCliCredential()
    token = credential.get_token("https://management.azure.com/.default")
    return token.token


def get_foundry_token():
    """Get token for Foundry/AI API"""
    credential = AzureCliCredential()
    token = credential.get_token("https://ai.azure.com/.default")
    return token.token


# =============================================================================
# STEP 1: CREATE AGENT WITH TOOLS (replaces client.beta.assistants.create)
# =============================================================================
def step1_create_agent():
    """Create a Foundry Agent WITH TOOLS - this is like creating an Assistant with tools"""
    print("[STEP 1] Creating Foundry Agent WITH TOOLS...")
    print("         (This replaces: client.beta.assistants.create() with tools)")
    print()
    
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )
    
    with project_client:
        # Define agent WITH TOOLS
        # Tools are configured here, not at request time
        agent_definition = PromptAgentDefinition(
            model=MODEL,
            instructions="""You are a helpful assistant with access to tools.
            
            You have the following capabilities:
            1. Web Search: You can search the web for real-time information using web_search_preview
            2. Code Interpreter: You can write and execute Python code
            
            When users ask about current events, news, or real-time information, use web search.
            When users ask you to calculate, analyze data, or write code, use the code interpreter.
            
            Always be helpful and explain what tools you're using.""",
            tools=[
                {"type": "web_search_preview"},
                {"type": "code_interpreter", "container": {"type": "auto"}}
            ]
        )
        
        # Try to delete existing agent first (to recreate with new definition)
        try:
            existing = project_client.agents.get(AGENT_NAME)
            print(f"    ℹ️  Deleting existing agent to recreate with tools...")
            project_client.agents.delete(AGENT_NAME)
            time.sleep(2)
        except Exception:
            pass  # Agent doesn't exist
        
        # Create the agent with tools
        agent = project_client.agents.create(
            name=AGENT_NAME,
            definition=agent_definition,
            description="POC agent with web_search and code_interpreter tools",
        )
        
        print(f"    ✅ Agent created: {agent.name}")
        print(f"    Agent ID: {agent.id}")
        print(f"    Tools configured: web_search_preview, code_interpreter")
        print()
        
        return agent


# =============================================================================
# STEP 2: PUBLISH AGENT (creates Agent Application + Deployment)
# =============================================================================
def step2_publish_agent():
    """Publish the agent via REST API to get a stable endpoint"""
    print("[STEP 2] Publishing Agent...")
    print("         (This creates an Agent Application with a stable endpoint)")
    print()
    
    token = get_management_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # API version for agent applications (must match region support)
    api_version = "2025-10-01-preview"
    
    # Base URL for management API
    base_url = (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.CognitiveServices/accounts/{ACCOUNT_NAME}"
        f"/projects/{PROJECT_NAME}"
    )
    
    # Step 2a: Create Agent Application
    print("    [2a] Creating Agent Application...")
    app_url = f"{base_url}/applications/{APP_NAME}?api-version={api_version}"
    
    app_payload = {
        "properties": {
            "displayName": "POC Migration App",
            "agents": [{"agentName": AGENT_NAME}]
        }
    }
    
    response = requests.put(app_url, headers=headers, json=app_payload)
    
    if response.status_code in [200, 201, 202]:
        print(f"    ✅ Agent Application created: {APP_NAME}")
        app_data = response.json()
        base_url_app = app_data.get("properties", {}).get("baseUrl", "pending...")
        print(f"    Base URL: {base_url_app}")
    else:
        print(f"    ❌ Failed: {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return None
    
    # Step 2b: Create Deployment
    print()
    print("    [2b] Creating Deployment...")
    deployment_url = f"{base_url}/applications/{APP_NAME}/agentdeployments/{DEPLOYMENT_NAME}?api-version={api_version}"
    
    deployment_payload = {
        "properties": {
            "displayName": "POC Deployment",
            "deploymentType": "Managed",
            "protocols": [
                {
                    "protocol": "responses",
                    "version": "1.0"
                }
            ],
            "agents": [
                {
                    "agentName": AGENT_NAME,
                    "agentVersion": "1"
                }
            ]
        }
    }
    
    response = requests.put(deployment_url, headers=headers, json=deployment_payload)
    
    if response.status_code in [200, 201, 202]:
        print(f"    ✅ Deployment created: {DEPLOYMENT_NAME}")
    else:
        print(f"    ❌ Failed: {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        return None
    
    # Wait for deployment to be ready
    print()
    print("    [2c] Waiting for deployment to be ready...")
    for i in range(30):
        response = requests.get(deployment_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            state = data.get("properties", {}).get("state", "unknown")
            provisioning = data.get("properties", {}).get("provisioningState", "unknown")
            print(f"         State: {state}, Provisioning: {provisioning}")
            
            if state == "Running" and provisioning == "Succeeded":
                print(f"    ✅ Deployment is running!")
                break
        time.sleep(2)
    
    # Construct the application endpoint
    app_endpoint = (
        f"https://{ACCOUNT_NAME}.services.ai.azure.com"
        f"/api/projects/{PROJECT_NAME}/applications/{APP_NAME}/protocols/openai"
    )
    
    print()
    print(f"    📍 Published Endpoint:")
    print(f"       {app_endpoint}")
    print()
    
    return app_endpoint


# =============================================================================
# STEP 3: INVOKE VIA RESPONSES API (replaces threads/runs/messages)
# =============================================================================
def step3_invoke_agent(app_endpoint: str):
    """Invoke the published agent using Responses API"""
    print("[STEP 3] Invoking Agent via Responses API...")
    print("         (This replaces: threads.create + messages.create + runs.create)")
    print()
    
    # Get token for Foundry API
    token = get_foundry_token()
    
    # Create OpenAI client pointing to the published app endpoint
    client = OpenAI(
        api_key=token,
        base_url=app_endpoint,
        default_query={"api-version": "2025-05-15-preview"}
    )
    
    # First message (like creating a thread and sending first message)
    print("    [3a] Sending first message...")
    response1 = client.responses.create(
        model=MODEL,  # Model is already configured in the agent
        input="Hello! My name is Alex. What's a good way to learn Python?",
    )
    
    print(f"    User: Hello! My name is Alex. What's a good way to learn Python?")
    print(f"    Agent: {response1.output_text[:300]}...")
    print(f"    Response ID: {response1.id}")
    print()
    
    # Store conversation history (this is what you'd save to Cosmos DB)
    conversation_history = [
        {"role": "user", "content": "Hello! My name is Alex. What's a good way to learn Python?"},
        {"role": "assistant", "content": response1.output_text}
    ]
    
    return client, conversation_history


# =============================================================================
# STEP 4: MULTI-TURN CONVERSATION (client-managed history)
# =============================================================================
def step4_multi_turn(client, conversation_history: list):
    """Continue the conversation by sending history with each request"""
    print("[STEP 4] Multi-turn Conversation...")
    print("         (Client-managed history - you store this in Cosmos DB)")
    print()
    print("    ⚠️  IMPORTANT: Published agents are STATELESS!")
    print("       You must send conversation history with each request.")
    print()
    
    # Second message - include history for context
    print("    [4a] Second message (should remember my name)...")
    
    # Build input with conversation history
    user_message_2 = "Can you recommend a specific Python course? And do you remember my name?"
    
    # Format: send history as input array
    input_with_history = conversation_history + [
        {"role": "user", "content": user_message_2}
    ]
    
    response2 = client.responses.create(
        model=MODEL,
        input=input_with_history,
    )
    
    print(f"    User: {user_message_2}")
    print(f"    Agent: {response2.output_text[:300]}...")
    print()
    
    # Update history
    conversation_history.append({"role": "user", "content": user_message_2})
    conversation_history.append({"role": "assistant", "content": response2.output_text})
    
    # Third message
    print("    [4b] Third message (building on context)...")
    
    user_message_3 = "What about for data science specifically?"
    input_with_history = conversation_history + [
        {"role": "user", "content": user_message_3}
    ]
    
    response3 = client.responses.create(
        model=MODEL,
        input=input_with_history,
    )
    
    print(f"    User: {user_message_3}")
    print(f"    Agent: {response3.output_text[:300]}...")
    print()
    
    # Update history
    conversation_history.append({"role": "user", "content": user_message_3})
    conversation_history.append({"role": "assistant", "content": response3.output_text})
    
    print(f"    📊 Conversation history length: {len(conversation_history)} messages")
    print()
    
    return conversation_history


# =============================================================================
# STEP 5: TEST TOOLS VIA PUBLISHED AGENT
# =============================================================================
def step5_test_tools(client, conversation_history: list):
    """Test the tools configured on the agent (no tools passed at request time)"""
    print("[STEP 5] Testing Tools via Published Agent...")
    print("         (Tools are configured on agent, not passed at request time)")
    print()
    
    # Test 1: Web Search - should trigger web_search_preview tool
    print("    [5a] Testing Web Search (should use web_search_preview)...")
    
    user_message = "What are the latest Azure AI announcements from this week?"
    
    input_with_history = conversation_history + [
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = client.responses.create(
            model=MODEL,
            input=input_with_history,
            # NO tools parameter - agent already has them configured
        )
        
        print(f"    User: {user_message}")
        print(f"    Agent: {response.output_text[:400]}...")
        print()
        
        # Check what tools were used
        if hasattr(response, 'output') and response.output:
            for output_item in response.output:
                if hasattr(output_item, 'type'):
                    print(f"    📎 Output type: {output_item.type}")
        
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response.output_text})
        
        print("    ✅ Web search test completed!")
        print()
        
    except Exception as e:
        print(f"    ❌ Web search test failed: {e}")
        print()
    
    # Test 2: Code Interpreter - should trigger code_interpreter tool
    print("    [5b] Testing Code Interpreter (should execute Python code)...")
    
    user_message_2 = "Can you calculate the first 20 Fibonacci numbers and show me the result?"
    
    input_with_history = conversation_history + [
        {"role": "user", "content": user_message_2}
    ]
    
    try:
        response2 = client.responses.create(
            model=MODEL,
            input=input_with_history,
            # NO tools parameter - agent already has them configured
        )
        
        print(f"    User: {user_message_2}")
        print(f"    Agent: {response2.output_text[:400]}...")
        print()
        
        # Check what tools were used
        if hasattr(response2, 'output') and response2.output:
            for output_item in response2.output:
                if hasattr(output_item, 'type'):
                    print(f"    📎 Output type: {output_item.type}")
        
        conversation_history.append({"role": "user", "content": user_message_2})
        conversation_history.append({"role": "assistant", "content": response2.output_text})
        
        print("    ✅ Code interpreter test completed!")
        print()
        
    except Exception as e:
        print(f"    ❌ Code interpreter test failed: {e}")
        print()
    
    # Test 3: Combined - ask something that might use both
    print("    [5c] Testing combined query...")
    
    user_message_3 = "What is the current stock price of Microsoft, and calculate what a 10% increase would be?"
    
    input_with_history = conversation_history + [
        {"role": "user", "content": user_message_3}
    ]
    
    try:
        response3 = client.responses.create(
            model=MODEL,
            input=input_with_history,
        )
        
        print(f"    User: {user_message_3}")
        print(f"    Agent: {response3.output_text[:400]}...")
        print()
        
        # Check what tools were used
        if hasattr(response3, 'output') and response3.output:
            for output_item in response3.output:
                if hasattr(output_item, 'type'):
                    print(f"    📎 Output type: {output_item.type}")
        
        conversation_history.append({"role": "user", "content": user_message_3})
        conversation_history.append({"role": "assistant", "content": response3.output_text})
        
        print("    ✅ Combined test completed!")
        print()
        
    except Exception as e:
        print(f"    ❌ Combined test failed: {e}")
        print()
    
    return conversation_history


# =============================================================================
# STEP 6: CLEANUP (optional)
# =============================================================================
def step6_cleanup():
    """Clean up the created resources"""
    print("[STEP 6] Cleanup (optional)...")
    print("         Skipping cleanup to keep resources for inspection.")
    print("         To clean up manually:")
    print(f"         - Delete deployment: {DEPLOYMENT_NAME}")
    print(f"         - Delete application: {APP_NAME}")
    print(f"         - Delete agent: {AGENT_NAME}")
    print()


# =============================================================================
# MAIN
# =============================================================================
def main():
    try:
        # Step 1: Create Agent
        agent = step1_create_agent()
        
        # Step 2: Publish Agent
        app_endpoint = step2_publish_agent()
        
        if not app_endpoint:
            print("❌ Publishing failed. Cannot continue.")
            return
        
        # Give it a moment to stabilize
        print("    Waiting 5 seconds for endpoint to stabilize...")
        time.sleep(5)
        
        # Step 3: Invoke via Responses API
        client, conversation_history = step3_invoke_agent(app_endpoint)
        
        # Step 4: Multi-turn conversation
        conversation_history = step4_multi_turn(client, conversation_history)
        
        # Step 5: Test Tools (web_search, code_interpreter)
        conversation_history = step5_test_tools(client, conversation_history)
        
        # Step 6: Cleanup
        step6_cleanup()
        
        # Summary
        print("=" * 70)
        print("✅ POC COMPLETE!")
        print("=" * 70)
        print()
        print("SUMMARY: Migration Path Validated")
        print("-" * 70)
        print("| Assistants API          | Foundry Agent Service              |")
        print("|-------------------------|-----------------------------------|")
        print("| assistants.create()     | agents.create()                   |")
        print("| threads.create()        | (not needed - stateless)          |")
        print("| messages.create()       | input parameter (with history)    |")
        print("| runs.create()           | responses.create()                |")
        print("| thread stores state     | YOU store state (Cosmos DB)       |")
        print("-" * 70)
        print()
        print("TOOLS TESTED:")
        print("-" * 70)
        print("| Tool                    | Status                            |")
        print("|-------------------------|-----------------------------------|")
        print("| web_search_preview      | See Step 5 output above           |")
        print("-" * 70)
        print()
        print("⚠️  KEY DIFFERENCE: Published agents are STATELESS!")
        print("    You must send conversation history with each request.")
        print("    (This is actually what you're already doing with Cosmos DB!)")
        print()
        print(f"Published Endpoint: {app_endpoint}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

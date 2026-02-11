"""
POC: Foundry Agent Service with Server-Managed State (Conversations API)

This script demonstrates the ALTERNATIVE approach using:
- Conversations API (server stores conversation history)
- Agent versioning (create_version instead of create)
- No publishing required (agent_reference)

This is CLOSER to Assistants API behavior where the server manages threads.

Compare with: 9_poc_client_managed_state.py (where YOU manage history)

Usage: uv run python 10_poc_server_managed_state.py
"""
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

AGENT_NAME = "poc-conversations-agent"

print("=" * 70)
print("POC: FOUNDRY AGENT WITH SERVER-MANAGED STATE (CONVERSATIONS API)")
print("=" * 70)
print(f"Project Endpoint: {PROJECT_ENDPOINT}")
print(f"Model: {MODEL}")
print()
print("This approach uses:")
print("  - conversations.create() → like threads.create()")
print("  - conversations.items.create() → like messages.create()")
print("  - Server stores conversation history (not you!)")
print()


def main():
    try:
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential) as project_client,
        ):
            # =================================================================
            # STEP 1: CREATE AGENT WITH VERSIONING
            # =================================================================
            print("[STEP 1] Creating Agent with Versioning...")
            print("         (Uses agents.create_version() instead of agents.create())")
            print()
            
            with project_client.get_openai_client() as openai_client:
                
                # Create agent with tools
                agent = project_client.agents.create_version(
                    agent_name=AGENT_NAME,
                    definition=PromptAgentDefinition(
                        model=MODEL,
                        instructions="""You are a helpful assistant with access to tools.
                        
                        You can:
                        1. Search the web for real-time information (web_search_preview)
                        2. Execute Python code (code_interpreter)
                        
                        Always be helpful and remember the conversation context.""",
                        tools=[
                            {"type": "web_search_preview"},
                            {"type": "code_interpreter", "container": {"type": "auto"}}
                        ]
                    ),
                )
                
                print(f"    ✅ Agent created:")
                print(f"       ID: {agent.id}")
                print(f"       Name: {agent.name}")
                print(f"       Version: {agent.version}")
                print()
                
                # =============================================================
                # STEP 2: CREATE CONVERSATION (like threads.create())
                # =============================================================
                print("[STEP 2] Creating Conversation...")
                print("         (This is like threads.create() - SERVER stores history)")
                print()
                
                conversation = openai_client.conversations.create(
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": "Hello! My name is Alex. What's a good way to learn Python?"
                        }
                    ],
                )
                
                print(f"    ✅ Conversation created:")
                print(f"       ID: {conversation.id}")
                print(f"       Initial message: Hello! My name is Alex...")
                print()
                
                # =============================================================
                # STEP 3: GET RESPONSE (using agent_reference)
                # =============================================================
                print("[STEP 3] Getting Response (using agent_reference)...")
                print("         (No publishing needed - reference agent by name)")
                print()
                
                response = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                    input="",  # Input is empty - message was in conversation
                )
                
                print(f"    User: Hello! My name is Alex. What's a good way to learn Python?")
                print(f"    Agent: {response.output_text[:300]}...")
                print()
                
                # =============================================================
                # STEP 4: MULTI-TURN (add message to conversation)
                # =============================================================
                print("[STEP 4] Multi-turn Conversation...")
                print("         (Server remembers context - no need to send history!)")
                print()
                
                # Add second message - SERVER remembers Alex's name!
                print("    [4a] Adding second message (should remember my name)...")
                
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": "Can you recommend a specific course? And do you remember my name?"
                        }
                    ],
                )
                
                response2 = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                    input="",
                )
                
                print(f"    User: Can you recommend a specific course? And do you remember my name?")
                print(f"    Agent: {response2.output_text[:300]}...")
                print()
                
                # Add third message
                print("    [4b] Adding third message (building on context)...")
                
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": "What about for data science specifically?"
                        }
                    ],
                )
                
                response3 = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                    input="",
                )
                
                print(f"    User: What about for data science specifically?")
                print(f"    Agent: {response3.output_text[:300]}...")
                print()
                
                # =============================================================
                # STEP 5: TEST TOOLS
                # =============================================================
                print("[STEP 5] Testing Tools...")
                print()
                
                # Test web search
                print("    [5a] Testing Web Search...")
                
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": "What are the latest Azure AI announcements from this week?"
                        }
                    ],
                )
                
                response4 = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                    input="",
                )
                
                print(f"    User: What are the latest Azure AI announcements?")
                print(f"    Agent: {response4.output_text[:300]}...")
                
                # Check what tools were used
                if hasattr(response4, 'output') and response4.output:
                    for output_item in response4.output:
                        if hasattr(output_item, 'type'):
                            print(f"    📎 Output type: {output_item.type}")
                print()
                
                # Test code interpreter
                print("    [5b] Testing Code Interpreter...")
                
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": "Calculate the first 15 prime numbers using Python code."
                        }
                    ],
                )
                
                response5 = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
                    input="",
                )
                
                print(f"    User: Calculate the first 15 prime numbers using Python code.")
                print(f"    Agent: {response5.output_text[:300]}...")
                
                # Check what tools were used
                if hasattr(response5, 'output') and response5.output:
                    for output_item in response5.output:
                        if hasattr(output_item, 'type'):
                            print(f"    📎 Output type: {output_item.type}")
                print()
                
                # =============================================================
                # STEP 6: CLEANUP
                # =============================================================
                print("[STEP 6] Cleanup...")
                
                openai_client.conversations.delete(conversation_id=conversation.id)
                print(f"    ✅ Conversation deleted: {conversation.id}")
                
                project_client.agents.delete_version(
                    agent_name=agent.name,
                    agent_version=agent.version
                )
                print(f"    ✅ Agent version deleted: {agent.name} v{agent.version}")
                print()
                
                # =============================================================
                # SUMMARY
                # =============================================================
                print("=" * 70)
                print("✅ POC COMPLETE!")
                print("=" * 70)
                print()
                print("COMPARISON: Server-Managed vs Client-Managed State")
                print("-" * 70)
                print("| Assistants API     | Server-Managed (this) | Client-Managed (9_)  |")
                print("|--------------------|-----------------------|----------------------|")
                print("| threads.create()   | conversations.create()| (not needed)         |")
                print("| messages.create()  | conversations.items   | send history array   |")
                print("| Server stores hist | ✅ YES                | ❌ NO (Cosmos DB)    |")
                print("| Publishing needed  | ❌ NO (agent_ref)     | ✅ YES               |")
                print("-" * 70)
                print()
                print("KEY INSIGHT:")
                print("  - Server-Managed: Closer to Assistants API behavior")
                print("  - Client-Managed: More control, but you manage state")
                print()
                print("FOR YOUR MIGRATION:")
                print("  - If you want to keep Cosmos DB → Client-Managed (9_)")
                print("  - If you want server to manage state → Server-Managed (this)")
                print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

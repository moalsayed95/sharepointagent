"""
Azure Foundry Responses API Demo

Uses the AIProjectClient (azure-ai-projects 2.0+) for Foundry-native authentication.

Usage: uv run python 7_foundry_responses_api.py
"""

import os
import base64
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")
PDF_PATH = "dummy-data/gpt-5-protein-synthesis.pdf"

# Setup Foundry Project Client
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

# Get authenticated OpenAI client from Foundry
with project_client.get_openai_client() as client:
    
    print("=== Foundry Responses API Test ===\n")
    
    # Test 1: Simple response
    print("[1] Simple text response")
    response = client.responses.create(
        model=MODEL,
        input="What is the capital of France?",
    )
    print(f"Response: {response.output_text}")
    print(f"Tokens: {response.usage.total_tokens}\n")

    # Test 2: Multi-turn chaining
    print("[2] Multi-turn chaining")
    response2 = client.responses.create(
        model=MODEL,
        previous_response_id=response.id,
        input=[{"role": "user", "content": "What is its population?"}]
    )
    print(f"Follow-up: {response2.output_text}")
    print(f"Tokens: {response2.usage.total_tokens}\n")

    # Test 3: PDF file analysis
    print("[3] PDF file analysis")
    if os.path.exists(PDF_PATH):
        with open(PDF_PATH, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        pdf_response = client.responses.create(
            model=MODEL,
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": os.path.basename(PDF_PATH),
                        "file_data": f"data:application/pdf;base64,{pdf_base64}",
                    },
                    {
                        "type": "input_text",
                        "text": "Summarize this PDF in 3 bullet points.",
                    },
                ],
            }]
        )
        print(f"PDF Summary:\n{pdf_response.output_text}")
        print(f"Tokens: {pdf_response.usage.total_tokens}")
    else:
        print(f"PDF not found: {PDF_PATH}")

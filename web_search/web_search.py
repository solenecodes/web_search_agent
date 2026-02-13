import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

client = AzureOpenAI(
    api_key=api_key,
    api_version="2025-03-01-preview",  # ✅ Version correcte
    azure_endpoint=endpoint
)

response = client.responses.create(
    model=deployment,
    tools=[{"type": "web_search_preview",
            "search_context_size": "high"}],
    input="Latest Azure AI updates"
)

print("\n=== RESPONSE ===")
print(response.output_text)

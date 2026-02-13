import os
import requests
from bs4 import BeautifulSoup
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2025-03-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


def fetch_page_content(url: str, max_chars: int = 10000) -> str:
    """Fetch et extrait le contenu d'une page web"""
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        soup = BeautifulSoup(response.content, 'html.parser')

        # Retirer scripts, styles, etc.
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # Extraire le texte
        text = soup.get_text(separator='\n', strip=True)

        # Limiter la taille
        return text[:max_chars]

    except Exception as e:
        return f"Error fetching {url}: {e}"


def deep_web_search(query: str):
    """Recherche + fetch du contenu complet des pages"""

    print("🔍 Step 1: Finding relevant pages...")

    # Étape 1 : Trouver les URLs pertinentes via web_search
    search_response = client.responses.create(
        model="gpt-4-1",
        tools=[{"type": "web_search_preview"}],
        include=["web_search_call.action.sources"],
        input=query
    )

    # Extraire les URLs
    sources = []
    for item in search_response.output:
        if item.type == "web_search_call":
            sources = item.action.sources or []

    print(f"✅ Found {len(sources)} relevant pages")

    # Étape 2 : Fetch le contenu complet de chaque page
    print("\n📄 Step 2: Fetching full page content...")

    full_contents = []
    for i, url in enumerate(sources[:5], 1):  # Limiter à 5 pages
        print(f"  Fetching [{i}/{min(len(sources), 5)}]: {url}")
        content = fetch_page_content(url)
        full_contents.append({
            "url": url,
            "content": content
        })

    # Étape 3 : Analyser avec GPT en utilisant le contenu complet
    print("\n🤖 Step 3: Analyzing full content with GPT...")

    # Construire le contexte avec contenu complet
    context = "\n\n---PAGE SEPARATOR---\n\n".join([
        f"SOURCE: {item['url']}\n\nFULL CONTENT:\n{item['content']}"
        for item in full_contents
    ])

    # Appel GPT avec le contenu complet
    analysis_response = client.chat.completions.create(
        model="gpt-4-1",
        messages=[
            {
                "role": "system",
                "content": """You are a research analyst.
                You have access to the FULL CONTENT of web pages (not just snippets).
                Provide a comprehensive analysis based on all the information available."""
            },
            {
                "role": "user",
                "content": f"""Based on the FULL CONTENT of these pages:

{context}

Question: {query}

Provide a detailed answer using all the information from the full pages.
Include specific details, quotes, and data that go beyond simple snippets."""
            }
        ],
        max_tokens=2000
    )

    return analysis_response.choices[0].message.content


# Utilisation
if __name__ == "__main__":
    result = deep_web_search(
        "Latest Azure AI updates in February 2026 - provide comprehensive details"
    )

    print("\n" + "=" * 70)
    print("DETAILED ANALYSIS (based on full page content)")
    print("=" * 70)
    print(result)

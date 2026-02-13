"""
HOSTED AGENT - Web Search + Fetch Content
==========================================
Agent qui fait UNIQUEMENT:
1. web_search_preview avec Azure OpenAI pour trouver les URLs
2. Fetch du contenu complet des pages

L'analyse/synthèse est faite par l'agent Foundry qui appelle ce hosted agent.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AzureOpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(
    title="Web Search + Fetch Agent",
    description="Hosted agent: web_search_preview + fetch contenu (pas d'analyse)",
    version="1.0.0"
)


# ============== CONFIGURATION ==============

def get_openai_client():
    """Crée le client Azure OpenAI"""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2025-03-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )


# ============== MODÈLES ==============

class SearchRequest(BaseModel):
    """Requête de recherche"""
    query: str = Field(..., description="La question ou le sujet à rechercher")
    max_pages: Optional[int] = Field(None, description="Nombre max de pages à fetcher (None = toutes)")
    max_chars_per_page: Optional[int] = Field(10000, description="Caractères max par page")


class PageContent(BaseModel):
    """Contenu d'une page"""
    url: str
    content: Optional[str] = None
    success: bool
    error: Optional[str] = None


class SearchResponse(BaseModel):
    """Réponse avec les contenus bruts (pas d'analyse)"""
    query: str
    pages: list[PageContent]
    total_found: int
    total_fetched: int


# ============== FONCTIONS CORE ==============

def fetch_page_content(url: str, max_chars: int = 10000) -> tuple[str, bool, str]:
    """Fetch et extrait le contenu d'une page web."""
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Retirer éléments non pertinents
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        text = soup.get_text(separator='\n', strip=True)
        lines = [line for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        return text[:max_chars], True, None

    except Exception as e:
        return "", False, str(e)


def web_search_find_urls(client: AzureOpenAI, query: str) -> list[str]:
    """
    Étape 1: Utilise Azure OpenAI avec web_search_preview pour trouver les URLs.
    Les URLs sont extraites des annotations url_citation dans la réponse.
    """
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-1")

    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search_preview"}],
        input=query
    )

    # Extraire les URLs depuis les annotations url_citation du message
    urls = []
    seen = set()
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if hasattr(content, 'annotations'):
                    for annotation in content.annotations:
                        if annotation.type == "url_citation" and annotation.url not in seen:
                            urls.append(annotation.url)
                            seen.add(annotation.url)

    return urls


def search_and_fetch(query: str, max_pages: Optional[int] = None, max_chars: int = 10000) -> dict:
    """
    Fonction principale:
    1. web_search_preview pour trouver les URLs
    2. Fetch du contenu complet

    PAS d'analyse - retourne le JSON brut pour Foundry.

    Args:
        max_pages: None = fetcher toutes les pages trouvées
    """
    client = get_openai_client()

    # Étape 1: Recherche web avec le modèle
    urls = web_search_find_urls(client, query)

    # Étape 2: Fetch du contenu en parallèle (max_pages=None → toutes)
    urls_to_fetch = urls if max_pages is None else urls[:max_pages]
    pages = []
    results = {}

    if urls_to_fetch:
        with ThreadPoolExecutor(max_workers=min(10, len(urls_to_fetch))) as executor:
            # Lancer tous les fetches en parallèle
            future_to_url = {
                executor.submit(fetch_page_content, url, max_chars): url
                for url in urls_to_fetch
            }

            # Récupérer les résultats dans l'ordre de complétion
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                content, success, error = future.result()
                results[url] = (content, success, error)

    # Reconstruire la liste dans l'ordre original
    fetched_count = 0
    for url in urls_to_fetch:
        content, success, error = results[url]
        pages.append({
            "url": url,
            "content": content if success else None,
            "success": success,
            "error": error
        })
        if success:
            fetched_count += 1

    return {
        "query": query,
        "pages": pages,
        "total_found": len(urls),
        "total_fetched": fetched_count
    }


# ============== ENDPOINTS ==============

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "web-search-fetch-agent"}


@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    🔍 ENDPOINT PRINCIPAL

    1. Utilise Azure OpenAI + web_search_preview pour trouver les pages
    2. Fetch le contenu complet des pages

    Retourne le JSON brut - l'agent Foundry fait l'analyse.
    """
    try:
        result = search_and_fetch(
            query=request.query,
            max_pages=request.max_pages,
            max_chars=request.max_chars_per_page
        )
        return SearchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Format compatible Azure AI Agent Service
@app.post("/run")
async def run_agent(request: dict):
    """
    Endpoint format Agent Service.
    Retourne le JSON brut avec les contenus des pages.
    """
    try:
        query = (
            request.get("query") or
            request.get("input") or
            request.get("messages", [{}])[-1].get("content", "")
        )

        if not query:
            raise HTTPException(status_code=400, detail="No query provided")

        max_pages = request.get("max_pages")  # None = toutes les pages
        max_chars = request.get("max_chars_per_page", 10000)

        result = search_and_fetch(query, max_pages, max_chars)

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

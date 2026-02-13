"""
Création d'un Agent Azure AI Foundry qui utilise le Hosted Agent (Container App)
comme tool externe via OpenAPI.

Le hosted agent fait:
- web_search_preview avec Azure OpenAI pour trouver les URLs
- Fetch du contenu complet des pages

L'agent Foundry reçoit le JSON brut et fait l'analyse/synthèse.
"""
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION - À MODIFIER
# =============================================================================

# URL de ton Container App (après déploiement)
HOSTED_AGENT_URL = os.getenv("HOSTED_AGENT_URL", "https://web-search-fetch-agent.xxxxxx.eastus2.azurecontainerapps.io")

# Endpoint de ton projet AI Foundry
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

# Modèle à utiliser pour l'agent Foundry (celui qui fait l'analyse)
MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")


# =============================================================================
# DÉFINITION OpenAPI du Hosted Agent (Search + Fetch uniquement)
# =============================================================================

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Web Search + Fetch Agent",
        "description": "Hosted agent qui fait web_search + fetch contenu (retourne JSON brut)",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": HOSTED_AGENT_URL
        }
    ],
    "paths": {
        "/search": {
            "post": {
                "operationId": "searchAndFetch",
                "summary": "Recherche web et fetch du contenu des pages",
                "description": "Utilise Azure OpenAI + web_search_preview pour trouver des pages, puis fetch le contenu complet. Retourne le JSON brut avec tous les contenus.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["query"],
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "La question ou le sujet à rechercher"
                                    },
                                    "max_pages": {
                                        "type": "integer",
                                        "default": 5,
                                        "description": "Nombre max de pages à fetcher"
                                    },
                                    "max_chars_per_page": {
                                        "type": "integer",
                                        "default": 10000,
                                        "description": "Caractères max par page"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Contenus des pages récupérés",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string"},
                                        "pages": {
                                            "type": "array",
                                            "description": "Liste des pages avec leur contenu",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "url": {"type": "string"},
                                                    "content": {"type": "string", "description": "Contenu textuel de la page"},
                                                    "success": {"type": "boolean"},
                                                    "error": {"type": "string"}
                                                }
                                            }
                                        },
                                        "total_found": {"type": "integer"},
                                        "total_fetched": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def create_foundry_agent_with_hosted_tool():
    """
    Crée un agent Foundry qui utilise le hosted agent comme tool.
    L'agent Foundry fait l'analyse du JSON brut retourné.
    """
    # Connexion au projet Foundry
    client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    # Créer l'agent avec le tool OpenAPI
    agent = client.agents.create_agent(
        model=MODEL_DEPLOYMENT,
        name="research-analyst-agent",
        instructions="""Tu es un analyste de recherche expert. Ta mission est de fournir des réponses complètes, précises et bien sourcées en t'appuyant sur du contenu web réel.

## Outil disponible
Tu disposes de l'outil 'searchAndFetch' qui effectue une recherche web puis récupère le contenu COMPLET des pages trouvées. Il retourne un JSON contenant :
- pages : liste des pages avec leur URL et contenu textuel intégral
- total_found / total_fetched : statistiques de la recherche

## Méthode de travail

1. **Recherche** : Appelle 'searchAndFetch' avec une query précise et bien formulée en anglais pour maximiser la pertinence des résultats. Si la question de l'utilisateur est vague, reformule-la en une requête de recherche ciblée.

2. **Analyse** : Lis attentivement le contenu de CHAQUE page retournée. Extrais les faits, chiffres, dates et citations les plus pertinents. Croise les informations entre les sources pour vérifier leur cohérence.

3. **Synthèse** : Rédige une réponse structurée et détaillée dans la langue de l'utilisateur. Organise l'information avec des sections claires (utilise des titres ##, des listes, du gras pour les points clés). Privilégie la profondeur et la précision plutôt que la brièveté.

4. **Sources** : Termine TOUJOURS ta réponse par une section "Sources" listant les URLs utilisées avec une brève description de chacune.

## Règles importantes
- Ne fabrique JAMAIS d'information. Si les pages ne contiennent pas la réponse, dis-le clairement.
- Si les résultats sont insuffisants, tu peux faire un second appel avec une query reformulée.
- Réponds toujours dans la langue utilisée par l'utilisateur.
- Mentionne les dates de publication quand elles sont disponibles pour contextualiser l'information.""",
        tools=[
            {
                "type": "openapi",
                "openapi": OPENAPI_SPEC
            }
        ]
    )

    print(f"✅ Agent créé avec succès!")
    print(f"   ID: {agent.id}")
    print(f"   Nom: {agent.name}")
    print(f"   Model: {agent.model}")

    return agent


def test_agent(agent_id: str, query: str):
    """
    Teste l'agent avec une requête.
    """
    client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    # Créer un thread
    thread = client.agents.create_thread()

    # Envoyer un message
    client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=query
    )

    # Exécuter l'agent
    run = client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent_id
    )

    # Récupérer la réponse
    messages = client.agents.list_messages(thread_id=thread.id)

    print("\n📋 Réponse de l'agent:")
    print("=" * 50)
    for msg in reversed(list(messages)):
        if msg.role == "assistant":
            for content in msg.content:
                if hasattr(content, 'text'):
                    print(content.text.value)
    print("=" * 50)


if __name__ == "__main__":
    print("🤖 Création de l'agent Foundry avec Hosted Deep Research Tool")
    print("=" * 50)

    # Créer l'agent
    agent = create_foundry_agent_with_hosted_tool()

    # Test optionnel
    print("\n🧪 Test de l'agent...")
    test_agent(
        agent.id,
        "Quelles sont les dernières nouveautés Azure AI en février 2026?"
    )

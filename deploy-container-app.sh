#!/bin/bash
# =============================================================================
# Script de déploiement du Hosted Agent sur Azure Container Apps
# =============================================================================

set -e

# Configuration - À MODIFIER
RESOURCE_GROUP="solene-lab"
LOCATION="westeurope"
ACR_NAME="acrsolenewebsearch$(date +%s | tail -c 6)"  # Généré unique
CONTAINER_APP_ENV="cae-agent-env"
CONTAINER_APP_NAME="web-search-fetch-agent"
IMAGE_NAME="web-search-fetch-agent"
IMAGE_TAG="v1"

# Charger les variables depuis .env si présent
if [ -f ".env" ]; then
    echo "📄 Chargement des variables depuis .env..."
    set -a
    source .env
    set +a
fi

# Variables Azure OpenAI (depuis .env ou environnement)
AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}"
AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY:-}"
AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME:-gpt-4-1}"

if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo "❌ ERREUR: Variables Azure OpenAI manquantes!"
    echo "   Ajoute-les dans .env ou exporte-les:"
    echo "   AZURE_OPENAI_ENDPOINT='https://xxx.openai.azure.com'"
    echo "   AZURE_OPENAI_API_KEY='your-key'"
    echo "   AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4-1'"
    exit 1
fi

echo "🚀 Déploiement du Hosted Agent (Search + Fetch) sur Azure Container Apps"
echo "======================================================="
echo "   Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "   Model: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo "   ⚠️  Ce hosted agent fait web_search + fetch (pas d'analyse)"
echo ""

# 1. Vérifier que le Resource Group existe
echo ""
echo "📦 Étape 1: Vérification du Resource Group..."
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo "   ✅ Resource Group '$RESOURCE_GROUP' existe déjà"
else
    echo "❌ Resource Group '$RESOURCE_GROUP' n'existe pas!"
    exit 1
fi

# 2. Créer Azure Container Registry
echo ""
echo "🏗️ Étape 2: Création d'Azure Container Registry '$ACR_NAME'..."
if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "   ✅ ACR '$ACR_NAME' existe déjà"
else
    echo "   📦 Création de l'ACR..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --location $LOCATION
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de la création de l'ACR"
        exit 1
    fi
    echo "   ✅ ACR créé"
fi

# 3. Build et push de l'image
echo ""
echo "🐳 Étape 3: Build et push de l'image Docker..."
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# 4. Créer l'environnement Container Apps (si nécessaire)
echo ""
echo "🌍 Étape 4: Création de l'environnement Container Apps..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none 2>/dev/null || echo "Environnement existe déjà"

# 5. Récupérer les credentials ACR
echo ""
echo "🔑 Étape 5: Récupération des credentials ACR..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# 6. Déployer la Container App avec les secrets Azure OpenAI
echo ""
echo "🚀 Étape 6: Déploiement de la Container App avec secrets..."
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_NAME \
    --registry-password $ACR_PASSWORD \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --secrets "openai-endpoint=$AZURE_OPENAI_ENDPOINT" "openai-key=$AZURE_OPENAI_API_KEY" \
    --env-vars "AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint" "AZURE_OPENAI_API_KEY=secretref:openai-key" "AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME" \
    --query properties.configuration.ingress.fqdn \
    --output tsv

# 7. Récupérer l'URL
echo ""
echo "✅ Déploiement terminé!"
echo ""
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo "======================================================="
echo "🌐 URL de votre Hosted Agent:"
echo "   https://$APP_URL"
echo ""
echo "📋 Endpoints disponibles:"
echo "   GET  https://$APP_URL/health"
echo "   POST https://$APP_URL/search   (endpoint principal)"
echo "   POST https://$APP_URL/run      (format Agent Service)"
echo ""
echo "🧪 Test rapide:"
echo "   curl -X POST https://$APP_URL/search \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"Latest Azure AI updates\"}'"
echo ""
echo "🔗 Pour Foundry, utilise cette URL:"
echo "   HOSTED_AGENT_URL=https://$APP_URL"
echo "======================================================="

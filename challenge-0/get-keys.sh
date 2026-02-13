#!/bin/bash
# ============================================================================
# Web Search Agent Hack - Get Keys and Configure Environment
# ============================================================================
# This script retrieves all necessary keys and endpoints from Azure
# and populates the .env file for the hackathon.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
RESOURCE_GROUP=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --resource-group|-g)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: ./get-keys.sh --resource-group YOUR_RESOURCE_GROUP_NAME"
            exit 1
            ;;
    esac
done

if [ -z "$RESOURCE_GROUP" ]; then
    echo -e "${RED}❌ Error: Resource group is required${NC}"
    echo "Usage: ./get-keys.sh --resource-group YOUR_RESOURCE_GROUP_NAME"
    exit 1
fi

echo -e "${GREEN}🔑 Web Search Agent Hack - Environment Configuration${NC}"
echo "============================================="
echo "  Resource Group: $RESOURCE_GROUP"
echo "============================================="
echo ""

# Check if logged in to Azure
echo -e "${YELLOW}📋 Checking Azure CLI login...${NC}"
if ! az account show &>/dev/null; then
    echo -e "${RED}❌ Not logged in to Azure CLI${NC}"
    echo "   Please run: az login --use-device-code"
    exit 1
fi
echo -e "${GREEN}   ✅ Azure CLI authenticated${NC}"
echo ""

# Get current user info for role assignments
echo -e "${YELLOW}👤 Getting current user info...${NC}"
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")
if [ -z "$USER_OBJECT_ID" ]; then
    echo -e "${YELLOW}   ⚠️ Could not get user object ID (might be a service principal)${NC}"
else
    echo -e "${GREEN}   ✅ User ID: ${USER_OBJECT_ID:0:8}...${NC}"
fi
echo ""

# Get Azure OpenAI details
echo -e "${YELLOW}🤖 Getting Azure OpenAI configuration...${NC}"
OPENAI_NAME=$(az cognitiveservices account list --resource-group $RESOURCE_GROUP --query "[?kind=='OpenAI'].name | [0]" -o tsv)

if [ -z "$OPENAI_NAME" ]; then
    echo -e "${RED}❌ No Azure OpenAI resource found in $RESOURCE_GROUP${NC}"
    exit 1
fi

OPENAI_ENDPOINT=$(az cognitiveservices account show --name $OPENAI_NAME --resource-group $RESOURCE_GROUP --query properties.endpoint -o tsv)
OPENAI_KEY=$(az cognitiveservices account keys list --name $OPENAI_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv)

# Get deployment name
OPENAI_DEPLOYMENT=$(az cognitiveservices account deployment list --name $OPENAI_NAME --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "gpt-4-1")

echo -e "${GREEN}   ✅ OpenAI: $OPENAI_NAME${NC}"
echo -e "${GREEN}   ✅ Endpoint: $OPENAI_ENDPOINT${NC}"
echo -e "${GREEN}   ✅ Deployment: $OPENAI_DEPLOYMENT${NC}"
echo ""

# Get Container Registry details
echo -e "${YELLOW}📦 Getting Container Registry configuration...${NC}"
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -n "$ACR_NAME" ]; then
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
    echo -e "${GREEN}   ✅ ACR: $ACR_LOGIN_SERVER${NC}"
else
    echo -e "${YELLOW}   ⚠️ No Container Registry found${NC}"
    ACR_NAME=""
    ACR_LOGIN_SERVER=""
fi
echo ""

# Get Container Apps Environment
echo -e "${YELLOW}🌐 Getting Container Apps Environment...${NC}"
CONTAINER_APP_ENV=$(az containerapp env list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -n "$CONTAINER_APP_ENV" ]; then
    echo -e "${GREEN}   ✅ Container App Env: $CONTAINER_APP_ENV${NC}"
else
    echo -e "${YELLOW}   ⚠️ No Container Apps Environment found${NC}"
fi
echo ""

# Get AI Foundry Project endpoint
echo -e "${YELLOW}🧠 Getting AI Foundry Project...${NC}"
AI_PROJECT_NAME=$(az ml workspace list --resource-group $RESOURCE_GROUP --query "[?kind=='Project'].name | [0]" -o tsv 2>/dev/null || echo "")

if [ -n "$AI_PROJECT_NAME" ]; then
    # Construct the project endpoint
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    AI_PROJECT_ENDPOINT="https://${AI_PROJECT_NAME}.${LOCATION:-westeurope}.api.azureml.ms"
    echo -e "${GREEN}   ✅ AI Project: $AI_PROJECT_NAME${NC}"
else
    echo -e "${YELLOW}   ⚠️ No AI Foundry Project found${NC}"
    AI_PROJECT_ENDPOINT=""
fi
echo ""

# Assign roles if we have user object ID
if [ -n "$USER_OBJECT_ID" ]; then
    echo -e "${YELLOW}🔐 Assigning required roles...${NC}"

    # Cognitive Services User role for OpenAI
    az role assignment create \
        --assignee $USER_OBJECT_ID \
        --role "Cognitive Services User" \
        --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP" \
        --output none 2>/dev/null || true
    echo -e "${GREEN}   ✅ Cognitive Services User role assigned${NC}"

    # AcrPush role for Container Registry
    if [ -n "$ACR_NAME" ]; then
        ACR_ID=$(az acr show --name $ACR_NAME --query id -o tsv)
        az role assignment create \
            --assignee $USER_OBJECT_ID \
            --role "AcrPush" \
            --scope $ACR_ID \
            --output none 2>/dev/null || true
        echo -e "${GREEN}   ✅ AcrPush role assigned${NC}"
    fi
    echo ""
fi

# Create .env file
echo -e "${YELLOW}📝 Creating .env file...${NC}"
ENV_FILE="../.env"

cat > $ENV_FILE << EOF
# ============================================================================
# Web Search Agent Hack - Environment Configuration
# Generated by get-keys.sh on $(date)
# ============================================================================

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=$OPENAI_DEPLOYMENT

# Azure AI Foundry Project
AZURE_AI_PROJECT_ENDPOINT=$AI_PROJECT_ENDPOINT

# Container Registry
ACR_NAME=$ACR_NAME
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER

# Container Apps
CONTAINER_APP_ENV=$CONTAINER_APP_ENV
RESOURCE_GROUP=$RESOURCE_GROUP
LOCATION=${LOCATION:-westeurope}

# Hosted Agent URL (will be set after deploying the Container App)
HOSTED_AGENT_URL=
EOF

echo -e "${GREEN}   ✅ .env file created at $ENV_FILE${NC}"
echo ""

# Summary
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}✅ Environment configuration complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "${BLUE}📋 Your .env file contains:${NC}"
echo "   - AZURE_OPENAI_ENDPOINT"
echo "   - AZURE_OPENAI_API_KEY"
echo "   - AZURE_OPENAI_DEPLOYMENT_NAME"
echo "   - AZURE_AI_PROJECT_ENDPOINT"
echo "   - ACR_NAME"
echo "   - CONTAINER_APP_ENV"
echo "   - RESOURCE_GROUP"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "   1. Review the .env file: cat ../.env"
echo "   2. Proceed to Challenge 1"
echo ""

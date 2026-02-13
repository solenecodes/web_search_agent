#!/bin/bash
# ============================================================================
# Web Search Agent Hack - Infrastructure Deployment Script
# ============================================================================

set -e

# Default values
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-websearch-hack}"
LOCATION="${LOCATION:-westeurope}"
BASE_NAME="${BASE_NAME:-websearchhack}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Web Search Agent Hack - Infrastructure Deployment${NC}"
echo "============================================="
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Base Name: $BASE_NAME"
echo "============================================="
echo ""

# Check if logged in to Azure
echo -e "${YELLOW}📋 Checking Azure CLI login...${NC}"
if ! az account show &>/dev/null; then
    echo -e "${RED}❌ Not logged in to Azure CLI${NC}"
    echo "   Please run: az login --use-device-code"
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}   ✅ Logged in to: $SUBSCRIPTION${NC}"
echo ""

# Create Resource Group
echo -e "${YELLOW}📦 Step 1: Creating Resource Group...${NC}"
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo -e "${GREEN}   ✅ Resource Group '$RESOURCE_GROUP' already exists${NC}"
else
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    echo -e "${GREEN}   ✅ Resource Group created${NC}"
fi
echo ""

# Deploy Bicep template
echo -e "${YELLOW}🏗️ Step 2: Deploying Azure resources (this may take 5-10 minutes)...${NC}"
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file main.bicep \
    --parameters location=$LOCATION baseName=$BASE_NAME \
    --query "properties.outputs" \
    --output json)

echo -e "${GREEN}   ✅ Deployment completed${NC}"
echo ""

# Extract outputs
OPENAI_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.openAiName.value')
OPENAI_ENDPOINT=$(echo $DEPLOYMENT_OUTPUT | jq -r '.openAiEndpoint.value')
ACR_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerRegistryName.value')
ACR_LOGIN_SERVER=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerRegistryLoginServer.value')
CONTAINER_APP_ENV=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerAppEnvName.value')
AI_PROJECT_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.aiProjectName.value')

echo -e "${YELLOW}📋 Step 3: Deployment Summary${NC}"
echo "============================================="
echo "  OpenAI Name: $OPENAI_NAME"
echo "  OpenAI Endpoint: $OPENAI_ENDPOINT"
echo "  Container Registry: $ACR_LOGIN_SERVER"
echo "  Container App Env: $CONTAINER_APP_ENV"
echo "  AI Project: $AI_PROJECT_NAME"
echo "============================================="
echo ""

echo -e "${GREEN}✅ Infrastructure deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "   1. Run ./get-keys.sh --resource-group $RESOURCE_GROUP"
echo "   2. Verify your .env file is populated"
echo "   3. Proceed to Challenge 1"

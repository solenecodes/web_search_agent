# Challenge 0 - Environment Setup & Resource Deployment

**Expected Duration:** 30 minutes

Welcome to the **Web Search Agent Hack**! In this challenge, you'll set up your development environment and deploy all the Azure resources needed for the subsequent challenges.

By completing this challenge, you will have:
- A configured development environment (GitHub Codespaces or local)
- All necessary Azure resources deployed
- Environment variables configured for the hackathon

---

## 📋 Prerequisites

- An Azure subscription with contributor access
- A GitHub account (for Codespaces)
- Basic familiarity with Azure CLI

---

## 1.1 Fork the Repository

Before you start, **fork this repository** to your GitHub account:

1. Click the `Fork` button in the upper right corner
2. Select your account/organization
3. Clone or open in Codespaces

---

## 1.2 Development Environment

### Option A: GitHub Codespaces (Recommended)

Click the button below to open in GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new)

Select your forked repository and create the Codespace.

### Option B: Local Development

```bash
# Clone your forked repository
git clone https://github.com/YOUR_USERNAME/agent_service_demo.git
cd agent_service_demo

# Install dependencies
pip install -r requirements.txt
```

---

## 1.3 Azure Login

Log in to Azure CLI with your account:

```bash
az login --use-device-code
```

Follow the instructions to authenticate.

Set your subscription (if you have multiple):

```bash
az account set --subscription "YOUR_SUBSCRIPTION_NAME"
```

---

## 1.4 Resource Deployment

### Option A: Manual Deployment via CLI (Recommended)

Run the deployment script:

```bash
cd challenge-0/infra
./deploy.sh
```

Or deploy manually:

```bash
# Set your variables
RESOURCE_GROUP="rg-websearch-hack"
LOCATION="westeurope"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file azuredeploy.json \
    --parameters location=$LOCATION
```

### Option B: Deploy to Azure Button

> ⚠️ **Note:** After forking, update the URL below with your GitHub username.

Once you've pushed to your fork, use this URL format:
```
https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FYOUR_GITHUB_USERNAME%2Fagent_service_demo%2Fmain%2Fchallenge-0%2Finfra%2Fazuredeploy.json
```

---

## 1.5 Verify Resource Creation

Go to the [Azure Portal](https://portal.azure.com/) and verify your Resource Group contains these resources:

| Resource Type | Name | Purpose |
|--------------|------|---------|
| Azure OpenAI | openai-websearch-hack | LLM with web_search_preview |
| AI Foundry Hub | hub-websearch-hack | AI project management |
| AI Foundry Project | project-websearch-hack | Agent development |
| Container Registry | acrwebsearchhack | Container image storage |
| Container Apps Env | cae-websearch-hack | Container hosting |
| Storage Account | stwebsearchhack | AI Foundry storage |

---

## 1.6 Retrieve Keys and Configure Environment

Run the get-keys script to automatically populate your `.env` file:

```bash
cd challenge-0
./get-keys.sh --resource-group rg-websearch-hack
```

This script will:
1. Fetch all necessary keys and endpoints from Azure
2. Assign required roles to your user account
3. Create and populate the `.env` file in the root directory

---

## 1.7 Verify `.env` Setup

Check that your `.env` file contains all required values:

```bash
cat ../.env
```

You should see values for:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_AI_PROJECT_ENDPOINT`
- `ACR_NAME`
- `CONTAINER_APP_ENV`

> ⚠️ **Note:** For convenience, this hack uses key-based authentication. In production, use managed identities and proper network security.

---

## ✅ Success Criteria

Before moving to Challenge 1, verify:

- [ ] All Azure resources are deployed successfully
- [ ] `.env` file is populated with correct values
- [ ] You can run `az account show` without errors
- [ ] Test the OpenAI connection:

```bash
python -c "
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version='2025-03-01-preview',
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)
print('✅ Azure OpenAI connection successful!')
"
```

---

## 🎯 What's Next?

Now that your environment is ready, proceed to **[Challenge 1](../challenge-1/README.md)** where you'll build your first web search agent!

---

## 🆘 Troubleshooting

### "Subscription not found"
```bash
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### "Insufficient permissions"
Ensure you have at least **Contributor** role on the subscription or resource group.

### "OpenAI quota exceeded"
Check your Azure OpenAI quota in the Azure Portal and request an increase if needed.

---

## 📚 Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Foundry](https://ai.azure.com)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)

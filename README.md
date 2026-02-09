# 🤖 AI-102 Quiz Agent - Azure AI Certification Prep

An intelligent quiz application for AI-102 certification preparation, powered by Azure AI Agents SDK and Microsoft Learn MCP integration.

## ✨ Features

- **Dynamic Question Generation**: AI agent generates unique questions each time using Azure AI Agents SDK
- **MCP Integration**: Connects to Microsoft Learn documentation for accurate, up-to-date information
- **Multiple Question Types**:
  - Multiple choice (4 options)
  - True/False
  - Short answer
- **Deep Technical Focus**: SDK specs, quotas, limits, edge cases, and best practices
- **Matrix Theme UI**: Dark cyberpunk aesthetic with Azure blue accents
- **Real-time Scoring**: Track your progress with instant feedback and explanations

## 🎯 AI-102 Topics Covered

- Azure OpenAI Service (SDK, quotas, TPM limits)
- Azure AI Vision & Custom Vision (training limits, SDK)
- Azure Cognitive Search (indexing, skillsets)
- Azure Bot Service (channels, SDK integration)
- Azure AI Language (CLU, intent recognition)
- Azure AI Document Intelligence (layout models)
- Azure AI Foundry & Prompt Flow (agent orchestration)
- Azure Content Safety, Speech, Translator services

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure subscription with AI Foundry project
- Azure CLI installed and logged in

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Azure Setup

**Create Azure AI Foundry Project:**

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name ai102-quiz-rg --location eastus

# Create AI Foundry project via Azure Portal:
# 1. Go to https://ai.azure.com
# 2. Create new project
# 3. Note your connection string or project details
```

**Get your connection string:**
- Go to Azure AI Foundry portal (https://ai.azure.com)
- Select your project
- Go to Settings → Copy connection string

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your Azure credentials:
# Option 1 (Recommended): Use connection string
AZURE_AI_PROJECT_CONNECTION_STRING=your-connection-string-here

# OR Option 2: Use individual credentials
AZURE_SUBSCRIPTION_ID=your-sub-id
AZURE_RESOURCE_GROUP=your-rg-name
AZURE_AI_PROJECT_NAME=your-project-name

# Set your model deployment
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### 4. Run the App

```bash
python app.py
```

Open your browser to: **http://127.0.0.1:5000**

## 🎮 How to Use

1. **Home Page**: Select number of questions (1-20) and optional topic
2. **Generate Quiz**: Click "Generate Quiz & Start" - AI agent creates questions dynamically
3. **Answer Questions**: One question at a time with immediate feedback
4. **View Results**: See explanations and final score

## 🏗️ Architecture

```
User Input → Flask App → Azure AI Agent → MCP (Microsoft Learn) → Question Generation
                ↓                                                           ↓
            Quiz UI ←───────────────── Formatted Questions ←────────────────┘
```

### Components:

- **Flask Backend**: Handles routing, state management
- **Azure AI Agents SDK**: Orchestrates question generation with tools
- **MCP Integration**: Queries Microsoft Learn docs for accuracy
- **Function Tools**: Agent can call `query_microsoft_learn` tool
- **Matrix UI**: Animated canvas background with responsive design

## 📦 Project Structure

```
agent_service_demo/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env               # Your credentials (git-ignored)
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_AI_PROJECT_CONNECTION_STRING` | Azure AI project connection string | Yes (Option 1) |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | Yes (Option 2) |
| `AZURE_RESOURCE_GROUP` | Resource group name | Yes (Option 2) |
| `AZURE_AI_PROJECT_NAME` | AI project name | Yes (Option 2) |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | Optional (default: gpt-4o-mini) |

### Azure Permissions

Ensure your Azure identity has:
- **Azure AI Developer** role on the AI project
- **Cognitive Services OpenAI User** role
- Access to deploy models in Azure OpenAI

## 🐛 Troubleshooting

### Agent Initialization Fails

**Problem**: `❌ Agent initialization failed`

**Solutions**:
1. Verify Azure CLI login: `az login`
2. Check connection string in `.env`
3. Ensure AI Foundry project exists
4. Verify model deployment (gpt-4o-mini) is available

### No Questions Generated

**Problem**: Fallback questions appear instead of AI-generated ones

**Solutions**:
1. Check Azure OpenAI quota and limits
2. Verify internet connectivity for MCP calls
3. Review console logs for specific errors
4. Try reducing number of questions

### MCP Unavailable

**Problem**: `MCP unavailable - using agent knowledge`

**Solutions**:
- This is expected if Microsoft Learn API is slow/unavailable
- Agent will still generate questions using its training data
- Not a critical error - quiz continues normally

## 🌐 MCP Integration

The app integrates with Microsoft Learn documentation:

- **Endpoint**: Microsoft Learn search API
- **Purpose**: Fetch accurate, current Azure AI documentation
- **Fallback**: Agent uses training data if MCP unavailable
- **Tool**: Agent's `query_microsoft_learn` function tool

## 🎨 UI Customization

### Colors:
- **Background**: `#000` (Black)
- **Primary Text**: `#00ff00` (Matrix Green)
- **Accent**: `#0078D4` (Azure Blue)
- **Font**: `'Courier New'` (Monospace)

### Modify Theme:
Edit CSS in `HTML_HOME` and `HTML_QUIZ` template strings in `app.py`

## 📝 Example Questions

**Multiple Choice:**
> What is the default token-per-minute (TPM) limit for Azure OpenAI GPT-3.5-turbo in Standard deployment?
> - A) 1,000 TPM
> - B) 10,000 TPM
> - C) 120,000 TPM ✅
> - D) 240,000 TPM

**True/False:**
> Azure Custom Vision supports training models with less than 5 images per tag.
> False ✅ - Minimum 5 images required per tag

**Short Answer:**
> In Azure Cognitive Search, what is the maximum number of indexes allowed in a Basic tier?
> Answer: 15 ✅

## 🔐 Security Notes

- Never commit `.env` file to git
- Use Azure Key Vault for production secrets
- Rotate credentials regularly
- Review Azure AI Responsible AI guidelines

## 📚 Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure AI Agents SDK](https://learn.microsoft.com/python/api/azure-ai-projects/)
- [AI-102 Certification](https://learn.microsoft.com/certifications/exams/ai-102/)
- [Microsoft Learn MCP](https://learn.microsoft.com/api/mcp)

## 🤝 Contributing

Feel free to enhance the quiz app:
- Add more AI-102 topics
- Improve question variety
- Enhance UI/UX
- Add user authentication
- Implement question history

## 📄 License

MIT License - Feel free to use for your AI-102 certification prep!

---

**Built with ❤️ using Azure AI Agents SDK + Flask + Matrix vibes** 🤖💚

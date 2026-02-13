# 🔍 Web Search Agent Hack

Build an AI Agent with real-time web search capabilities using Azure OpenAI's `web_search_preview` tool and Azure AI Foundry.

## 🎯 What You'll Build

A **Hosted Agent** that:
1. Searches the web using Azure OpenAI's built-in web search
2. Fetches full page content (not just snippets)
3. Returns structured data for analysis by an AI Foundry agent

## 📋 Challenges

| Challenge | Description | Duration |
|-----------|-------------|----------|
| **[Challenge 0](challenge-0/README.md)** | Environment Setup & Resource Deployment | 30 min |
| **[Challenge 1](challenge-1/README.md)** | Build the Web Search API | 45 min |
| **[Challenge 2](challenge-2/README.md)** | Deploy to Azure Container Apps | 30 min |
| **[Challenge 3](challenge-3/README.md)** | Connect to Azure AI Foundry Agent | 45 min |
| **[Challenge 4](challenge-4/README.md)** | Advanced Features & Optimization | 30 min |

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   User Query    │────▶│  AI Foundry Agent    │────▶│  Hosted Agent   │
│                 │     │  (Analysis/Synthesis) │     │  (Web Search)   │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                              │
                                    ┌─────────────────────────┼─────────────────────────┐
                                    │                         │                         │
                                    ▼                         ▼                         ▼
                            ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
                            │   Web Page 1  │         │   Web Page 2  │         │   Web Page N  │
                            │  (Full Text)  │         │  (Full Text)  │         │  (Full Text)  │
                            └───────────────┘         └───────────────┘         └───────────────┘
```

## 🛠️ Technologies

- **Azure OpenAI** - GPT-4 with `web_search_preview` tool
- **Azure AI Foundry** - Agent orchestration
- **Azure Container Apps** - Serverless hosting
- **FastAPI** - Python API framework
- **Python** - Backend development

## 🚀 Quick Start

### Prerequisites
- Azure subscription with contributor access
- GitHub account

### Get Started

1. **Fork this repository**

2. **Open in GitHub Codespaces**

   [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new)

3. **Start with Challenge 0**
   ```bash
   cd challenge-0
   cat README.md
   ```

## 📁 Repository Structure

```
agent_service_demo/
├── challenge-0/           # Environment setup
│   ├── README.md
│   ├── infra/
│   │   ├── main.bicep    # Infrastructure as Code
│   │   └── deploy.sh
│   ├── get-keys.sh       # Environment configuration
│   └── .env.sample
├── challenge-1/           # Build Web Search API (coming soon)
├── challenge-2/           # Deploy to Azure (coming soon)
├── challenge-3/           # AI Foundry integration (coming soon)
├── challenge-4/           # Advanced features (coming soon)
├── web_search/            # Source code
│   ├── hosted_agent_api.py
│   ├── deep_research.py
│   └── create_foundry_agent.py
├── Dockerfile
├── requirements.txt
└── deploy-container-app.sh
```

## 📚 Resources

- [Azure OpenAI Web Search Preview](https://learn.microsoft.com/azure/ai-services/openai/how-to/web-search)
- [Azure AI Foundry](https://ai.azure.com)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🆘 Need Help?

- Check the troubleshooting section in each challenge
- Ask your coach/facilitator
- Open an issue in this repository

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

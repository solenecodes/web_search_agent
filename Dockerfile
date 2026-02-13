FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copier le code de l'API
COPY web_search/hosted_agent_api.py ./web_search/

# Port exposé
EXPOSE 8000

# Healthcheck pour Container Apps
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Lancer l'API
CMD ["uvicorn", "web_search.hosted_agent_api:app", "--host", "0.0.0.0", "--port", "8000"]

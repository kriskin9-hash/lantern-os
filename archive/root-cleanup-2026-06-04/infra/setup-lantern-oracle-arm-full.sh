#!/bin/bash
# Lantern OS - Oracle ARM Ampere A1 Full Setup

set -e

echo "=== Starting Lantern OS Oracle ARM Full Setup ==="

sudo apt update && sudo apt upgrade -y
sudo apt install curl git htop neofetch docker.io docker-compose-v2 -y

mkdir -p ~/lantern-ai
cd ~/lantern-ai

cat > docker-compose.yml << '\''EOF'\''
version: '\''3.9'\''

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    deploy:
      resources:
        limits:
          cpus: '\''3.8'\''
          memory: 22G

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - ENABLE_SIGNUP=false
    depends_on:
      - ollama

volumes:
  ollama:
  open-webui:
EOF

docker compose up -d

echo "Pulling models..."
docker exec -it ollama ollama pull qwen3:14b
docker exec -it ollama ollama pull qwen3-coder:14b
docker exec -it ollama ollama pull qwen3:8b

echo ""
echo "=== LANTERN OS ORACLE ARM SETUP COMPLETE ==="
echo "Open WebUI → http://$(curl -s ifconfig.me):8080"
echo "Ollama API → http://$(curl -s ifconfig.me):11434"

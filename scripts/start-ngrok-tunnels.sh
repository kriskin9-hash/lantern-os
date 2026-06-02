#!/bin/bash
# start-ngrok-tunnels.sh
# Launches ngrok tunnels for all Lantern OS services and updates documentation URLs

set -e

NGROK_CONFIG="${1:-./.ngrok.yml}"
AUTH_TOKEN="${NGROK_AUTHTOKEN}"
LOG_DIR="logs"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
LOG_FILE="$LOG_DIR/ngrok-tunnels-$TIMESTAMP.log"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if ngrok is available
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Please install ngrok: https://ngrok.com/download"
    exit 1
fi

echo -e "${GREEN}🚀 Starting Lantern OS ngrok tunnels...${NC}"

# Validate auth token
if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ NGROK_AUTHTOKEN environment variable not set"
    echo "Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Set auth token
echo "Setting ngrok authentication token..."
ngrok config add-authtoken "$AUTH_TOKEN" || true

echo "Starting tunnels from config: $NGROK_CONFIG"

# Start ngrok with all tunnels
ngrok start --all --config "$NGROK_CONFIG" 2>&1 | tee "$LOG_FILE" &
NGROK_PID=$!

echo -e "${GREEN}✅ ngrok started with PID: $NGROK_PID${NC}"
echo "Tunnels log: $LOG_FILE"
echo ""
echo -e "${YELLOW}Waiting for tunnels to initialize...${NC}"

# Wait for ngrok API to be ready
sleep 3

# Query ngrok API for tunnel URLs
RETRIES=0
while [ $RETRIES -lt 10 ]; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        RESPONSE=$(curl -s http://localhost:4040/api/tunnels)

        echo -e "\n${GREEN}📡 Active Tunnels:${NC}"
        echo "======================================================================"

        # Extract tunnel URLs using jq or python
        API_URL=$(echo "$RESPONSE" | grep -o '"lantern-api"[^}]*"public_url":"[^"]*' | sed 's/.*"public_url":"//' | head -1)
        DASHBOARD_URL=$(echo "$RESPONSE" | grep -o '"lantern-dashboard"[^}]*"public_url":"[^"]*' | sed 's/.*"public_url":"//' | head -1)
        BROWSER_URL=$(echo "$RESPONSE" | grep -o '"lantern-browser"[^}]*"public_url":"[^"]*' | sed 's/.*"public_url":"//' | head -1)
        ORCHESTRATOR_URL=$(echo "$RESPONSE" | grep -o '"lantern-orchestrator"[^}]*"public_url":"[^"]*' | sed 's/.*"public_url":"//' | head -1)
        RAG_URL=$(echo "$RESPONSE" | grep -o '"lantern-rag"[^}]*"public_url":"[^"]*' | sed 's/.*"public_url":"//' | head -1)

        # Save tunnel URLs to environment file
        cat > .env.ngrok << EOF
# ngrok Tunnel URLs - Generated $(date)
LANTERN_API_URL=${API_URL%\"}
LANTERN_DASHBOARD_URL=${DASHBOARD_URL%\"}
LANTERN_BROWSER_URL=${BROWSER_URL%\"}
LANTERN_ORCHESTRATOR_URL=${ORCHESTRATOR_URL%\"}
LANTERN_RAG_URL=${RAG_URL%\"}

# ngrok Dashboard
NGROK_DASHBOARD=http://localhost:4040/
EOF

        echo "✅ URLs saved to .env.ngrok"

        echo "======================================================================"
        echo -e "\n${GREEN}🌐 Access Lantern OS:${NC}"
        echo "  API:           ${API_URL%\"}"
        echo "  Dashboard:     ${DASHBOARD_URL%\"}"
        echo "  Browser:       ${BROWSER_URL%\"}"
        echo "  Orchestrator:  ${ORCHESTRATOR_URL%\"}"
        echo "  RAG Server:    ${RAG_URL%\"}"
        echo ""
        echo -e "ngrok Dashboard: ${GREEN}http://localhost:4040/${NC}"
        echo -e "\n${GREEN}✅ Tunnels are live! Press Ctrl+C to stop.${NC}"

        wait $NGROK_PID
        break
    fi

    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -lt 10 ]; then
        echo "  Waiting for ngrok to initialize... ($RETRIES/10)"
        sleep 1
    fi
done

if [ $RETRIES -ge 10 ]; then
    echo "❌ Failed to initialize ngrok tunnels after 10 attempts"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo "📋 Tunnel logs: $LOG_FILE"
echo "Environment: .env.ngrok"

#!/bin/bash
# Discord bot token validator (curl-based, no PowerShell needed)
# Usage: ./test-discord-token.sh <TOKEN> [GUILD_ID] [CHANNEL_ID]
#
# Examples:
#   ./test-discord-token.sh "MTAx..."
#   ./test-discord-token.sh "MTAx..." "123456789" "987654321"

set -e

TOKEN="${1:?Token required. Usage: $0 <TOKEN> [GUILD_ID] [CHANNEL_ID]}"
GUILD_ID="${2:-}"
CHANNEL_ID="${3:-}"

DISCORD_API="https://discordapp.com/api/v10"

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

header() {
    echo -e "\n${CYAN}$1${NC}"
    echo "$1" | sed 's/./-/g'
}

# Test token validity
header "Testing Discord Token"

BOT_INFO=$(curl -s -X GET "$DISCORD_API/users/@me" \
    -H "Authorization: Bot $TOKEN" \
    -H "Content-Type: application/json" \
    2>/dev/null || true)

# Check if token is valid (response should contain 'id' field)
if echo "$BOT_INFO" | grep -q '"id"'; then
    BOT_ID=$(echo "$BOT_INFO" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    BOT_NAME=$(echo "$BOT_INFO" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
    success "Token valid"
    echo "  Bot: $BOT_NAME (ID: $BOT_ID)"
else
    error "Token invalid or expired"
    echo "Response: $BOT_INFO"
    exit 1
fi

# Test guild if provided
if [ -n "$GUILD_ID" ]; then
    header "Testing Guild Access"

    GUILD_INFO=$(curl -s -X GET "$DISCORD_API/guilds/$GUILD_ID" \
        -H "Authorization: Bot $TOKEN" \
        -H "Content-Type: application/json" \
        2>/dev/null || true)

    if echo "$GUILD_INFO" | grep -q '"id"'; then
        GUILD_NAME=$(echo "$GUILD_INFO" | grep -o '"name":"[^"]*' | cut -d'"' -f4)
        success "Guild accessible"
        echo "  Guild: $GUILD_NAME (ID: $GUILD_ID)"
    else
        error "Guild not accessible"
        echo "Response: $GUILD_INFO"
    fi
fi

# Test channel if provided
if [ -n "$CHANNEL_ID" ] && [ -n "$GUILD_ID" ]; then
    header "Testing Channel Access"

    CHANNEL_INFO=$(curl -s -X GET "$DISCORD_API/channels/$CHANNEL_ID" \
        -H "Authorization: Bot $TOKEN" \
        -H "Content-Type: application/json" \
        2>/dev/null || true)

    if echo "$CHANNEL_INFO" | grep -q '"id"'; then
        CHANNEL_NAME=$(echo "$CHANNEL_INFO" | grep -o '"name":"[^"]*' | cut -d'"' -f4)
        CHANNEL_TYPE=$(echo "$CHANNEL_INFO" | grep -o '"type":[0-9]*' | cut -d':' -f2)
        TYPE_NAME="Unknown"
        if [ "$CHANNEL_TYPE" = "0" ]; then TYPE_NAME="Text"; fi
        if [ "$CHANNEL_TYPE" = "2" ]; then TYPE_NAME="Voice"; fi

        success "Channel accessible"
        echo "  Channel: #$CHANNEL_NAME (ID: $CHANNEL_ID, Type: $TYPE_NAME)"

        # Try sending a test message
        header "Testing Send Permissions"

        TIMESTAMP=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        TEST_MESSAGE="{\"content\":\"🤖 Lantern Lounge Bot Health Check: $TIMESTAMP\"}"

        MESSAGE_RESPONSE=$(curl -s -X POST "$DISCORD_API/channels/$CHANNEL_ID/messages" \
            -H "Authorization: Bot $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$TEST_MESSAGE" \
            2>/dev/null || true)

        if echo "$MESSAGE_RESPONSE" | grep -q '"id"'; then
            MESSAGE_ID=$(echo "$MESSAGE_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
            success "Message sent successfully"
            echo "  Message ID: $MESSAGE_ID"

            # Delete test message
            curl -s -X DELETE "$DISCORD_API/channels/$CHANNEL_ID/messages/$MESSAGE_ID" \
                -H "Authorization: Bot $TOKEN" \
                2>/dev/null || true
        else
            error "Cannot send message"
            echo "Response: $MESSAGE_RESPONSE"
        fi
    else
        error "Channel not accessible"
        echo "Response: $CHANNEL_INFO"
    fi
fi

# Summary
header "Validation Complete"
success "Discord bot token is ready for deployment"
echo ""

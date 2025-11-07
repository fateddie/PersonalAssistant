#!/bin/bash
# ==============================================
# Google Calendar Configuration Helper
# ==============================================
# Interactive script to configure Google Calendar credentials
#
# Usage:
#   ./scripts/configure-calendar.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENV_FILE="config/.env"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Google Calendar Configuration         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: config/.env not found${NC}"
    echo "Run ./scripts/setup.sh first to create it"
    exit 1
fi

echo -e "${BLUE}This script will help you configure Google Calendar integration.${NC}"
echo ""
echo "You'll need:"
echo "  1. Google Cloud Project with Calendar API enabled"
echo "  2. OAuth 2.0 Client ID"
echo "  3. OAuth 2.0 Client Secret"
echo ""
echo "See: docs/CALENDAR_SETUP.md for setup instructions"
echo ""

# Prompt for values
read -p "$(echo -e ${YELLOW}Enter your Google Client ID: ${NC})" CLIENT_ID

if [[ ! "$CLIENT_ID" =~ \.apps\.googleusercontent\.com$ ]]; then
    echo -e "${YELLOW}⚠️  Warning: Client ID should end with .apps.googleusercontent.com${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 1
    fi
fi

read -p "$(echo -e ${YELLOW}Enter your Google Client Secret: ${NC})" CLIENT_SECRET

if [ -z "$CLIENT_SECRET" ]; then
    echo -e "${RED}❌ Error: Client Secret cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Client ID: ${CLIENT_ID}"
echo "  Client Secret: ${CLIENT_SECRET:0:10}...${CLIENT_SECRET: -4}"
echo ""

read -p "$(echo -e ${YELLOW}Is this correct? (y/n) ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# Update .env file
echo ""
echo -e "${BLUE}Updating config/.env...${NC}"

# Check if calendar config already exists
if grep -q "GOOGLE_CALENDAR_ENABLED" "$ENV_FILE"; then
    # Update existing values
    sed -i.bak "s|^GOOGLE_CALENDAR_ENABLED=.*|GOOGLE_CALENDAR_ENABLED=true|" "$ENV_FILE"
    sed -i.bak "s|^GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$CLIENT_ID|" "$ENV_FILE"
    sed -i.bak "s|^GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$CLIENT_SECRET|" "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✅ Updated existing calendar configuration${NC}"
else
    # Add new config section
    cat >> "$ENV_FILE" << EOF

# -----------------------------------------------------
# Google Calendar Configuration (Added: $(date +%Y-%m-%d))
# -----------------------------------------------------
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=$CLIENT_ID
GOOGLE_CLIENT_SECRET=$CLIENT_SECRET
GOOGLE_REDIRECT_URI=http://localhost:8000/calendar/oauth/callback
EOF
    echo -e "${GREEN}✅ Added calendar configuration${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Configuration Complete! ✅             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Restart AskSharon.ai:"
echo -e "   ${YELLOW}./scripts/stop.sh && ./scripts/start.sh${NC}"
echo ""
echo "2. Authenticate with Google:"
echo -e "   ${YELLOW}Open: http://localhost:8000/calendar/auth${NC}"
echo ""
echo "3. Test the integration:"
echo -e "   ${YELLOW}./scripts/test-calendar.sh${NC}"
echo ""

# Offer to restart services
read -p "$(echo -e ${YELLOW}Restart services now? (y/n) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Restarting services...${NC}"
    ./scripts/stop.sh
    ./scripts/start.sh
    echo ""
    echo -e "${GREEN}✅ Services restarted!${NC}"
    echo ""
    echo "Next: Open http://localhost:8000/calendar/auth in your browser"
fi

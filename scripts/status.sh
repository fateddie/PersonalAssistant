#!/bin/bash
# AskSharon.ai - Service Status Check
# Check which services are currently running

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📊 AskSharon.ai Service Status${NC}"
echo -e "${BLUE}================================${NC}"

# Check orchestrator (port 8000)
echo -e "\n${YELLOW}Orchestrator (FastAPI - port 8000):${NC}"
ORCHESTRATOR_PID=$(lsof -ti :8000 || echo "")
if [ -n "$ORCHESTRATOR_PID" ]; then
    echo -e "${GREEN}✓ Running (PID: $ORCHESTRATOR_PID)${NC}"
    echo -e "  URL: http://localhost:8000"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check Assistant API (port 8002)
echo -e "\n${YELLOW}Assistant API (FastAPI - port 8002):${NC}"
API_PID=$(lsof -ti :8002 || echo "")
if [ -n "$API_PID" ]; then
    echo -e "${GREEN}✓ Running (PID: $API_PID)${NC}"
    echo -e "  URL: http://localhost:8002"
    echo -e "  API Docs: http://localhost:8002/docs"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check frontend (port 8501)
echo -e "\n${YELLOW}Frontend (Streamlit - port 8501):${NC}"
FRONTEND_PID=$(lsof -ti :8501 || echo "")
if [ -n "$FRONTEND_PID" ]; then
    echo -e "${GREEN}✓ Running (PID: $FRONTEND_PID)${NC}"
    echo -e "  URL: http://localhost:8501"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Database status
echo -e "\n${YELLOW}Database:${NC}"
if [ -f "assistant/data/memory.db" ]; then
    DB_SIZE=$(du -h assistant/data/memory.db | cut -f1)
    echo -e "${GREEN}✓ Found${NC} (Size: $DB_SIZE)"
else
    echo -e "${RED}✗ Not found${NC}"
fi

# Log files
echo -e "\n${YELLOW}Recent Logs:${NC}"
if [ -f "logs/backend.log" ]; then
    BACKEND_LINES=$(wc -l < logs/backend.log)
    echo -e "  Backend:  ${BACKEND_LINES} lines (tail -f logs/backend.log)"
fi
if [ -f "logs/frontend.log" ]; then
    FRONTEND_LINES=$(wc -l < logs/frontend.log)
    echo -e "  Frontend: ${FRONTEND_LINES} lines (tail -f logs/frontend.log)"
fi

echo -e "\n${BLUE}================================${NC}"

# Summary
if [ -n "$ORCHESTRATOR_PID" ] && [ -n "$API_PID" ] && [ -n "$FRONTEND_PID" ]; then
    echo -e "${GREEN}✓ All 3 services operational${NC}"
elif [ -n "$ORCHESTRATOR_PID" ] || [ -n "$API_PID" ] || [ -n "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}⚠ Partial services running${NC}"
    echo -e "${YELLOW}  To start all: ./scripts/start.sh${NC}"
else
    echo -e "${RED}✗ No services running${NC}"
    echo -e "${YELLOW}  To start: ./scripts/start.sh${NC}"
fi

echo -e "${BLUE}================================${NC}"
echo ""

#!/bin/bash
# AskSharon.ai - Start All Services
# Central startup script for all 3 services

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Project root
cd "$(dirname "$0")/.."

echo -e "${BLUE}🚀 Starting AskSharon.ai${NC}"
echo -e "${BLUE}================================${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}  Run: ./scripts/setup.sh first${NC}"
    exit 1
fi

# Check if processes are already running
ORCHESTRATOR_PID=$(lsof -ti :8000 || echo "")
API_PID=$(lsof -ti :8002 || echo "")
FRONTEND_PID=$(lsof -ti :8501 || echo "")

if [ -n "$ORCHESTRATOR_PID" ] || [ -n "$API_PID" ] || [ -n "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}⚠ Services already running:${NC}"
    [ -n "$ORCHESTRATOR_PID" ] && echo -e "  • Orchestrator (8000): PID $ORCHESTRATOR_PID"
    [ -n "$API_PID" ] && echo -e "  • Assistant API (8002): PID $API_PID"
    [ -n "$FRONTEND_PID" ] && echo -e "  • Frontend (8501): PID $FRONTEND_PID"
    echo -e "${YELLOW}  Run: ./scripts/stop.sh to stop existing services${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Activate virtual environment
source .venv/bin/activate

# Initialize database tables (Phase 3.5 discipline system)
echo -e "\n${YELLOW}[0/3] Initializing database tables...${NC}"
python -c "from assistant.modules.behavioural_intelligence import bil_db_init" 2>/dev/null || true
echo -e "${GREEN}✓ Database tables ready${NC}"

# Helper function to wait for port
wait_for_port() {
    local port=$1
    local max_wait=$2
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if lsof -ti :$port > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    return 1
}

# Start orchestrator (port 8000)
echo -e "\n${YELLOW}[1/3] Starting Orchestrator on port 8000...${NC}"
nohup uvicorn assistant.core.orchestrator:app --host 0.0.0.0 --port 8000 > logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > logs/orchestrator.pid

if ! wait_for_port 8000 10; then
    echo -e "${RED}✗ Orchestrator failed to start. Check logs/orchestrator.log${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Orchestrator started (PID: $ORCHESTRATOR_PID)${NC}"

# Start Assistant API (port 8002)
echo -e "\n${YELLOW}[2/3] Starting Assistant API on port 8002...${NC}"
nohup uvicorn assistant_api.app.main:app --host 0.0.0.0 --port 8002 > logs/assistant_api.log 2>&1 &
API_PID=$!
echo $API_PID > logs/assistant_api.pid

if ! wait_for_port 8002 10; then
    echo -e "${RED}✗ Assistant API failed to start. Check logs/assistant_api.log${NC}"
    kill $ORCHESTRATOR_PID 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}✓ Assistant API started (PID: $API_PID)${NC}"

# Start frontend (port 8501)
echo -e "\n${YELLOW}[3/3] Starting Streamlit frontend on port 8501...${NC}"
nohup streamlit run assistant/modules/voice/main.py --server.port 8501 --server.headless true > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > logs/frontend.pid

if ! wait_for_port 8501 15; then
    echo -e "${RED}✗ Frontend failed to start. Check logs/frontend.log${NC}"
    kill $ORCHESTRATOR_PID 2>/dev/null || true
    kill $API_PID 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Success summary
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✓ All services running!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📡 Access Points:${NC}"
echo -e "  • Orchestrator:   ${GREEN}http://localhost:8000${NC}"
echo -e "  • Assistant API:  ${GREEN}http://localhost:8002${NC}"
echo -e "  • API Docs:       ${GREEN}http://localhost:8002/docs${NC}"
echo -e "  • Frontend UI:    ${GREEN}http://localhost:8501${NC}"
echo ""
echo -e "${BLUE}📊 Process IDs:${NC}"
echo -e "  • Orchestrator:   $ORCHESTRATOR_PID"
echo -e "  • Assistant API:  $API_PID"
echo -e "  • Frontend:       $FRONTEND_PID"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo -e "  • Orchestrator:   logs/orchestrator.log"
echo -e "  • Assistant API:  logs/assistant_api.log"
echo -e "  • Frontend:       logs/frontend.log"
echo ""
echo -e "${YELLOW}To stop services: ./scripts/stop.sh${NC}"
echo -e "${YELLOW}To view logs: tail -f logs/assistant_api.log${NC}"
echo ""

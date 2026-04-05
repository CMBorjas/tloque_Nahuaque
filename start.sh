#!/bin/bash
# Start everything for Tloque Nahuaque
# Usage: ./start.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Tloque Nahuaque...${NC}"

# 1. Activate venv (create if missing)
if [ ! -d "$VENV" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    pip install -q -r "$DIR/requirements.txt" PyQt6 Pillow discord.py python-dotenv 2>/dev/null
else
    source "$VENV/bin/activate"
fi

# 2. Start backend API (port 8000)
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Backend already running on :8000"
else
    echo -e "${GREEN}Starting backend on :8000...${NC}"
    python -m orchestrator.main &
    sleep 2
fi

# 3. Start frontend (port 5173)
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "Frontend already running on :5173"
else
    echo -e "${GREEN}Starting frontend on :5173...${NC}"
    (cd "$DIR/frontend" && npm run dev &) 2>/dev/null
    sleep 2
fi

# 4. Start desktop pet
if pgrep -f "desktop_pet.py" > /dev/null 2>&1; then
    echo "Desktop pet already running"
else
    echo -e "${GREEN}Starting Nahua desktop pet...${NC}"
    python "$DIR/desktop_pet.py" &
fi

echo ""
echo -e "${GREEN}All systems go!${NC}"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Pet:      Nahua is on your screen"
echo ""
echo "To stop everything: ./stop.sh"

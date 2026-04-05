#!/bin/bash
# Stop everything for Tloque Nahuaque

echo "Stopping Tloque Nahuaque..."

kill $(lsof -ti:8000) 2>/dev/null && echo "Backend stopped" || echo "Backend not running"
kill $(lsof -ti:5173) 2>/dev/null && echo "Frontend stopped" || echo "Frontend not running"
pkill -f "desktop_pet.py" 2>/dev/null && echo "Pet stopped" || echo "Pet not running"
launchctl unload ~/Library/LaunchAgents/com.nahua.desktoppet.plist 2>/dev/null

echo "Done."

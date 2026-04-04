#!/bin/bash
# Tloque Nahuaque - Initialization Script

set -e

echo "Starting Tloque Nahuaque setup..."

echo "1. Creating Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "2. Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "3. Verifying Docker setup..."
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker Engine 24.0+."
    exit 1
fi

echo "Setup COMPLETE!"
echo ""
echo "To start the orchestrator API server, run:"
echo "source venv/bin/activate"
echo "python3 -m orchestrator.main"

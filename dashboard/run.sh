#!/bin/bash

# Entobot Enterprise Dashboard Launcher

echo "=========================================="
echo "  Entobot Enterprise Dashboard"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "../.venv" ]; then
    echo "Virtual environment not found. Please run from main project directory:"
    echo "  cd /home/chibionos/r/entobot"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r pyproject.toml"
    exit 1
fi

# Activate virtual environment
source ../.venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null

echo "Starting dashboard server..."
echo "Access at: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run dashboard
python app.py

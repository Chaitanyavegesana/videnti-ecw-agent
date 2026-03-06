#!/bin/bash

# Start all services for Videnti ECW Agent

cd /Users/chaitanya/Desktop/videnti-ecw-agent

echo "🚀 Starting Videnti Services..."
echo ""

# Kill any existing services on ports
echo "Cleaning up existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null

sleep 1

# Track PIDs
echo "Starting services..."

# Terminal 1: eCW Bridge
echo "[1/4] Starting eCW Bridge (port 8001)..."
.venv/bin/python mcp_servers/ecw_bridge/server.py > /tmp/eCW-Bridge-Server.log 2>&1 &
PID_ECW=$!
echo "✓ eCW-Bridge-Server started (PID: $PID_ECW, Port: 8001)"

sleep 2

# Terminal 2: Ollama
echo "[2/4] Starting Ollama Server (port 8000)..."
.venv/bin/python mcp_servers/ollama_server/server.py > /tmp/Ollama-Server.log 2>&1 &
PID_OLLAMA=$!
echo "✓ Ollama-Server started (PID: $PID_OLLAMA, Port: 8000)"

sleep 2

# Terminal 3: Search
echo "[3/4] Starecho "[3/4] Starecho "[3/4] Starecho "[3/4] Starecho "[3/4] Starecho "[3/4] Starechor.echo "[3/4Seaecho "[3/4] Starecho "[3/4] Starecho "[3/choecho "[3/4] Starecho "[3/4] Starecho "[3/4]SEARecho "[3/4] Starecho "[3/4] Starechal 4: React Dasecho "[3/4] Starecho "[3/4] StarecDashecho "[3/4] Starecho "[3/4] Starecho "[pmecho "[3/4] Starecho "[3/4] Starecho2>&1 &echo "[3/4] Starecho "[3/4] Starecho "[oard started (PID: $PID_DASHBOARD, Port: 5173)"

# Save# Save# Sav"$PID_ECW $PID_OLLAMA $PID_SEARCH $PID_DASHBOARD" > .ser# Save# Save# Sav"$PID_ECW $PID_OLLAMA $PID_SEte# Save# Save# Sav"$PID_ECW $PID_OLLAMA $PID_SEARCH $PID_DASHBOARD" > .ser# Save# SBridge: http://# Save# Save# Sav"$PID_ECW $PID_OLLAMA $PID_SEARCH $PID_DA
echo " echo "h: echo " echo "h: host:echo " echo "h: echo " echo "h: host:echo " ecp/eCWecho " echo "h: echo " echo "h: host:echo " echo "h: echo " echo "h: host:echo " eearch-MCP-Server.echo " echo "h: echo " echo "h: host:echo " echo "h:""

# Graceful shutdown on Ctrl+C
trap "bash stop_services.sh" EXIT INT TERM

# Keep script running
while true; do sleep 1; done

#!/bin/bash

echo "🛑 Stopping Videnti Services..."

# Kill by port
echo "Killing processes on ports 8000-8002, 5173..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Kill stray processes
killall -9 python 2>/dev/null
killall -9 npm 2>/dev/null
killall -9 node 2>/dev/null

# Cleanup
rm -f .service_pids

echo "✅ All services stopped"

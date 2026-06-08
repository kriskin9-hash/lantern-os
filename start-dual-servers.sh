#!/bin/bash
# Start two independent Lantern Garage servers

echo "🌙 Starting dual Lantern Garage servers..."
echo ""

# Kill any existing servers on these ports
echo "Cleaning up old processes..."
lsof -i :4177 2>/dev/null | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null || true
lsof -i :4178 2>/dev/null | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null || true
sleep 2

# Start main branch server (port 4177) — MASTER ONLY
echo "📍 Checking out master branch..."
cd /c/Users/alexp/OneDrive/Documents/GitHub/lantern-os
git checkout master
git pull origin master

echo "📍 Starting MAIN branch server on port 4177 (from master)..."
cd /c/Users/alexp/OneDrive/Documents/GitHub/lantern-os/apps/lantern-garage
PORT=4177 npm start &
MAIN_PID=$!

# Start dev/preview branch server (port 4178)
echo "📍 Starting PREVIEW branch server on port 4178..."
PORT=4178 npm start &
DEV_PID=$!

echo ""
echo "✅ Both servers starting in background..."
echo "   🌙 Main (port 4177): http://127.0.0.1:4177"
echo "   🌙 Dev  (port 4178): http://127.0.0.1:4178"
echo ""
echo "PIDs: Main=$MAIN_PID, Dev=$DEV_PID"
echo ""
echo "To stop servers: kill $MAIN_PID $DEV_PID"

wait

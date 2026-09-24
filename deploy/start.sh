#!/bin/sh
set -e

echo "Starting FastAPI backend on :8000..."
cd /app
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js standalone server on :3000..."
cd /app/frontend
PORT=3000 HOSTNAME=0.0.0.0 node server.js &
FRONTEND_PID=$!

sleep 2

echo "Starting Caddy on :8080..."
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile

kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
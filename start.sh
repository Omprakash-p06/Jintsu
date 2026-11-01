#!/usr/bin/env bash
# ==============================================================================
# Reality Check AI (jintru) — One-Command Full-Stack Launcher
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Ensure environment file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "No .env found. Generating from .env.example (mock providers enabled)..."
        cp .env.example .env
    else
        echo "❌ .env file not found. Run ./setup.sh first." >&2
        exit 1
    fi
fi

# Locate Python environment
if [ -x "backend/.venv/bin/uvicorn" ]; then
    UVICORN_BIN="backend/.venv/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
    UVICORN_BIN="uvicorn"
else
    echo "❌ uvicorn not found in backend/.venv. Run ./setup.sh first." >&2
    exit 1
fi

# Locate Node/Pnpm for Frontend
if command -v pnpm >/dev/null 2>&1; then
    FRONTEND_RUNNER="pnpm --prefix frontend dev"
elif command -v npm >/dev/null 2>&1; then
    FRONTEND_RUNNER="npm --prefix frontend run dev"
else
    echo "❌ Neither pnpm nor npm found. Please install Node.js." >&2
    exit 1
fi

echo "=========================================================================="
echo "🚀 Starting Reality Check AI (jintru) System..."
echo "=========================================================================="

# Trap exits to kill background processes cleanly
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "✓ All services stopped. Goodbye!"
}

trap cleanup INT TERM EXIT

# Start Backend API
echo "Starting FastAPI Backend on http://127.0.0.1:8000..."
(
    cd backend
    exec "$ROOT_DIR/$UVICORN_BIN" app.main:app --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# Wait for Backend to become ready
echo "Waiting for Backend health check..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        echo "✓ Backend API is ready!"
        break
    fi
    sleep 0.5
done

# Start Frontend Workbench
echo "Starting Next.js Frontend on http://localhost:3000..."
$FRONTEND_RUNNER &
FRONTEND_PID=$!

echo ""
echo "=========================================================================="
echo "✨ Reality Check AI is LIVE!"
echo "   - Frontend Workbench:   http://localhost:3000"
echo "   - Backend REST API:     http://localhost:8000/api/v1"
echo "   - Interactive Swagger:  http://localhost:8000/docs"
echo "=========================================================================="
echo "Press Ctrl+C to stop all services."
echo ""

# Keep alive and monitor child processes
while true; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "❌ Backend process died unexpectedly."
        exit 1
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "❌ Frontend process died unexpectedly."
        exit 1
    fi
    sleep 2
done

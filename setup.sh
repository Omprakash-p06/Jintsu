#!/usr/bin/env bash
# ==============================================================================
# Reality Check AI (jintru) — One-Command Project Setup
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=== [1/5] Checking System Prerequisites ==="

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Python $PY_VER found"
else
    echo "❌ Python 3 is required but not installed." >&2
    exit 1
fi

# Check Node
if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node -v)
    echo "✓ Node.js $NODE_VER found"
else
    echo "❌ Node.js is required but not installed." >&2
    exit 1
fi

echo ""
echo "=== [2/5] Initializing Environment Configuration ==="
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example (mock providers enabled by default)..."
    cp .env.example .env
    echo "✓ Created .env"
else
    echo "✓ Existing .env file found"
fi

echo ""
echo "=== [3/5] Setting up Python Virtual Environment & Dependencies ==="
if [ ! -d "backend/.venv" ]; then
    echo "Creating backend virtualenv in backend/.venv..."
    python3 -m venv backend/.venv
fi

PYTHON_BIN="backend/.venv/bin/python"
PIP_BIN="backend/.venv/bin/pip"

"$PIP_BIN" install --upgrade pip setuptools wheel
"$PIP_BIN" install -e "backend[dev]"
echo "✓ Backend Python dependencies installed"

echo ""
echo "=== [4/5] Setting up Frontend Dependencies ==="
if command -v pnpm >/dev/null 2>&1; then
    echo "Installing frontend dependencies with pnpm..."
    pnpm --prefix frontend install
else
    echo "Installing frontend dependencies with npm..."
    npm --prefix frontend install
fi
echo "✓ Frontend dependencies installed"

echo ""
echo "=== [5/5] Initializing Database & Running Smoke Tests ==="
mkdir -p data
"$PYTHON_BIN" -c "
import asyncio
from app.db.database import Database
async def init():
    db = Database('data/jintru.db')
    await db.init_db()
    print('✓ SQLite WAL database initialized at data/jintru.db')
asyncio.run(init())
"

"$PYTHON_BIN" -m pytest backend/tests/unit/test_schemas.py -q
echo "✓ Backend smoke tests passed"

echo ""
echo "=========================================================================="
echo "🎉 Setup complete! You can now start the entire application with:"
echo "   ./start.sh"
echo "   or"
echo "   make dev"
echo "=========================================================================="

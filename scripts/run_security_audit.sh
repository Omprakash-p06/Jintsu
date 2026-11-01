#!/usr/bin/env bash
# Security audit script for Reality Check AI (jintru)
# Verifies SEC-01: semgrep SAST, pip-audit dependencies, and npm frontend audit.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== [1/3] Running Semgrep SAST Scan on backend/app/ ==="
if [ -x "backend/.venv/bin/semgrep" ]; then
    SEMGREP_BIN="backend/.venv/bin/semgrep"
else
    SEMGREP_BIN="semgrep"
fi
"$SEMGREP_BIN" scan --config auto backend/app/
echo "✓ Semgrep SAST scan completed cleanly."

echo ""
echo "=== [2/3] Running Python Dependency Vulnerability Audit (pip-audit) ==="
if [ -x "backend/.venv/bin/pip-audit" ]; then
    PIPAUDIT_BIN="backend/.venv/bin/pip-audit"
else
    PIPAUDIT_BIN="pip-audit"
fi
"$PIPAUDIT_BIN"
echo "✓ Python dependencies clean of known vulnerabilities."

echo ""
echo "=== [3/3] Running Frontend Dependency Vulnerability Audit (npm audit) ==="
npm --prefix frontend audit --audit-level=high
echo "✓ Frontend dependencies clean of high/critical vulnerabilities."

echo ""
echo "=========================================="
echo "✓ All security audits passed successfully!"
echo "=========================================="

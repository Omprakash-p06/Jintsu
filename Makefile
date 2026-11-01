# ==============================================================================
# Reality Check AI (jintru) — Developer Makefile
# ==============================================================================

.PHONY: help setup dev start backend frontend test eval audit lint typecheck build clean

help:
	@echo "Reality Check AI (jintru) Commands:"
	@echo "  make setup      - Install all dependencies (backend venv + frontend pnpm)"
	@echo "  make start      - Launch both backend and frontend services simultaneously"
	@echo "  make dev        - Alias for make start"
	@echo "  make backend    - Run FastAPI backend only (http://127.0.0.1:8000)"
	@echo "  make frontend   - Run Next.js frontend only (http://localhost:3000)"
	@echo "  make test       - Run all backend unit & integration tests (97 tests)"
	@echo "  make eval       - Run offline factuality and SLA latency benchmark suite"
	@echo "  make audit      - Run security scans (Semgrep SAST, pip-audit, npm audit)"
	@echo "  make lint       - Run Ruff Python linter"
	@echo "  make typecheck  - Run Pyright Python typecheck and TypeScript typecheck"
	@echo "  make build      - Build Next.js production frontend"
	@echo "  make clean      - Clean temporary files, caches, and test artifacts"

setup:
	./setup.sh

start:
	./start.sh

dev: start

backend:
	cd backend && ../backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	pnpm --prefix frontend dev

test:
	backend/.venv/bin/pytest backend/tests

eval:
	backend/.venv/bin/python evals/run_evals.py --cases evals/cases.jsonl

audit:
	bash scripts/run_security_audit.sh

lint:
	backend/.venv/bin/ruff check backend/ app/

typecheck:
	backend/.venv/bin/pyright -p backend
	pnpm --prefix frontend run typecheck

build:
	pnpm --prefix frontend run build

clean:
	rm -rf data/*.db-shm data/*.db-wal
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

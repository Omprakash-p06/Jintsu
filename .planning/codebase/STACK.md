---
last_mapped_commit: 168e6fe06a5dbb0cb5faa57eaa2b32b26587f020
last_mapped_at: 2026-11-02
---
# Technology Stack

**Analysis Date:** 2026-11-02

## Languages

**Primary:**
- Python `>=3.12` - Backend verification pipeline, API server, database abstraction, provider clients (`backend/pyproject.toml`, `backend/app/`)
- TypeScript `5.7.3` - Frontend user interface, API client, workbench application, Playwright end-to-end tests (`frontend/package.json`, `frontend/tsconfig.json`)

**Secondary:**
- Shell (Bash) - Security audit tooling, CI/CD utility scripts (`scripts/run_security_audit.sh`)
- CSS (Tailwind CSS v4) - UI styling and design system tokens (`frontend/app/globals.css`)
- JSON / JSONL - Offline evaluation benchmarks, test cases, configuration manifests (`evals/cases.jsonl`, `frontend/components.json`)

## Runtime

**Environment:**
- Python 3.12+ (CPython)
- Node.js `>=20` / Node.js 24 runtime support
- pnpm `9.15.0` package manager for frontend

**Package Manager:**
- Backend: `pip` / `uv` / `hatchling` via PEP 621 (`backend/pyproject.toml`)
- Frontend: `pnpm` (Corepack / `packageManager: pnpm@9.15.0` in `frontend/package.json`)
- Lockfiles: `frontend/pnpm-lock.yaml` (present), `swe-sweep/uv.lock` (present)

## Frameworks

**Core:**
- FastAPI `>=0.115.0,<1.0.0` - Backend asynchronous REST API framework (`backend/app/main.py`, `backend/app/api/routes.py`)
- Uvicorn `[standard]>=0.30.0` - High-performance ASGI web server (`backend/pyproject.toml`)
- Pydantic `>=2.9.0` & Pydantic-Settings `>=2.5.0` - Schema enforcement, strict JSON Schema generation, environment configuration (`backend/app/api/schemas.py`, `backend/app/core/config.py`)
- Next.js `16.4.3` (App Router) - Frontend React application framework (`frontend/package.json`, `frontend/app/layout.tsx`, `frontend/app/page.tsx`)
- React `19.x` & React-DOM `19.x` - Modern component architecture with server/client boundaries (`frontend/package.json`)
- Tailwind CSS `^4.3.3` with `@tailwindcss/postcss` `^4.3.3` - Modern atomic CSS styling framework (`frontend/postcss.config.mjs`)
- shadcn/ui & Radix/Base UI (`@base-ui/react` `^1.5.0`, `class-variance-authority` `^0.7.1`, `lucide-react` `^1.16.0`) - Accessible component primitives

**Testing:**
- Pytest `>=8.3.0` & Pytest-Asyncio `>=0.24.0` - Asynchronous backend unit and integration test runner (`backend/tests/`)
- Playwright `@playwright/test` `^1.64.1` - Cross-browser end-to-end automation (`frontend/tests/e2e/workbench.spec.ts`)
- Semgrep `>=1.80.0` - Static application security testing (SAST) (`scripts/run_security_audit.sh`)
- Pip-Audit `>=2.7.0` - Python dependency vulnerability scanner (`scripts/run_security_audit.sh`)
- Pyright `>=1.1.380` - Static type checking for Python (`backend/pyproject.toml`)
- Ruff `>=0.6.0` - Fast Python linter and code formatter (`backend/pyproject.toml`)

**Build/Dev:**
- Hatchling - PEP 517 build backend for packaging (`backend/pyproject.toml`)
- PostCSS `8.5` - CSS processing pipeline (`frontend/postcss.config.mjs`)
- TypeScript `5.7.3` Compiler (`tsc`) (`frontend/tsconfig.json`)

## Key Dependencies

**Critical:**
- `httpx>=0.27.0`: Fully asynchronous HTTP client used for external search and LLM synthesis calls with strict timeout controls (`backend/app/providers/brave.py`, `backend/app/providers/meta.py`)
- `aiosqlite>=0.20.0`: Non-blocking SQLite adapter powering the persistent local verification history and auditing store (`backend/app/db/database.py`)
- `clsx` & `tailwind-merge`: Class variance utilities for conditional styling (`frontend/lib/utils.ts`)

**Infrastructure:**
- SQLite 3 (WAL mode, `PRAGMA synchronous = NORMAL`, `PRAGMA busy_timeout = 5000`): Zero-infrastructure ACID persistence store (`backend/app/db/database.py`)

## Configuration

**Environment:**
- Configured via `.env` file and environment variables mapped via Pydantic `BaseSettings` (`backend/app/core/config.py`)
- Frontend environment configured via Next.js `process.env.NEXT_PUBLIC_API_BASE_URL` (`frontend/lib/api.ts`)

**Key Configurations Required:**
- `BRAVE_API_KEY`: API access key for Brave Search API (or set `USE_MOCK_PROVIDERS=True` for offline/mock mode)
- `META_API_KEY`: API token for Meta / Llama model synthesis provider
- `META_API_BASE_URL`: Endpoint URL for LLM provider (default: `https://api.meta.ai/v1`)
- `META_MODEL`: LLM model ID (default: `muse-spark-1.3`)
- `DATABASE_PATH`: SQLite database file path (default: `data/jintru.db`)
- `REQUEST_DEADLINE_SECONDS`: Overall monotonic verification SLA budget ceiling (default: `8.0`)
- `BRAVE_RETRIEVAL_MODE`: Search format mode (`"snippets"` or `"context"`, default: `"snippets"`)
- `USE_MOCK_PROVIDERS`: Offline/development deterministic mock provider toggle (`False` by default)

**Build:**
- `backend/pyproject.toml`: Build configuration, Pyright rules, Ruff rules, Pytest settings
- `frontend/package.json`: NPM package metadata and lifecycle scripts
- `frontend/tsconfig.json`: TypeScript compiler options (`target: ES2017`, `moduleResolution: bundler`, `strict: true`)
- `frontend/components.json`: Shadcn component library configuration

## Platform Requirements

**Development:**
- Linux / macOS / WSL2 environment
- Python 3.12+ virtualenv (`python3 -m venv .venv`)
- Node.js 20+ and pnpm 9+
- SQLite 3 with WAL support

**Production:**
- Linux container (Docker / OCI) with CPython 3.12 runtime and Node.js reverse proxy or static export
- Local persistent volume mount for `data/jintru.db`
- Outbound HTTPS network access to `api.search.brave.com` and `api.meta.ai` (or configured LLM base URL)

---

*Stack analysis: 2026-11-02*

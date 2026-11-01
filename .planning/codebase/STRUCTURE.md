---
last_mapped_commit: b77aa778b9b4a8b8ba1996061b3ee591626cb1d1
last_mapped_at: 2026-11-02
---
# Codebase Structure

**Analysis Date:** 2026-11-02

## Directory Layout

```
/home/omprakash/Documents/jintru/
├── backend/                             # Python FastAPI backend application
│   ├── app/                             # Core application package
│   │   ├── api/                         # REST API routes and Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── routes.py                # Endpoint definitions (/verifications, /health)
│   │   │   └── schemas.py               # Request, response, and domain models
│   │   ├── core/                        # Configuration and error primitives
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # BaseSettings and environment mappings
│   │   │   └── errors.py                # Typed domain exceptions (503, 504, 499)
│   │   ├── db/                          # Database connection and persistence
│   │   │   ├── __init__.py
│   │   │   └── database.py              # Async SQLite persistence with WAL & retry
│   │   ├── providers/                   # External search and LLM synthesis clients
│   │   │   ├── __init__.py              # Provider factory getters
│   │   │   ├── base.py                  # Abstract SearchProvider and ModelProvider
│   │   │   ├── brave.py                 # Brave Search API integration
│   │   │   ├── meta.py                  # Meta / OpenAI-compatible LLM client
│   │   │   └── mock.py                  # Deterministic offline mock providers
│   │   ├── services/                    # Modular verification services layer
│   │   │   ├── __init__.py              # Re-exports core verification services
│   │   │   ├── screening.py             # Gate A conservative pre-retrieval screening
│   │   │   ├── clustering.py            # Source domain clustering & wire service mapping
│   │   │   ├── citations.py             # Verbatim excerpt quote & citation validation
│   │   │   ├── policy.py                # Deterministic verdict policy & limitations
│   │   │   ├── cache.py                 # Persistent query caching for search retrieval
│   │   │   └── verification.py          # 8.0s monotonic SLA VerificationPipeline orchestrator
│   │   └── main.py                      # FastAPI app initialization, lifespan, CORS
│   ├── pyproject.toml                   # Python dependencies, Ruff, Pyright, Pytest config
│   ├── Dockerfile                       # Containerized backend build
│   └── tests/                           # Backend test suite (97 tests)
│       ├── conftest.py                  # Shared fixtures and mock configurations
│       ├── integration/                 # End-to-end API and concurrency tests
│       │   ├── test_api.py              # API endpoint integration tests
│       │   └── test_concurrency.py      # Multi-worker async SQLite lock tests
│       └── unit/                        # Isolated unit tests
│           ├── test_budget.py           # 8.0s monotonic SLA budget & guard tests
│           ├── test_citations.py        # Strict verbatim citation validation tests
│           ├── test_classification.py   # Gate A empirical screening tests
│           ├── test_db.py               # Database CRUD and retry logic tests
│           ├── test_evals_offline.py    # Offline evaluation threshold assertions
│           ├── test_pipeline.py         # Verification pipeline execution tests
│           ├── test_policy.py           # Application verdict policy matrix tests
│           ├── test_providers.py        # Provider error handling and parsing tests
│           ├── test_schemas.py          # Schema validation tests
│           └── test_swe_sweep_bugs.py   # Regressions discovered during SWE-sweep
├── frontend/                            # Next.js React workbench application
│   ├── app/                             # App Router layout and pages
│   │   ├── globals.css                  # Global styles and Tailwind v4 directives
│   │   ├── layout.tsx                   # Root HTML shell and metadata
│   │   └── page.tsx                     # Full verification workbench user interface
│   ├── components/                      # UI components
│   │   ├── ui/                          # Shadcn UI primitives
│   │   │   └── button.tsx               # Accessible button component
│   │   └── components.json              # Shadcn configuration
│   ├── lib/                             # Shared frontend utilities and clients
│   │   ├── api.ts                       # Typed REST client with error envelopes
│   │   └── utils.ts                     # Tailwind class merging helpers (cn)
│   ├── package.json                     # Frontend dependencies and npm scripts
│   ├── playwright.config.ts             # Playwright E2E configuration
│   ├── postcss.config.mjs               # PostCSS & Tailwind v4 plugin config
│   ├── next.config.mjs                  # Proxy rewrites and CSP security headers
│   ├── Dockerfile                       # Multi-stage containerized frontend build
│   ├── tests/                           # Frontend automated tests
│   │   └── e2e/
│   │       └── workbench.spec.ts        # Playwright E2E browser tests
│   └── tsconfig.json                    # TypeScript compiler configuration
├── evals/                               # Factuality and SLA evaluation harness
│   ├── cases.jsonl                      # Curated benchmark claims with ground truth
│   ├── results.json                     # Latest evaluation benchmark outputs
│   └── run_evals.py                     # Offline evaluation benchmark CLI runner
├── scripts/                             # Repository tooling and maintenance
│   └── run_security_audit.sh            # Security audit gate (Semgrep, pip-audit, npm)
├── setup.sh                             # One-command project setup and dependency install
├── start.sh                             # One-command full-stack launcher (backend + frontend)
├── Makefile                             # Developer task targets
├── docker-compose.yml                   # Containerized full-stack deployment
├── .env.example                         # Environment configuration template
├── .env                                 # Local runtime environment settings
├── README.md                            # Complete project guide and codebase map
└── .planning/                           # GSD roadmap, state, and codebase maps
    ├── codebase/                        # Generated codebase map documents
    ├── PROJECT.md                       # Project overview and goals
    ├── REQUIREMENTS.md                  # System requirements and specifications
    ├── ROADMAP.md                       # Phase planning and governance
    └── STATE.md                         # Current milestone and session state
```

## Directory Purposes

**`backend/app/`:**
- Purpose: Complete server-side verification application
- Contains: API routes, business logic services, database interactions, provider clients
- Key files: `backend/app/main.py`, `backend/app/services/verification.py`

**`backend/app/services/`:**
- Purpose: Modular verification domain logic
- Submodules:
  - `screening.py`: Pre-retrieval empirical check (<10ms)
  - `clustering.py`: Domain extraction and wire service grouping
  - `citations.py`: Verbatim substring quote matching
  - `policy.py`: Deterministic verdict policy enforcement
  - `cache.py`: Search query cache with TTL expiration
  - `verification.py`: 8.0s monotonic SLA VerificationPipeline

**`frontend/`:**
- Purpose: Next.js 16 + React 19 interactive workbench
- Key files: `frontend/app/page.tsx`, `frontend/lib/api.ts`, `frontend/next.config.mjs`

**`evals/`:**
- Purpose: Quantitative factuality benchmark (ADR-005)
- Key files: `evals/run_evals.py`, `evals/cases.jsonl`, `evals/results.json`

## Entry Points

- **One-Command Setup:** `./setup.sh` or `make setup`
- **One-Command Start:** `./start.sh` or `make dev`
- **Containerized Run:** `docker compose up`
- **Backend Service:** `uvicorn app.main:app --port 8000` (in `backend/`)
- **Frontend Service:** `pnpm --prefix frontend dev`
- **Evaluation Runner:** `python evals/run_evals.py --cases evals/cases.jsonl`
- **Security Audit:** `bash scripts/run_security_audit.sh`

---

*Structure analysis: 2026-11-02*

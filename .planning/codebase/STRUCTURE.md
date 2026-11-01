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
│   │   ├── services/                    # Core business logic and verification engine
│   │   │   ├── __init__.py
│   │   │   └── verification.py          # Bounded retrieval, citation validation, policy
│   │   └── main.py                      # FastAPI app initialization, lifespan, CORS
│   ├── pyproject.toml                   # Python dependencies, Ruff, Pyright, Pytest config
│   └── tests/                           # Backend test suite
│       ├── conftest.py                  # Shared fixtures and mock configurations
│       ├── integration/                 # End-to-end API and concurrency tests
│       │   ├── test_api.py              # API endpoint integration tests
│       │   └── test_concurrency.py      # High-concurrency database lock tests
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
├── swe-sweep/                           # Autonomous bug discovery harness integration
├── misc/                                # Design documents, research notes, and specs
│   └── docs/designs/                    # Architecture and design specifications
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

**`backend/tests/`:**
- Purpose: Unit and integration testing suites
- Contains: Pytest suites covering SLA budgeting, citation validation, concurrency, and API contracts
- Key files: `backend/tests/unit/test_budget.py`, `backend/tests/integration/test_concurrency.py`

**`frontend/app/`:**
- Purpose: Next.js frontend pages and layouts
- Contains: Root application entry, UI views, styling
- Key files: `frontend/app/page.tsx`, `frontend/app/globals.css`

**`frontend/lib/`:**
- Purpose: Client-side shared library and API connectors
- Contains: Type definitions, HTTP communication, utility functions
- Key files: `frontend/lib/api.ts`, `frontend/lib/utils.ts`

**`evals/`:**
- Purpose: Independent factuality benchmark and SLA compliance evaluation
- Contains: Ground truth test cases, evaluation runner script, benchmark score logs
- Key files: `evals/run_evals.py`, `evals/cases.jsonl`

**`scripts/`:**
- Purpose: Maintenance, CI check scripts, security scanners
- Contains: Automated security scanning scripts for SAST and dependency audits
- Key files: `scripts/run_security_audit.sh`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI server entry point and application lifespan
- `frontend/app/page.tsx`: Web application root view and workbench interface
- `evals/run_evals.py`: Offline evaluation suite runner

**Configuration:**
- `backend/app/core/config.py`: Application runtime settings via Pydantic `BaseSettings`
- `backend/pyproject.toml`: Backend dependencies, Ruff, Pyright, Pytest configuration
- `frontend/package.json`: Frontend dependencies and build scripts
- `frontend/tsconfig.json`: TypeScript compiler options

**Core Logic:**
- `backend/app/services/verification.py`: Verification pipeline, Gate A screening, 8.0s monotonic SLA budget, citation validation, and verdict policy
- `backend/app/db/database.py`: SQLite connection pool, schema initialization, retry logic
- `backend/app/providers/brave.py`: Brave Search integration
- `backend/app/providers/meta.py`: LLM structured completion integration

**Testing:**
- `backend/tests/unit/`: Comprehensive backend unit tests
- `backend/tests/integration/`: Backend integration and high-concurrency database tests
- `frontend/tests/e2e/workbench.spec.ts`: Playwright end-to-end user experience tests

## Naming Conventions

**Files:**
- Backend: Snake_case for Python source and test files (`verification.py`, `test_budget.py`)
- Frontend: PascalCase or kebab-case for React components (`page.tsx`, `button.tsx`), camelCase for utilities and clients (`api.ts`, `utils.ts`)

**Directories:**
- Lowercase snake_case or single-word lowercase (`app`, `services`, `providers`, `components`, `e2e`)

## Where to Add New Code

**New Feature (Backend):**
- Domain logic: Implement within `backend/app/services/`
- API endpoints: Register in `backend/app/api/routes.py` with schemas in `backend/app/api/schemas.py`
- Tests: Add corresponding unit tests in `backend/tests/unit/test_<feature>.py`

**New Search or Model Provider:**
- Implementation: Create new provider module in `backend/app/providers/<provider_name>.py` implementing `SearchProvider` or `ModelProvider`
- Factory wiring: Register in `backend/app/providers/__init__.py`
- Tests: Add unit tests in `backend/tests/unit/test_providers.py`

**New UI Component / Modal:**
- Implementation: Add to `frontend/components/` or `frontend/components/ui/`
- Styling: Use Tailwind CSS v4 atomic classes
- E2E Tests: Add assertions in `frontend/tests/e2e/workbench.spec.ts`

**Utilities:**
- Backend helpers: Add to `backend/app/core/` or `backend/app/services/`
- Frontend helpers: Add to `frontend/lib/utils.ts`

## Special Directories

**`data/`:**
- Purpose: Stores local SQLite database (`jintru.db`, `jintru.db-wal`, `jintru.db-shm`)
- Generated: Yes (created automatically at runtime by `Database`)
- Committed: No (ignored via `.gitignore`)

**`.planning/`:**
- Purpose: GSD system state, phase roadmaps, requirements, and codebase mappings
- Generated: Yes
- Committed: Yes

**`evals/`:**
- Purpose: Curated offline evaluation datasets and results
- Generated: Results generated by `run_evals.py`
- Committed: Yes

---

*Structure analysis: 2026-11-02*

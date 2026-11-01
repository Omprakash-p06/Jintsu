# Structure Summary: Reality Check AI (jintru)

## Project Directory Layout

```
/home/omprakash/Documents/jintru/          # Project root
├── .github/                               # CI/CD workflows
│   └── workflows/
│       └── ci.yml                         # GitHub Actions matrix
├── .mcp.json                              # MCP configuration
├── .planning/                             # Planning and documentation
│   ├── ROADMAP.md                         # 4-phase roadmap governance
│   ├── STATE.md                           # Project state tracking
│   ├── REQUIREMENTS.md                    # Project requirements
│   ├── PROJECT.md                         # Project metadata
│   ├── STATE.json                         # Machine-readable state
│   ├── milestone.lock                     # Milestone locking
│   └── codebase/                          # Codebase mapping (this dir)
│       ├── STACK.md                       # Technology stack summary
│       ├── ARCHITECTURE.md                # System architecture
│       ├── CONVENTIONS.md                 # Code style conventions
│       ├── TESTING.md                     # Test suite overview
│       ├── STRUCTURE.md                   # Project structure
│       ├── CONCERNS.md                    # Known concerns and risks
│       └── INTEGRATIONS.md                # External service integrations
├── AGENTS.md                              # Agent role definition
├── implementation_readiness_report.md     # Delivery readiness
├── misc/                                  # Design specifications & ADRs
│   ├── docs/
│   │   ├── designs/
│   │   │   ├── jintru_claim_verification.md
│   │   │   └── concepts_brief.md
│   │   └── specification.md
│   ├── consolidated_review_report.md
│   └── goldfish_review_report.md
├── evals/                                 # Evaluation suite
│   ├── cases.jsonl                        # 27 benchmark cases
│   ├── results.json                       # Evaluation results
│   └── run_evals.py                       # Evaluation runner
├── backend/                               # Backend application
│   ├── app/                               # Source code
│   │   ├── api/                           # API endpoints
│   │   ├── core/                          # Core logic (errors, config)
│   │   ├── db/                            # Database module
│   │   ├── providers/                     # Model/search providers
│   │   ├── services/                      # Business services
│   │   └── schemas.py                     # Pydantic schemas
│   ├── tests/                             # Test directory
│   │   ├── unit/                          # Unit tests
│   │   │   ├── test_budget.py
│   │   │   └── test_evals_offline.py
│   │   └── integration/                   # Integration tests
│   │       └── test_concurrency.py
│   ├── pyproject.toml                     # Python project config
│   ├── .venv/                             # Virtual environment
│   └── scripts/                           # Utility scripts
├── frontend/                              # Frontend application
│   ├── package.json                       # Node.js dependencies
│   ├── package-lock.json                  # Lock file
│   ├── playwright.config.ts               # Playwright config
│   ├── tsconfig.json                      # TypeScript config
│   ├── src/                               # Source files
│   │   └── components/                    # React components
│   ├── tests/                             # E2E test directory
│   │   └── workbench.spec.ts
│   └── src/                               # Main source files
├── scripts/                               # Utility scripts
│   └── run_security_audit.sh              # Security audit script
├── misc/                                  # Goldfish review reports
│   └── goldfish_review_report.md
└── .git/                                  # Git repository
```

## Key Directory Descriptions

### `backend/app/` — Core Application Logic
- **`api/`** — FastAPI route definitions and endpoints
  - Verification API (`/api/v1/`)
  - Gateway endpoint with lifespan and CORS
- **`core/`** — Fundamental utilities
  - Error types (`ProviderTimeoutError`, etc.)
  - Configuration management
  - SLA guard enforcement
- **`db/`** — Database module
  - `Database` class with `@asynccontextmanager _connect()`
  - `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;`
  - `json.loads()` for JSON column decoding
  - `verifications` table (flat, JSON columns)
- **`providers/`** — External service integrations
  - Model providers (Meta AI `muse-spark-1.3`)
  - Search providers (Brave Search API)
  - Mock providers for testing
- **`services/`** — Business logic services
  - `VerificationPipeline` — Orchestrates two-stage retrieval
  - Gate A pre-retrieval screening
  - Structured synthesis call
- **`schemas.py`** — Pydantic data models
  - `SourceItem` — Search result with stance, hash, provenance
  - `VerificationSynthesisPayload` — JSON schema for LLM output
  - `PublicVerdict` — `supported|contradicted|mixed|insufficient_evidence|not_verifiable`
  - `ReasoningStatement` — Citation-backed reasoning

### `frontend/` — User Interface
- **`package.json`** — Node.js dependencies (Playwright, React, Tailwind)
- **`playwright.config.ts`** — Test configuration (Chromium + Firefox)
- **`src/`** — React components and pages
  - Workbench component (main user interface)
  - Verification result display
  - Verdict badge with color tokens
  - Source card components
  - Relationship map visualization
  - Settings modal (keyboard navigation, Escape dismissal)
- **`tests/e2e/workbench.spec.ts`** — E2E test suite

### `evals/` — Evaluation & Benchmarking
- **`cases.jsonl`** — 27 curated benchmark cases (7 categories)
- **`run_evals.py`** — Decoupled evaluation runner (ADR-005)
  - Isolates model reasoning from retrieval noise
  - Tier 1/2 citation entailment evaluation
  - Verdict counterevidence compliance check
  - Gate A screening evaluation
  - Generates `results.json` report
- **`results.json`** — Machine-readable evaluation output

### `scripts/` — Utility Scripts
- **`run_security_audit.sh`** — Three-part security audit
  - `semgrep scan --config auto backend/app/`
  - `pip-audit` for Python dependencies
  - `npm --prefix frontend audit --audit-level=high`

### `.planning/` — Project Planning & Governance
- **`ROADMAP.md`** — 4-phase governance structure
  - Phase 1: Foundations, Data Contracts & External Providers
  - Phase 2: Verification Engine, Citation Validation & API Gateway
  - Phase 3: Frontend Wiring & Full-Stack Integration
  - Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking
- **`STATE.md`** — Current project state tracking
- **`REQUIREMENTS.md`** — Project requirements and Milestone references
- **`PROJECT.md`** — Project metadata and description
- **`milestone.lock`** — Milestone locking mechanism
- **`codebase/`** — Codebase mapping artifacts (STACK.md, ARCHITECTURE.md, etc.)
- **`phases/`** — Individual phase artifacts (JINTRU-01 through JINTRU-04)
  - `*-SUMMARY.md` — Phase completion summaries
  - `*-PLAN.md` — Phase plans and deliverables
  - `*-REVIEW.md` — Code review reports

## File Relationships

### Verification Flow
1. User submits claim via frontend
2. Gate A pre-classification (subjective/future check)
3. Stage 1: Brave Search API (max 5 snippets)
4. Stage 2: Dialectical counter-search
5. Model synthesis (Meta API, `muse-spark-1.3`, temp=0.0)
6. Structured output validation (JSON Schema)
7. SQLite persistence (`verifications` table)
8. Verdict determination (5-tier: supported/contradicted/mixed/insufficient_evidence/not_verifiable)
9. Badge rendering + source cards + relationship map

### Test Execution Flow
1. `pytest` discovers `backend/tests/unit/` and `backend/tests/integration/`
2. `test_budget.py` validates SLA guards and timeout behavior
3. `test_evals_offline.py` asserts factuality thresholds
4. `test_concurrency.py` verifies SQLite WAL concurrency
5. Results reported to CI, which gates on 100% pass rate

### CI Pipeline Flow
1. Push to triggers GitHub Actions matrix
2. Matrix cell runs on Python 3.12 or Node 20
3. Backend: `pytest`, `ruff check`, `pyright`
4. Frontend: `tsc --noEmit`
5. Security: `semgrep`, `pip-audit`, `npm audit`
6. Playwright E2E (selected cells)
7. Results aggregated; failure if any job fails

## Commit History Snapshot (Last 10 Commits)
1. `73b2a31` feat(phase-4): implement offline evals benchmark, live SLA benchmarking
2. `9448928` feat(phase-4): implement verification suite, concurrency tests, E2E, security audit, CI
3. `3f6937b` docs(planning): create Phase 4 plans
4. `fb9c1e6` docs(phase-3): record code review fix report
5. `2d8882e` chore(frontend): clean placeholder assets, update package name
6. `aaac48c9` fix(frontend): remediate review findings
7. `f1d3347` fix(security): validate URL schemes, sanitize evidence href sinks
8. `f082075` docs(03): add code review report
9. `2ec2dbb` chore(frontend): ignore incremental typecheck output
10. `4a98af4` docs(03): record phase 3 summaries and blocked build gate
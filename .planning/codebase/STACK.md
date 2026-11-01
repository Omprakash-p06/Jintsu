# Stack Summary: Reality Check AI (jintru)

## Architecture Overview
The jintru system is a **Verifiable Claim Verification System** that evaluates empirical assertions through a bounded SLA pipeline. It follows a four-phase roadmap governance model.

## Core Components

### 1. Backend (Python/FastAPI)
- **Location:** `backend/app/`
- **Framework:** FastAPI with Python 3.12+ requirement
- **Key Dependencies:**
  - `uvicorn[standard]` - ASGI server
  - `pydantic>=2.9.0` - Data validation
  - `pydantic-settings>=2.5.0` - Configuration management
  - `httpx>=0.27.0` - HTTP client
  - `aiosqlite>=0.20.0` - Async SQLite support
  - `fastapi>=0.115.0,<1.0.0` - Web framework

### 2. Frontend (TypeScript/React)
- **Location:** `frontend/`
- **Framework:** React with Playwright E2E testing
- **Key Dependencies:**
  - Playwright (Chromium + Firefox)
  - Tailwind CSS v4 (`^4.0.0`)
  - Focus-visible rings (`#7C3AED`)

### 3. Verification Pipeline (Core Logic)
- **Two-stage bounded retrieval:**
  - **Stage 1 (Search):** Brave Search API, max 5 snippets, 2.0s timeout
  - **Stage 2 (Dialectical Counter-Search):** Unconditional query with `f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`, 2.0s timeout
- **SLA ceiling:** 8.0 seconds total
  - 0.2s Gate A Pre-Classification
  - 2.3s Stage 1 Search
  - 2.0s Stage 2 Counter-Search
  - 3.0s Structured Synthesis Call
  - 0.5s SQLite Persistence & Safety Buffer
- **Minimum Synthesis Window Guard:** At least 2.5s remaining required before model synthesis

### 4. Database (SQLite WAL Mode)
- **Connection factory:** `@asynccontextmanager _connect()`
- **Pragmas executed on every connection:**
  - `PRAGMA busy_timeout = 5000;`
  - `PRAGMA synchronous = NORMAL;`
- **Table:** `verifications` (flat table with JSON columns)

### 5. Evaluation Suite
- **Location:** `evals/`
- **Dataset:** `cases.jsonl` (27 curated benchmark cases)
- **Categories:** Empirical Supported, Contradicted, Disputed/Mixed, Insufficient Evidence, Subjective Value Judgments, Future Predictions, Adversarial Prompt Injections
- **Runner:** `run_evals.py` (implements ADR-005 decoupled protocol)

### 6. CI/CD Pipeline
- **Location:** `.github/workflows/ci.yml`
- **Matrix:** Python 3.12 + Node 20
- **Steps:**
  - Backend tests (`pytest`)
  - Frontend typecheck/build (`tsc`)
  - Security audits (semgrep, pip-audit, npm audit)
  - Playwright E2E tests

### 7. Planning & Documentation
- **Location:** `.planning/`
- **Roadmap:** `ROADMAP.md` (4-phase governance)
- **State tracking:** `STATE.md`, `REQUIREMENTS.md`
- **Phase plans:** `JINTRU-01` through `JINTRU-04`
- **Review artifacts:** `*-REVIEW.md` files per phase

## External Integrations
- **Brave Search API:** `/res/v1/web/search` and `/res/v1/llm/context`
- **Meta Model API:** `https://api.meta.ai/v1`, model `muse-spark-1.3`
- **Evaluation Benchmark:** SSOT-compliant datasets in `misc/`

## Design References
- `misc/docs/designs/jintru_claim_verification.md` - Master Design Specification
- `misc/docs/designs/concepts_brief.md` - Architectural Concepts
- `misc/docs/specification.md` - Research Foundations & ADRs
- `misc/consolidated_review_report.md` - EGM Master Review Sign-Off
- `misc/goldfish_review_report.md` - Contract Resolution Audit
# Reality Check AI (`jintru`) — Verifiable Claim Verification System

A production-grade, clock-bounded empirical claim verification engine with dialectical multi-stage retrieval, strict verbatim citation entailment, and hard application-level verdict policy guardrails.

---

## 🌟 Overview & Core Principles

Reality Check AI (`jintru`) evaluates single empirical assertions within a strict **8.0-second monotonic SLA deadline**. Unlike conventional LLM-based search or fact-checking tools that blindly summarize search results or trust raw model outputs, `jintru` implements strict architectural and verification guardrails:

1. **Clock-Bounded Monotonic Budgeting:** Every asynchronous retrieval, filtering, and synthesis step is strictly bounded against an authoritative 8.0s wall-clock ceiling. Subordinate timeouts clamp to remaining time; requests abort cleanly with an HTTP 504 `SYNTHESIS_WINDOW_EXCEEDED` if fewer than 2.5s remain.
2. **Gate A Conservative Pre-Retrieval Screening:** Fast regex-based screening flags subjective value judgments and future prospective predictions within <10ms without wasting external search quotas or LLM compute.
3. **Dialectical Two-Stage Retrieval:** Queries affirmative search in Stage 1, followed by dialectical counter-evidence search in Stage 2 to actively discover conflicting or refuting evidence.
4. **Strict Verbatim Citation Entailment:** Quotes proposed by LLM synthesis must match retrieved snippet text verbatim (with zero-width stripping and HTML unescaping); ungrounded citations are stripped.
5. **Deterministic Verdict Policy Matrix:**
   - **Absence of Counterevidence Guardrail:** Prohibits awarding `supported` if credible, relevant refuting evidence is present in retrieved sources.
   - **Multi-Family Corroboration:** Requires $\ge 2$ independent source domains (normalizing publisher subdomains and wire services like AP, Reuters, PR Newswire) to award `supported`.
   - **Grounding Checks:** Prohibits `contradicted` without direct refutations and `mixed` without both supporting and refuting evidence.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    Next.js Workbench UI (App Router)                    │
│           `frontend/app/page.tsx` & `frontend/lib/api.ts`               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP /api/v1 (JSON Envelopes)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway & Lifespan Router                    │
│           `backend/app/main.py` & `backend/app/api/routes.py`           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│    Gate A Screening Engine      │             │  SQLite Async Store (WAL mode)  │
│   (Subjective/Future Filtering) │             │    `backend/app/db/database.py` │
│ `backend/app/services/screening`│             └─────────────────────────────────┘
└────────────────┬────────────────┘                              ▲
                 │ (Empirical Claims)                            │
                 ▼                                               │ (Persist Record)
┌──────────────────────────────────────────────────────────┐     │
│   Verification Engine Pipeline (8.0s Monotonic Budget)   ├─────┘
│           `backend/app/services/verification.py`         │
└────────┬────────────────────────────────┬────────────────┘
         │                                │
         ▼                                ▼
┌────────────────────────────────┐ ┌────────────────────────────────┐
│   Brave Search Provider        │ │   Meta AI / OpenAI Provider    │
│  (Stage 1 Affirmative Search   │ │  (Strict Structured JSON       │
│   + Stage 2 Dialectical)       │ │   Reasoning Synthesis)         │
│ `backend/app/providers/brave.py`│ │ `backend/app/providers/meta.py`│
└────────────────────────────────┘ └────────────────────────────────┘
```

---

## ⚡ Quickstart: One-Command Universal Setup & Run

### 1. Universal Setup (Windows, macOS, Linux)
Install all backend and frontend dependencies, initialize the `.env` file, and prepare the SQLite database with a single cross-platform Python command:

```bash
# Works natively on Windows, macOS, and Linux
python setup.py

# Alternatively, on POSIX / bash:
./setup.sh
# or using Makefile:
make setup
```

### 2. Universal Full-Stack Start (Windows, macOS, Linux)
Launch both the FastAPI backend (`http://localhost:8000`) and the Next.js frontend (`http://localhost:3000`) with a single command:

```bash
# Works natively on Windows, macOS, and Linux
python run.py

# Alternatively, on POSIX / bash:
./start.sh
# or using Makefile:
make dev
```

### 3. Containerized Run (Docker Compose)
Run the entire system in isolated containers:

```bash
docker compose up --build
```

### 🌐 Access Endpoints
- **Frontend Workbench:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 📁 Codebase Map (`.planning/codebase/`)

The repository structure adheres to the GSD codebase mapping contract:

| Document | Description | Key Topics Covered |
|----------|-------------|--------------------|
| [**`STACK.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/STACK.md) | Technology Stack | Python 3.11+, TypeScript 5.7+, FastAPI, Next.js 16, React 19, Tailwind CSS v4, Pydantic, aiosqlite |
| [**`ARCHITECTURE.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/ARCHITECTURE.md) | System Architecture | Monotonic 8.0s budget, Gate A screening, 2-stage retrieval, verbatim citation entailment, verdict policy |
| [**`STRUCTURE.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/STRUCTURE.md) | Directory Organization | Directory layout, entry points, component placement guidelines, test locations |
| [**`CONVENTIONS.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/CONVENTIONS.md) | Coding Conventions | PEP 8, Ruff formatting, Pyright strict types, typed API errors, async patterns |
| [**`TESTING.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/TESTING.md) | Testing Practices | 97 Pytest suites, Playwright E2E browser tests, offline factuality evaluation harness |
| [**`INTEGRATIONS.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/INTEGRATIONS.md) | External Integrations | Brave Search API, Meta AI / OpenAI endpoints, SQLite WAL concurrency, CI matrix |
| [**`CONCERNS.md`**](file:///home/omprakash/Documents/jintru/.planning/codebase/CONCERNS.md) | Technical Concerns & Fixes | Resolution of technical debt, modularization, security headers, query caching |

### Directory Layout

```
jintru/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST routes and Pydantic schemas (routes.py, schemas.py)
│   │   ├── core/                # App configuration and domain error envelopes (config.py, errors.py)
│   │   ├── db/                  # Async SQLite persistence with WAL & retry (database.py)
│   │   ├── providers/           # Brave Search, Meta AI, and Mock provider adapters
│   │   │   ├── base.py          # SearchProvider and ModelProvider ABCs
│   │   │   ├── brave.py         # Brave web search & LLM context client
│   │   │   ├── meta.py          # Strict JSON schema LLM synthesis client
│   │   │   └── mock.py          # Deterministic offline mock provider suite
│   │   ├── services/            # Verification engine pipeline (modular architecture)
│   │   │   ├── screening.py     # Gate A pre-retrieval classification
│   │   │   ├── clustering.py    # URL sanitization & source domain normalization
│   │   │   ├── citations.py     # Verbatim quote & citation validation
│   │   │   ├── policy.py        # Application verdict policy matrix
│   │   │   ├── cache.py         # Persistent search query cache
│   │   │   └── verification.py  # 8.0s monotonic SLA VerificationPipeline orchestrator
│   │   └── main.py              # FastAPI app factory, lifespan, and CORS middleware
│   ├── tests/                   # 97 Pytest unit and integration test suites
│   └── pyproject.toml           # Python dependencies and tool configs (Ruff, Pyright, Pytest)
├── frontend/
│   ├── app/                     # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   ├── components/              # Shadcn UI primitives and accessible components
│   ├── lib/                     # Typed API client with error envelopes (api.ts, utils.ts)
│   ├── tests/e2e/               # Playwright browser end-to-end automation
│   ├── package.json             # Frontend dependencies (React 19, Tailwind CSS v4)
│   └── next.config.mjs          # Next.js proxy rewrites and CSP security headers
├── evals/
│   ├── cases.jsonl              # 27 curated evaluation benchmark cases across 7 categories
│   ├── results.json             # Benchmark scorecard outputs
│   └── run_evals.py             # Offline evaluation benchmark CLI runner (ADR-005)
├── scripts/
│   └── run_security_audit.sh    # Semgrep SAST, pip-audit, and npm audit security gate
├── setup.py                     # Universal cross-platform setup script (Windows, macOS, Linux)
├── run.py                       # Universal cross-platform full-stack runner (Windows, macOS, Linux)
├── setup.sh                     # POSIX shell setup wrapper
├── start.sh                     # POSIX shell launcher wrapper
├── Makefile                     # Developer convenience Makefile
├── docker-compose.yml           # Multi-container orchestration
├── .env.example                 # Environment configuration template
├── .env                         # Local runtime environment settings
└── README.md                    # Complete project guide and codebase map
```

---

## 🔧 Environment Configuration (`.env`)

Configure `.env` at the project root (copied automatically from `.env.example` by `python setup.py`):

```bash
# --- Provider Mode ---
# Set to 'true' to use local deterministic mocks (no paid API keys required).
# Set to 'false' to enable live web retrieval and model synthesis.
USE_MOCK_PROVIDERS=true

# --- Brave Search API ---
# Obtain from https://brave.com/search/api/ (Required if USE_MOCK_PROVIDERS=false)
BRAVE_API_KEY=your_brave_api_key_here
BRAVE_RETRIEVAL_MODE=snippets    # "snippets" or "context"

# --- LLM Provider (Meta AI / OpenAI-compatible) ---
# (Required if USE_MOCK_PROVIDERS=false)
META_API_KEY=your_meta_api_key_here
META_API_BASE_URL=https://api.meta.ai/v1
META_MODEL=muse-spark-1.3

# --- Storage & Performance ---
DATABASE_PATH=data/jintru.db
REQUEST_DEADLINE_SECONDS=8.0
CACHE_ENABLED=true               # Enables search query caching
```

---

## 🧪 Testing & Quality Gates

### 1. Backend Test Suite (97 tests)
Runs unit, integration, and high-concurrency database lock tests:

```bash
make test
# or:
backend/.venv/bin/pytest backend/tests
```

### 2. Offline Factuality & SLA Benchmark (ADR-005)
Evaluates 27 curated ground-truth cases across 7 categories:

```bash
make eval
# or:
backend/.venv/bin/python evals/run_evals.py --cases evals/cases.jsonl
```

**SLA Scorecard Metrics:**
- **Verdict Classification Accuracy:** $\ge 95\%$
- **Citation Entailment Precision:** $100\%$ (Target: $\ge 90\%$)
- **False-Support Rate under Absent Evidence:** $0.0\%$ (Target: $\le 5\%$)
- **Counterevidence Recall:** $100\%$ (Target: $\ge 80\%$)
- **SLA 504 Degradation Guard:** $100\%$ compliance

### 3. Security Audits (SAST & Vulnerabilities)
Runs Semgrep SAST scanning, Python dependency vulnerability scanning, and npm frontend audits:

```bash
make audit
# or:
bash scripts/run_security_audit.sh
```

### 4. Static Typechecking & Linting
```bash
make lint        # Ruff Python linter
make typecheck   # Pyright strict Python check + tsc --noEmit
```

---

## 🛡️ Addressed Concerns & Technical Hardening

All concerns listed in [`CONCERNS.md`](file:///home/omprakash/Documents/jintru/.planning/codebase/CONCERNS.md) have been resolved:

1. **Monolithic Verification Pipeline Refactoring:** Decomposed the 500+ line pipeline into specialized modules:
   - `screening.py`: Pre-retrieval classification
   - `clustering.py`: Domain normalization and news wire mapping
   - `citations.py`: Verbatim quote verification
   - `policy.py`: Grounding and limitation checks
   - `cache.py`: Search query cache
   - `verification.py`: 8.0s monotonic SLA orchestrator
2. **Python Compatibility Broadening:** Relaxed `requires-python = ">=3.11"` in `backend/pyproject.toml` to support Python 3.11+ deployment environments.
3. **Node Runtime Floor & Frontend Build:** Resolved Next.js 16 requirements by configuring Node.js 20 LTS and pnpm, enabling static compilation and clean production builds (`pnpm build`).
4. **Persistent Search Query Caching:** Added `QueryCache` (`backend/app/services/cache.py`) to prevent duplicate external search calls and rate-limit exhaustion.
5. **Security & CSP Headers:** Added strict security headers (Content Security Policy, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy) in `frontend/next.config.mjs`.
6. **Zero-Friction Startup:** Provided `setup.sh`, `start.sh`, `Makefile`, and `docker-compose.yml` for single-command setup and execution.

---

## 📜 License
Reality Check AI (`jintru`) is licensed under the Apache 2.0 License.

---
last_mapped_commit: f58f1905d7983a44dba0aa09255ff203eb536a4f
last_mapped_at: 2026-11-02
---
<!-- refreshed: 2026-11-02 -->

# Architecture

**Analysis Date:** 2026-11-02

## System Overview

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
│ `backend/app/services/verif...` │             └─────────────────────────────────┘
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

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `create_app` / FastAPI Lifespan | Initializes database, registers exception envelopes, and manages router middleware | `backend/app/main.py` |
| `router` | Defines REST endpoints (`/verifications`, `/verifications/{id}`, `/health`) and query parsing | `backend/app/api/routes.py` |
| `VerificationPipeline` | Orchestrates Gate A screening, 8.0s budget management, two-stage search, LLM synthesis, citation validation, and verdict policy enforcement | `backend/app/services/verification.py` |
| `Database` | Handles asynchronous SQLite operations with WAL mode, busy timeouts, and exponential write retries | `backend/app/db/database.py` |
| `BraveSearchProvider` | Queries Brave web or context APIs with subordinate timeouts and extracts normalized source items | `backend/app/providers/brave.py` |
| `MetaModelProvider` | Dispatches structured chat completion calls with hardened JSON schemas and handles model fallback | `backend/app/providers/meta.py` |
| `MockSearchProvider` / `MockModelProvider` | Provides deterministic offline search and synthesis execution for testing | `backend/app/providers/mock.py` |
| Workbench UI (`page.tsx`) | Renders claims submission, live execution progress, verdict badges, citations, and verification history | `frontend/app/page.tsx` |
| Typed API Client (`api.ts`) | Type-safe wrapper for API requests, error envelope parsing, and URL sanitization | `frontend/lib/api.ts` |

## Pattern Overview

**Overall:** Monotonic Deadline-Bounded Pipeline Architecture with Hard Application-Level Policy Gates

**Key Characteristics:**
- **Authoritative Monotonic SLA Budgeting:** Every asynchronous phase checks elapsed time against a strict 8.0s ceiling. Subordinate timeouts clamp to remaining time, and synthesis aborts early if fewer than 2.5s remain.
- **Dialectical Two-Stage Retrieval:** Queries affirmative search in Stage 1, followed by counter-evidence search in Stage 2 to discover conflicting or refuting evidence.
- **Strict Verbatim Citation Entailment:** Model-proposed citations and quotes are validated against actual source snippets using whitespace normalization and zero-width character stripping.
- **Deterministic Policy Matrix:** Verdicts (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`) are finalized by application logic rather than trusting raw LLM verdicts.

## Layers

**Presentation Layer (Frontend):**
- Purpose: Interactive verification workbench, history navigation, and verdict visualization
- Location: `frontend/app/`, `frontend/components/`
- Contains: React 19 functional components, Tailwind CSS styling, Lucid icons, accessibility hooks
- Depends on: Typed API client (`frontend/lib/api.ts`)
- Used by: End users in web browsers

**API & Routing Layer:**
- Purpose: HTTP contract serialization, parameter validation, and standard error envelopment
- Location: `backend/app/api/`, `backend/app/main.py`
- Contains: FastAPI router, Pydantic request/response schemas, exception handlers
- Depends on: Verification service and database layers
- Used by: Frontend client, evaluation scripts, external HTTP consumers

**Service / Engine Layer:**
- Purpose: Core claim verification logic, budget countdown, screening, citation validation, and policy checks
- Location: `backend/app/services/verification.py`
- Contains: `VerificationPipeline`, `classify_input`, `extract_verbatim_quotes`, `apply_verdict_policy`
- Depends on: Provider layer and database abstraction
- Used by: Route handlers and offline evaluation benchmarks

**Provider Layer:**
- Purpose: Abstract interface and concrete clients for search indexes and LLM synthesis
- Location: `backend/app/providers/`
- Contains: `SearchProvider`, `ModelProvider`, `BraveSearchProvider`, `MetaModelProvider`, `MockSearchProvider`
- Depends on: `httpx`, Pydantic schemas, `app.core.config`
- Used by: `VerificationPipeline`

**Data Persistence Layer:**
- Purpose: Local ACID persistence of verification sessions, sources, reasoning, and metadata
- Location: `backend/app/db/database.py`
- Contains: `Database` class, connection lifecycle, migration logic, SQLite schema
- Depends on: `aiosqlite`, SQLite 3
- Used by: Route handlers, pipeline persistence step

## Data Flow

### Primary Request Path (Empirical Claim)

1. Client posts claim to `/api/v1/verifications` (`backend/app/api/routes.py:18`)
2. FastAPI validates claim length (5-500 chars) and non-whitespace constraints (`backend/app/api/schemas.py:23`)
3. `VerificationPipeline.verify()` records `monotonic()` start time and executes Gate A screening (`backend/app/services/verification.py:270`)
4. Stage 1 affirmative search executed via `SearchProvider.search()` with timeout clamped to `min(2.0, remaining)` (`backend/app/services/verification.py:315`)
5. If remaining time >= 3.5s, Stage 2 dialectical counter-search executes with inverted query (`backend/app/services/verification.py:330`)
6. Sources are unified, deduplicated by URL and content hash, and news wire attribution tokens are mapped (`backend/app/services/verification.py:350`)
7. Minimum synthesis window checked: if remaining time < 2.5s, aborts with 504 `SYNTHESIS_WINDOW_EXCEEDED` (`backend/app/services/verification.py:365`)
8. Model generates structured synthesis payload via `ModelProvider.synthesize()` (`backend/app/services/verification.py:375`)
9. Citation quotes undergo verbatim substring validation against retrieved snippets (`backend/app/services/verification.py:400`)
10. Application verdict policy verifies independent source corroboration, unresolved counterevidence, and grounds verdict (`backend/app/services/verification.py:430`)
11. Record is persisted to SQLite asynchronously with write retry (`backend/app/db/database.py:65`)
12. Formatted `VerificationResponse` is returned with status 200 (`backend/app/api/routes.py:30`)

### Non-Empirical / Prospective Claim Flow (Gate A Early Exit)

1. Client posts subjective or future prediction claim (e.g. "By 2050 humans will live on Mars")
2. `classify_input()` identifies regex/temporal pattern (`backend/app/services/verification.py:120`)
3. Pipeline exits immediately without invoking external search or LLM providers
4. Record persisted with verdict `not_verifiable` and rationale in limitations
5. Response returned in <10ms with status 200

**State Management:**
- Stateless per-request execution pipeline.
- Persistent state stored entirely in SQLite database (`verifications` table).
- Frontend manages local UI state using React `useState`, `useCallback`, and `useMemo` hooks.

## Key Abstractions

**`SearchProvider` (Abstract Base Class):**
- Purpose: Defines standard interface for multi-mode external search retrieval
- Examples: `BraveSearchProvider` (`backend/app/providers/brave.py`), `MockSearchProvider` (`backend/app/providers/mock.py`)
- Pattern: Strategy Pattern

**`ModelProvider` (Abstract Base Class):**
- Purpose: Defines standard interface for structured claim synthesis and reasoning
- Examples: `MetaModelProvider` (`backend/app/providers/meta.py`), `MockModelProvider` (`backend/app/providers/mock.py`)
- Pattern: Strategy Pattern

**`ErrorEnvelope` (Pydantic Base Model):**
- Purpose: Standardized API error payload across all failure modes (validation, timeout, provider unavailable, disconnection)
- Examples: `backend/app/api/schemas.py`, handled in `backend/app/main.py`
- Pattern: Uniform Error Envelope

## Entry Points

**API Service:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Responsibilities: ASGI server lifecycle, DB connection pooling, CORS setup, routing

**Frontend Workbench:**
- Location: `frontend/app/page.tsx`
- Triggers: Next.js dev or production server (`pnpm dev` / `pnpm start`)
- Responsibilities: User interaction, real-time claim entry, history inspection

**Evaluation Suite CLI:**
- Location: `evals/run_evals.py`
- Triggers: `python evals/run_evals.py --cases evals/cases.jsonl`
- Responsibilities: Batch benchmarking, precision/recall metrics, SLA distribution verification

**Security Audit Runner:**
- Location: `scripts/run_security_audit.sh`
- Triggers: CI runner or developer execution (`bash scripts/run_security_audit.sh`)
- Responsibilities: Semgrep SAST, pip-audit, and npm audit gating

## Architectural Constraints

- **Monotonic Budget & SLA Ceiling:** Strict 8.0s hard ceiling using `time.monotonic()`. Subordinate timeouts are never static; they are clamped to `min(stage_budget, remaining_time)`.
- **Threading & Async Event Loop:** Single-threaded asyncio event loop. No blocking synchronous I/O allowed inside request coroutines. SQLite operations run via `aiosqlite`.
- **Global State:** Minimal module-level state. Settings object initialized in `backend/app/core/config.py`. FastAPI `app.state` holds runtime singletons (`db`, `pipeline`, `settings`).
- **Circular Imports:** Modules follow strict directional flow: `core` → `db` / `providers` → `services` → `api` → `main`. No circular dependencies permitted.

## Anti-Patterns

### Raw Model Verdict Trust

**What happens:** Accepting the LLM's returned verdict without verifying corroboration or counter-evidence.
**Why it's wrong:** Models hallucinate consensus, ignore dissenting retrieved snippets, or declare "supported" based on a single partisan source.
**Do this instead:** Apply `apply_verdict_policy()` (`backend/app/services/verification.py:195`) to enforce independent multi-family corroboration and cap verdicts when counterevidence exists.

### Static Unbounded Timeouts

**What happens:** Using static `httpx.AsyncClient(timeout=10.0)` or unbounded search requests across stages.
**Why it's wrong:** Individual network delays cascade, causing the 8.0s SLA to be breached and socket connections to hang indefinitely.
**Do this instead:** Pass `timeout=min(STAGE_TIMEOUT, remaining)` and enforce `_enforce_synthesis_guard(remaining)` (`backend/app/services/verification.py:290`).

## Error Handling

**Strategy:** Uniform JSON error envelopment with RFC-compliant status codes (422, 499, 503, 504).

**Patterns:**
- Custom typed domain exceptions inheriting from `DomainError` in `backend/app/core/errors.py`:
  - `ProviderTimeoutError` → HTTP 504 Gateway Timeout
  - `ProviderUnavailableError` → HTTP 503 Service Unavailable
  - `ClientDisconnectedError` → HTTP 499 Client Closed Request
  - `RequestConstraintError` → HTTP 422 Unprocessable Entity
- Graceful degradation: synthesis guard guarantees clean 504 without corrupting database state.

## Cross-Cutting Concerns

**Logging:** Standardized Python logging with stage timestamps and latency metrics in `backend/app/services/verification.py`.
**Validation:** Dual-layer validation via Pydantic schemas in `backend/app/api/schemas.py` and TypeScript interfaces in `frontend/lib/api.ts`.
**Security & Sanitation:** Verbatim citation quotation checks, URL schema sanitization (`safeHref` in `frontend/lib/api.ts`), and regular automated SAST scans (`scripts/run_security_audit.sh`).

---

*Architecture analysis: 2026-11-02*

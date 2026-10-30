# Roadmap: Reality Check AI (`jintru`)

## Overview

This roadmap defines the end-to-end execution path for Reality Check AI (`jintru`) Milestone 1. Per architectural requirements, the project is consolidated into **4 broad, cohesive phases** that build the complete vertical slice: from Python 3.12 foundations and external search/synthesis adapters, to clock-bounded verification orchestration and citation validation, through an accessible React 19 workbench UI, culminating in comprehensive CI automation, security audits, and offline/live evaluation benchmarks.

---

> [!IMPORTANT]
> **MANDATORY PROJECT INVARIANT — ULTIMATE STATE OF TRUTH (SSOT):**  
> To guarantee that the project does not get diverted, the ultimate state of truth for each and every phase of this project is strictly defined by the approved design, specification, and review artifacts in [`misc/`](file:///home/omprakash/Documents/jintru/misc):
> 1. [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) — Master Executable Design Specification & Interface Contracts
> 2. [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) — Architectural Concepts Brief
> 3. [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) — Research Foundations, ADRs & Baseline Bibliography
> 4. [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) — EGM Goldfish Review Protocol Master Sign-off
> 5. [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) — Final Contract Resolution Audit
>
> Every phase plan (`*-PLAN.md`) created under `/gsd-plan-phase` **must** explicitly reference and strictly conform to these documents.

---

## Phases

- [ ] **Phase 1: Foundations, Data Contracts & External Providers** - Core Python 3.12 dependencies, Pydantic schemas, SQLite WAL persistence, and Brave Search / Meta Model provider adapters.
- [ ] **Phase 2: Verification Engine, Citation Validation & API Gateway** - Clock-bounded monotonic pipeline, Gate A classification, 2-tier citation matching, verdict policy, and FastAPI routes.
- [ ] **Phase 3: React Workbench UI & Full-Stack Integration** - React 19 + TypeScript 5.6 + stable Tailwind CSS v4 workbench application, 5-way verdict badge, evidence cards, and history drawer.
- [ ] **Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking** - Automated unit/integration tests, Playwright E2E tests, security audits, and quantitative offline/live evaluation benchmarks.

---

## Phase Details

### Phase 1: Foundations, Data Contracts & External Providers
**Goal**: Deliver the compiling Python 3.12 backend scaffolding, typed Pydantic contracts, concurrency-hardened SQLite persistence, and external search/synthesis provider adapters.  
**Ultimate State of Truth (SSOT)**:
- [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) (Sections 3.6, 3.7; Phases 1, 2, 3)
- [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) (ADR-001, ADR-003)
- [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) (ADR-003, ADR-004)
- [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) (Findings IR-01, IR-02, IR-04, IR-06, IR-07)
- [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) (Item 1, Item 3)

**Depends on**: Nothing (first phase)  
**UI hint**: no  
**Requirements**: `FOUND-01`, `FOUND-02`, `FOUND-03`, `DATA-01`, `PROV-01`, `PROV-02`  
**Success Criteria** (what must be TRUE):
  1. `backend/pyproject.toml` installs cleanly under Python 3.12; `ruff check backend/` and `pyright backend/app/` pass with zero errors.
  2. `backend/app/core/config.py` loads `Settings` with `META_MODEL="muse-spark-1.3"`, `REQUEST_DEADLINE_SECONDS=8.0`, and `USE_MOCK_PROVIDERS`.
  3. `Database` in `backend/app/db/database.py` enforces connection-scoped `PRAGMA busy_timeout=5000;` and `PRAGMA synchronous=NORMAL;` via `_connect()`, and `get_verification()` parses JSON fields without Pydantic validation errors.
  4. `BraveSearchProvider` extracts snippets and maps `grounding.generic[].snippets` (LLM Context) into `SourceItem` contracts with SHA-256 hashes and wire/domain clustering.
  5. `MetaModelProvider` dispatches structured completion requests locked to `muse-spark-1.3` using `response_format` matching `VerificationSynthesisPayload`.
  6. Deterministic mock search and model providers in `mock.py` return valid data for offline testing.

**Plans**: 2 plans
- [ ] 01-01: Backend scaffolding, configuration, Pydantic data schemas, and concurrency-safe SQLite persistence.
- [ ] 01-02: External provider interfaces, Brave Search adapter (snippets + context), Meta Model API adapter, and deterministic mocks.

---

### Phase 2: Verification Engine, Citation Validation & API Gateway
**Goal**: Build the core deterministic verification pipeline, conservative pre-retrieval classification, two-tier citation verification, deterministic verdict policy with counterevidence guardrails, and FastAPI REST endpoints.  
**Ultimate State of Truth (SSOT)**:
- [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) (Sections 3.1–3.5, 3.8; Phases 4, 5)
- [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) (ADR-001, ADR-002)
- [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) (ADR-001, ADR-002)
- [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) (Findings CR-01, CR-02, IR-05, IR-08, IR-10, IR-13, IR-14)
- [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) (Item 1)

**Depends on**: Phase 1  
**UI hint**: no  
**Requirements**: `PIPE-01`, `PIPE-02`, `CITE-01`, `POL-01`, `API-01`, `API-02`  
**Success Criteria** (what must be TRUE):
  1. `classify_input` catches subjective value judgments and future predictions using conservative regex (protecting entities like "Best Buy" and historical statements), short-circuiting to `not_verifiable` (0 search, 0 LLM calls).
  2. Orchestrator executes monotonic budget: Stage 1 search (2.3s allocation, 2.0s timeout), unconditional Stage 2 dialectical counter-search if time ≥ 3.5s, and cleanly returns HTTP 504 Gateway Timeout if synthesis window drops below 2.5s.
  3. `validate_citations` validates Tier 1 ID existence and Tier 2 normalized exact substring matching (`quoted_excerpt` in `snippet`).
  4. `apply_verdict_policy` strictly bars `supported` when credible counterevidence exists (`stance == "refutes"` with direct/contextual relevance), and enforces the 2-domain corroboration guardrail.
  5. FastAPI app mounts all 6 routes (`/verifications`, `/health`, CRUD) using modern `@asynccontextmanager lifespan` handler and structured `ErrorEnvelope`.

**Plans**: 2 plans
- [ ] 02-01: Verification pipeline orchestrator (Gate A screening, two-stage dialectical retrieval, 2.5s window guard, citation validation, verdict policy).
- [ ] 02-02: FastAPI gateway routes (`/api/v1`), modern lifespan handler, CORS configuration, and domain exception handlers.

---

### Phase 3: React Workbench UI & Full-Stack Integration
**Goal**: Build the responsive, accessible web workbench using React 19, TypeScript, and stable Tailwind CSS v4, providing claim verification input, live timers, 5-way verdict badges, quoted source evidence cards, and history management.  
**Ultimate State of Truth (SSOT)**:
- [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) (Section 3.1; Phase 6)
- [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md)
- [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) (Findings IR-03, IR-11, IR-19)
- [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) (Item 2)

**Depends on**: Phase 2  
**UI hint**: yes  
**Requirements**: `UI-01`, `UI-02`, `UI-03`, `UI-04`, `UI-05`  
**Success Criteria** (what must be TRUE):
  1. Frontend project builds and typechecks cleanly via `npm run build`, `npm run lint`, and `npm run typecheck` using stable Tailwind v4 (`^4.0.0`).
  2. `Workbench.tsx` enforces 500-character input ceiling, submit triggers verification, and active state displays loading spinner with elapsed timer.
  3. `VerdictCard.tsx` renders accessible 5-way badge pairing semantic icons with explicit color tokens (`supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo), summary narrative, and limitations accordion.
  4. `EvidenceList.tsx` renders source items with stance badges, canonical domains, quoted snippets, and safe external links (`rel="noopener noreferrer"`).
  5. `HistoryPanel.tsx` drawer allows browsing previous runs, deleting individual records (`DELETE /verifications/{id}`), and purging history (`DELETE /verifications`).
  6. Frontend integrates with backend over `/api/v1` via Vite proxy with zero CORS or serialization errors.

**Plans**: 2 plans
- [ ] 03-01: Frontend project scaffolding, Vite proxy, Tailwind CSS v4 setup, typed API client, and root shell.
- [ ] 03-02: Feature components (`Workbench`, `VerdictCard`, `EvidenceList`, `HistoryPanel`) and full-stack integration.

---

### Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking
**Goal**: Implement comprehensive automated testing, Playwright E2E user journeys, static security audits, offline factuality evaluation harness, and live WAN latency distribution benchmarking.  
**Ultimate State of Truth (SSOT)**:
- [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) (Phases 7, 8; Section 5 Verification Plan)
- [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) (ADR-005)
- [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) (ADR-005)
- [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) (Findings IR-09, IR-12, IR-17)
- [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) (Item 3)

**Depends on**: Phase 3  
**UI hint**: no  
**Requirements**: `TEST-01`, `TEST-02`, `SEC-01`, `EVAL-01`, `EVAL-02`  
**Success Criteria** (what must be TRUE):
  1. `pytest backend/tests/` passes with unit and integration tests verifying citation checks, budget enforcement, provider mocks, and 0 database lockups under 10 concurrent tasks.
  2. Playwright E2E tests (`npm --prefix frontend run test:e2e -- --project=chromium --project=firefox`) validate CUJ 1 and CUJ 3 end-to-end.
  3. Security audits pass cleanly: `semgrep --config auto backend/`, `pip-audit backend/`, and `npm --prefix frontend audit`.
  4. Offline benchmark harness (`evals/run_evals.py --cases evals/cases.jsonl`) verifies quantitative metrics: citation entailment precision ≥ 90%, false-support rate under absent evidence ≤ 5%, counterevidence recall ≥ 80%.
  5. Live WAN retrieval benchmark tracks latency distribution (P50, P90, P95) and confirms that 100% of injected latency spikes reducing synthesis time below 2.5s degrade cleanly to HTTP 504 Gateway Timeout.

**Plans**: 2 plans
- [ ] 04-01: Unit, integration, concurrency, Playwright E2E test suites, and security audit automation.
- [ ] 04-02: Curated offline evaluation benchmark harness and live WAN latency distribution benchmarking.

---

## Progress

**Execution Order:**
Phases execute in numeric order: Phase 1 → Phase 2 → Phase 3 → Phase 4

| Phase | Plans Complete | Status | Completed |
|-------|:--------------:|:------:|:---------:|
| 1. Foundations, Data Contracts & External Providers | 0/2 | Not started | - |
| 2. Verification Engine, Citation Validation & API Gateway | 0/2 | Not started | - |
| 3. React Workbench UI & Full-Stack Integration | 0/2 | Not started | - |
| 4. Verification Suite, Offline Evals & Live SLA Benchmarking | 0/2 | Not started | - |


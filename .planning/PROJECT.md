# Reality Check AI (`jintru`) — Verifiable Claim Verification System

## What This Is

Reality Check AI (`jintru`) is a single-agent, deterministic factual verification system exposed through an accessible React web workbench. It evaluates single empirical assertions (≤ 500 characters) against live web evidence retrieved from search snippets, actively searching for counterevidence, clustering syndicated source provenance, and enforcing three-tier citation validation.

## Core Value

> **"Show what supports a claim, what challenges it, how reliable that evidence is, and exactly what remains unknown."**

The system does not claim to declare universal truth; it provides an unyielding, inspectable evidence workbench that gives claims a fair chance to be disproved, refuses to hallucinate consensus, and strictly abstains when evidence is absent or inconclusive.

---

## Ultimate State of Truth (Single Source of Truth — SSOT)

> [!IMPORTANT]
> **MANDATORY PROJECT INVARIANT:**  
> The ultimate state of truth for each and every phase of this project is strictly defined by the approved design, specification, and review artifacts in [`misc/`](file:///home/omprakash/Documents/jintru/misc):
> 1. [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) — Master Executable Design Specification & Interface Contracts
> 2. [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) — Architectural Concepts Brief
> 3. [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) — Research Foundations, ADRs & Baseline Bibliography
> 4. [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) — EGM Goldfish Review Protocol Master Sign-off
> 5. [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) — Final Contract Resolution Audit
>
> All phase planning, implementation tasks, code structures, and verifications **must** strictly adhere to these documents. No phase may deviate, improvise alternative architectures, or re-open locked architectural decisions.

---

## Requirements

### Validated

- [x] **REQ-FOUND-01**: Project scaffolding in `backend/pyproject.toml` with Python 3.12, FastAPI, Pydantic v2, `aiosqlite`, and clean dev tooling passing `ruff` and `pyright`.
- [x] **REQ-FOUND-02**: Typed configuration in `backend/app/core/config.py` with `Settings` capturing `BRAVE_API_KEY`, `META_API_KEY`, `META_API_BASE_URL`, `META_MODEL` (`muse-spark-1.3`), `REQUEST_DEADLINE_SECONDS` (8.0s), and `USE_MOCK_PROVIDERS`.
- [x] **REQ-FOUND-03**: Core Pydantic data schemas in `backend/app/api/schemas.py` including `VerificationRequest`, `SourceItem` (with `is_quarantined`, `relevance`, `exact_quote`), `ReasoningStatement` (with `quoted_excerpt`), `VerificationSynthesisPayload`, `VerificationResponse`, and `ErrorEnvelope`.
- [x] **REQ-DATA-01**: SQLite WAL persistence in `backend/app/db/database.py` with dedicated `@asynccontextmanager _connect()` executing connection-scoped `PRAGMA busy_timeout = 5000;`, `PRAGMA synchronous = NORMAL;`, and `PRAGMA journal_mode = WAL;`, bounded write retry, and JSON deserialization in `get_verification()`.
- [x] **REQ-PROV-01**: `BraveSearchProvider` in `backend/app/providers/brave.py` supporting `mode="snippets"` (`/res/v1/web/search`) and `mode="context"` (`/res/v1/llm/context` mapping `grounding.generic[].snippets` to `SourceItem`), with SHA-256 content hashes and domain/wire clustering.
- [x] **REQ-PROV-02**: `MetaModelProvider` in `backend/app/providers/meta.py` locked to `muse-spark-1.3` with `response_format` JSON schema matching strict `VerificationSynthesisPayload`, alongside deterministic mock providers in `mock.py`.

### Active

- [ ] **REQ-PIPE-01**: Conservative Gate A pre-retrieval classification in `backend/app/services/verification.py` using context-aware regex to catch subjective value judgments and future predictions (without false-positive rejection of entities like "Best Buy" or historical statements) to `not_verifiable` (0 search, 0 LLM calls).
- [ ] **REQ-PIPE-02**: Monotonic clock-bounded pipeline orchestrator enforcing 8.0s request ceiling: Stage 1 search (2.3s), unconditional Stage 2 dialectical counter-search if time ≥ 3.5s (`f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`), and clean fail-safe abort to HTTP 504 Gateway Timeout if synthesis window < 2.5s.
- [ ] **REQ-CITE-01**: Three-tier citation validation enforcing Tier 1 ID presence and Tier 2 normalized exact substring matching (`quoted_excerpt` in `snippet`) after HTML unescaping and whitespace/quote normalization.
- [ ] **REQ-POL-01**: Deterministic application-level verdict policy: strictly barring `supported` if credible, relevant counterevidence exists (`stance == "refutes"` with direct/contextual relevance), and enforcing the Two-Domain Corroboration Guardrail (≥ 2 distinct `source_family_id` clusters).
- [ ] **REQ-API-01**: FastAPI application in `backend/app/main.py` using modern `@asynccontextmanager lifespan` handler, CORS configuration, and domain error handlers mapping timeouts to HTTP 504.
- [ ] **REQ-API-02**: Complete REST endpoints in `backend/app/api/routes.py`: `POST /api/v1/verifications`, `GET /api/v1/verifications`, `GET /api/v1/verifications/{id}`, `DELETE /api/v1/verifications/{id}`, `DELETE /api/v1/verifications`, and `GET /api/v1/health`.
- [ ] **REQ-UI-01**: Next.js 16 + React 19 + TypeScript + stable Tailwind CSS v4 (`^4.3.3`) frontend application integration with typed API client (`frontend/lib/api.ts`).
- [ ] **REQ-UI-02**: Workbench claim input textarea with 500-character counter, submit action, and loading state with live elapsed timer and progress stages.
- [ ] **REQ-UI-03**: Accessible 5-way verdict badge pairing distinct colors with semantic icons and text labels (`supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo), summary narrative, and limitations accordion ("What remains unknown") wired to backend response.
- [ ] **REQ-UI-04**: Evidence cards (`SourceCard`) displaying retrieved sources with stance badges, canonical domains, wire attribution, quoted snippets, and safe external links (`rel="noopener noreferrer"`).
- [ ] **REQ-UI-05**: History sidebar drawer with real-time verification listing, individual deletion (`DELETE /api/v1/verifications/{id}`), and full purge controls (`DELETE /api/v1/verifications`).
- [ ] **REQ-TEST-01**: Unit test suite verifying citation normalization, budget enforcement, mock provider compliance, and 0 database lockups under 10 concurrent tasks.
- [ ] **REQ-TEST-02**: Playwright E2E tests validating CUJ 1 (claim submission to citation inspection) and CUJ 3 (abstention on absent evidence) across Chromium and Firefox.
- [ ] **REQ-SEC-01**: Security audits passing `semgrep --config auto backend/`, `pip-audit backend/`, and `npm --prefix frontend audit`.
- [ ] **REQ-EVAL-01**: Offline evaluation benchmark (`evals/run_evals.py` on `cases.jsonl`) verifying citation entailment precision ≥ 90%, false-support rate ≤ 5%, and counterevidence recall ≥ 80%.
- [ ] **REQ-EVAL-02**: Live WAN retrieval latency distribution benchmarking (P50, P90, P95) asserting 100% fail-safe degradation to HTTP 504 when synthesis window drops below 2.5s.

### Out of Scope

| Exclusion | Rationale |
|:---|:---|
| **Compound Claim Decomposition (FActScore)** | Reserved for Phase 2; Milestone 1 strictly verifies single atomic claims (≤ 500 chars). |
| **Raw HTML Web Crawling & Scraping** | Snippet-first ingestion eliminates SSRF attack vectors and TLS certificate validation hazards. |
| **Vector Databases & Local Embeddings** | Relies on real-time web retrieval; avoids vector DB maintenance and staleness. |
| **PDF Export & Batch Operations** | Web workbench and JSON REST API are sufficient for initial milestone. |
| **Multi-Agent Autonomous Loops** | Single-agent deterministic pipeline ensures predictable latency, inspectability, and reliability. |
| **Multi-Tenant User Accounts & Cloud Auth** | Operates in single-user local mode with complete local SQLite data sovereignty. |

---

## Context

The project operates as a specialized evidence workbench designed to solve the critical flaws of current AI fact-checkers: confirmation bias in search formulation, artificial consensus through syndicated reporting, uncalibrated hallucinated certainty, and SSRF vulnerabilities.

The project architecture has undergone a complete 5-stage EGM Goldfish Review Protocol, converging from an over-scoped 5-claim research proposal to a battle-tested Milestone 1 vertical slice.

---

## Constraints

- **Latency Budget**: Authoritative 8.0s synchronous HTTP request ceiling; requests abort cleanly to HTTP 504 if synthesis window drops below 2.5s.
- **Provider Interfaces**: External search via Brave Search API / LLM Context; model synthesis locked to Meta Model API (`muse-spark-1.3`).
- **Security Boundary**: Snippet-first ingestion only; zero raw HTML web crawling; prompt injection quarantine; no external telemetry.
- **Phase Granularity**: Consolidated into **4 coarse phases** to maintain high momentum and broad cohesive scope.
- **Single Source of Truth**: All work must strictly adhere to the verified designs in `misc/`.

---

## Key Decisions

| Decision | Rationale | Outcome |
|:---|:---|:---:|
| **Single Atomic Claim Scope (≤ 500 chars)** | Keeps execution strictly within 8.0s synchronous budget and eliminates NLP decomposition errors. | ✓ Good |
| **Snippet-First Ingestion** | Eliminates arbitrary URL crawling, userland socket IP-pinning, and SSRF attack surface. | ✓ Good |
| **Meta Model API Locked to `muse-spark-1.3`** | Officially documented base URL `https://api.meta.ai/v1`, Bearer auth, and strict `response_format` JSON schema. | ✓ Good |
| **Unconditional Dialectical Counter-Search** | When Stage 1 finds results and time ≥ 3.5s, counter-search runs unconditionally to eliminate confirmation bias. | ✓ Good |
| **Two-Domain Corroboration & Counterevidence Policy** | Barring `supported` if counterevidence exists or if evidence derives from only a single domain. | ✓ Good |
| **Flat SQLite Persistence in WAL Mode** | Eliminates relational join bugs and Alembic migration overhead for local single-user workbench. | ✓ Good |
| **4-Phase Coarse Milestone Structure** | Consolidates former 8 micro-phases into 4 broad, deliverable execution waves as requested by user. | ✓ Good |

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-31 after initialization*


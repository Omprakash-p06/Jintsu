# Requirements: Reality Check AI (`jintru`)

**Defined:** 2026-10-31  
**Core Value:** Show what supports a claim, what challenges it, how reliable that evidence is, and exactly what remains unknown.  
**Granularity:** Coarse (4 Consolidated Phases)

---

> [!IMPORTANT]
> **Ultimate State of Truth (Single Source of Truth — SSOT):**  
> All requirements below derive directly from the approved design and specification documents in [`misc/`](file:///home/omprakash/Documents/jintru/misc):
> - [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md)
> - [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md)
> - [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md)
> - [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md)
> - [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md)

---

## v1 Requirements

### Backend Foundations & Data Contracts

- [x] **FOUND-01**: Project scaffolding in `backend/pyproject.toml` with Python 3.12, FastAPI, Pydantic v2, `aiosqlite`, and clean dev tooling passing `ruff` and `pyright`.
- [x] **FOUND-02**: Typed configuration in `backend/app/core/config.py` with `Settings` capturing `BRAVE_API_KEY`, `META_API_KEY`, `META_API_BASE_URL`, `META_MODEL` (`muse-spark-1.3`), `REQUEST_DEADLINE_SECONDS` (8.0s), and `USE_MOCK_PROVIDERS`.
- [x] **FOUND-03**: Core Pydantic data schemas in `backend/app/api/schemas.py` including `VerificationRequest`, `SourceItem` (with `is_quarantined`, `relevance`, `exact_quote`), `ReasoningStatement` (with `quoted_excerpt`), `VerificationSynthesisPayload`, `VerificationResponse`, and `ErrorEnvelope`.
- [x] **DATA-01**: SQLite WAL persistence in `backend/app/db/database.py` with dedicated `@asynccontextmanager _connect()` executing connection-scoped `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;`, bounded write retry, and JSON deserialization in `get_verification()`.
- [x] **PROV-01**: `BraveSearchProvider` in `backend/app/providers/brave.py` supporting `mode="snippets"` (`/res/v1/web/search`) and `mode="context"` (`/res/v1/llm/context` mapping `grounding.generic[].snippets` to `SourceItem`), with SHA-256 content hashes and domain/wire clustering.
- [x] **PROV-02**: `MetaModelProvider` in `backend/app/providers/meta.py` locked to `muse-spark-1.3` with `response_format` JSON schema matching `VerificationSynthesisPayload`, alongside deterministic mock providers in `mock.py`.

### Verification Pipeline & Engine

- [x] **PIPE-01**: Conservative Gate A pre-retrieval classification in `backend/app/services/verification.py` using context-aware regex to catch subjective value judgments and future predictions (without false-positive rejection of entities like "Best Buy" or historical statements) to `not_verifiable` (0 search, 0 LLM calls).
- [x] **PIPE-02**: Monotonic clock-bounded pipeline orchestrator enforcing 8.0s request ceiling: Stage 1 search (2.3s), unconditional Stage 2 dialectical counter-search if time ≥ 3.5s (`f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`), and clean fail-safe abort to HTTP 504 Gateway Timeout if synthesis window < 2.5s.
- [x] **CITE-01**: Three-tier citation validation enforcing Tier 1 ID presence and Tier 2 normalized exact substring matching (`quoted_excerpt` in `snippet`) after HTML unescaping and whitespace/quote normalization.
- [x] **POL-01**: Deterministic application-level verdict policy: strictly barring `supported` if credible, relevant counterevidence exists (`stance == "refutes"` with direct/contextual relevance), and enforcing the Two-Domain Corroboration Guardrail (≥ 2 distinct `source_family_id` clusters).

### API Gateway & Endpoints

- [x] **API-01**: FastAPI application in `backend/app/main.py` using modern `@asynccontextmanager lifespan` handler, CORS configuration, and domain error handlers mapping timeouts to HTTP 504.
- [x] **API-02**: Complete REST endpoints in `backend/app/api/routes.py`: `POST /api/v1/verifications`, `GET /api/v1/verifications`, `GET /api/v1/verifications/{id}`, `DELETE /api/v1/verifications/{id}`, `DELETE /api/v1/verifications`, and `GET /api/v1/health`.

### Workbench Frontend

- [x] **UI-01**: Next.js 16 + React 19 + TypeScript + stable Tailwind CSS v4 (`^4.3.3`) frontend application integration with typed API client (`frontend/lib/api.ts`).
- [x] **UI-02**: Workbench claim input textarea with 500-character counter, submit action, and loading state with live elapsed timer and progress stages.
- [x] **UI-03**: Accessible 5-way verdict badge pairing semantic icons with explicit color tokens (`supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo), summary narrative, and limitations accordion ("What remains unknown") wired to backend response.
- [x] **UI-04**: Evidence cards (`SourceCard`) displaying retrieved sources with stance badges, canonical domains, wire attribution, quoted snippets, and safe external links (`rel="noopener noreferrer"`).
- [x] **UI-05**: History sidebar drawer with real-time verification listing, individual deletion (`DELETE /api/v1/verifications/{id}`), and full purge controls (`DELETE /api/v1/verifications`).

### Quality, Verification & Benchmarks

- [ ] **TEST-01**: Unit test suite verifying citation normalization, budget enforcement, mock provider compliance, and 0 database lockups under 10 concurrent tasks.
- [ ] **TEST-02**: Playwright E2E tests validating CUJ 1 (claim submission to citation inspection) and CUJ 3 (abstention on absent evidence) across Chromium and Firefox against the wired full-stack app.
- [ ] **SEC-01**: Security audits passing `semgrep --config auto backend/`, `pip-audit backend/`, and `npm --prefix frontend audit`.
- [ ] **EVAL-01**: Offline evaluation benchmark (`evals/run_evals.py` on `cases.jsonl`) verifying citation entailment precision ≥ 90%, false-support rate ≤ 5%, and counterevidence recall ≥ 80%.
- [ ] **EVAL-02**: Live WAN retrieval latency distribution benchmarking (P50, P90, P95) asserting 100% fail-safe degradation to HTTP 504 when synthesis window drops below 2.5s.

---

## v2 Requirements

### Advanced Claim Analysis (Deferred to Milestone 2)
- **DEC-01**: Compound proposition decomposition using FActScore to split complex multi-predicate statements into atomic claims.
- **MEDIA-01**: Multimodal evidence ingestion for image, chart, and audio verification.
- **EXP-01**: PDF and CSV verification report exports.
- **AUTH-01**: Multi-tenant user accounts and cloud history synchronization.

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Raw HTML Web Crawling & Scraping | Snippet-first ingestion via Brave eliminates userland socket SSRF risks and TLS cert issues. |
| Vector Databases & Local Embeddings | Real-time web retrieval is essential for fresh factual assertions; avoids stale vector corpora. |
| Autonomous Multi-Agent Negotiation Swarms | A single-agent deterministic pipeline ensures predictable latency, debuggability, and 8.0s SLA compliance. |
| Arbitrary Numerical Credibility Scores | Replaced by transparent source categories, canonical domains, and wire attribution tracking. |

---

## Traceability

| Requirement | Phase | Status |
|:---|:---|:---:|
| **FOUND-01** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **FOUND-02** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **FOUND-03** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **DATA-01** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **PROV-01** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **PROV-02** | Phase 1: Foundations, Data Contracts & External Providers | Satisfied |
| **PIPE-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **PIPE-02** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **CITE-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **POL-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **API-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **API-02** | Phase 2: Verification Engine, Citation Validation & API Gateway | Satisfied |
| **UI-01** | Phase 3: Frontend Wiring & Full-Stack Integration | Satisfied |
| **UI-02** | Phase 3: Frontend Wiring & Full-Stack Integration | Satisfied |
| **UI-03** | Phase 3: Frontend Wiring & Full-Stack Integration | Satisfied |
| **UI-04** | Phase 3: Frontend Wiring & Full-Stack Integration | Satisfied |
| **UI-05** | Phase 3: Frontend Wiring & Full-Stack Integration | Satisfied |
| **TEST-01** | Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking | Pending |
| **TEST-02** | Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking | Pending |
| **SEC-01** | Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking | Pending |
| **EVAL-01** | Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking | Pending |
| **EVAL-02** | Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-31*  
*Last updated: 2026-11-01 after Phase 3 execution (UI-01..UI-05 satisfied at source/type level; `next build` and browser verification blocked on Node >= 20.9.0)*


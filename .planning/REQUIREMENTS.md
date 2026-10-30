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

- [ ] **PIPE-01**: Conservative Gate A pre-retrieval classification in `backend/app/services/verification.py` using context-aware regex to catch subjective value judgments and future predictions (without false-positive rejection of entities like "Best Buy" or historical statements) to `not_verifiable` (0 search, 0 LLM calls).
- [ ] **PIPE-02**: Monotonic clock-bounded pipeline orchestrator enforcing 8.0s request ceiling: Stage 1 search (2.3s), unconditional Stage 2 dialectical counter-search if time ≥ 3.5s (`f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`), and clean fail-safe abort to HTTP 504 Gateway Timeout if synthesis window < 2.5s.
- [ ] **CITE-01**: Three-tier citation validation enforcing Tier 1 ID presence and Tier 2 normalized exact substring matching (`quoted_excerpt` in `snippet`) after HTML unescaping and whitespace/quote normalization.
- [ ] **POL-01**: Deterministic application-level verdict policy: strictly barring `supported` if credible, relevant counterevidence exists (`stance == "refutes"` with direct/contextual relevance), and enforcing the Two-Domain Corroboration Guardrail (≥ 2 distinct `source_family_id` clusters).

### API Gateway & Endpoints

- [ ] **API-01**: FastAPI application in `backend/app/main.py` using modern `@asynccontextmanager lifespan` handler, CORS configuration, and domain error handlers mapping timeouts to HTTP 504.
- [ ] **API-02**: Complete REST endpoints in `backend/app/api/routes.py`: `POST /verifications`, `GET /verifications`, `GET /verifications/{id}`, `DELETE /verifications/{id}`, `DELETE /verifications`, and `GET /health`.

### Workbench Frontend

- [ ] **UI-01**: Vite + React 19 + TypeScript 5.6 + stable Tailwind CSS v4 (`^4.0.0`) frontend application scaffolding with typed fetch client.
- [ ] **UI-02**: Workbench input textarea with 500-character counter, submit action, and loading state with live elapsed timer.
- [ ] **UI-03**: Accessible 5-way verdict badge (`VerdictCard.tsx`) pairing distinct colors with semantic icons and text labels (`supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo), summary, and limitations accordion.
- [ ] **UI-04**: Evidence cards (`EvidenceList.tsx`) displaying retrieved sources with stance badges, canonical domains, quoted snippets, and safe external links (`rel="noopener noreferrer"`).
- [ ] **UI-05**: History sidebar drawer (`HistoryPanel.tsx`) with individual verification deletion and full purge controls.

### Quality, Verification & Benchmarks

- [ ] **TEST-01**: Unit test suite verifying citation normalization, budget enforcement, mock provider compliance, and 0 database lockups under 10 concurrent tasks.
- [ ] **TEST-02**: Playwright E2E tests validating CUJ 1 (claim submission to citation inspection) and CUJ 3 (abstention on absent evidence) across Chromium and Firefox.
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
| **FOUND-01** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **FOUND-02** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **FOUND-03** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **DATA-01** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **PROV-01** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **PROV-02** | Phase 1: Foundations, Data Contracts & External Providers | Pending |
| **PIPE-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **PIPE-02** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **CITE-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **POL-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **API-01** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **API-02** | Phase 2: Verification Engine, Citation Validation & API Gateway | Pending |
| **UI-01** | Phase 3: React Workbench UI & Full-Stack Integration | Pending |
| **UI-02** | Phase 3: React Workbench UI & Full-Stack Integration | Pending |
| **UI-03** | Phase 3: React Workbench UI & Full-Stack Integration | Pending |
| **UI-04** | Phase 3: React Workbench UI & Full-Stack Integration | Pending |
| **UI-05** | Phase 3: React Workbench UI & Full-Stack Integration | Pending |
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
*Last updated: 2026-10-31 after initialization*


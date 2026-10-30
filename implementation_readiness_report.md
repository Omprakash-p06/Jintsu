# Implementation Readiness Review Report: `docs/designs/jintru_claim_verification.md`

**Auditors:** Pragmatic Tech Lead (`egm-implementation-readiness`), Pedantic Technical Quality Auditor (`egm-codebase-details`), Technical Copy Editor (`egm-style`)  
**Standard Applied:** [Implementation Readiness Standard](file:///home/omprakash/.gemini/config/plugins/egm/resources/document_standards/implementation-readiness-standard.md) (The Zero-Decision Rule)  
**Target Document:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)  
**Target Scope:** `DetailedRange` (Lines 438–518: Detailed Implementation Plan & Verification Plan)  
**Reference Documents:** [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md), [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md)  
**Stage:** Stage 9 (Detailed Scope Review)  
**Overall Verdict:** 🔴 **FAIL (NOT READY FOR IMPLEMENTATION UNDER ZERO-DECISION RULE)**

---

## 1. Executive Summary

Under the **Zero-Decision Rule**, an implementation plan passes only if a competent engineer (or fresh AI coding session) unfamiliar with the codebase can execute the plan and produce the correct changes on the first attempt without guessing, asking clarifying questions, or making independent architectural or design choices.

The current `Detailed Implementation Plan` (Lines 438–518) fails this standard across three parallel review lenses:
1. **Unordered Flat File Inventory:** Lines 438–493 present an unordered inventory of one-line file summaries with zero phased execution sequence, no dependency graph, and no incremental build/test milestones.
2. **Missing Core Services & Scaffolding:** Services featured in the architecture diagram and CUJs (`Conflict Resolver`, `Evidence Gap Diagnoser`, and LLM prompt modules) are completely missing from the backend plan. The frontend plan lists feature components but omits mandatory Vite/TypeScript scaffolding files (`vite.config.ts`, `tsconfig.json`, `index.html`, `App.tsx`, `main.tsx`).
3. **Broken Runtime Dependencies & Commands:** The plan hard-codes `fastapi==0.162.0` without `pydantic-settings` (crashing FastAPI startup), omits `uvicorn`, references non-existent files (`backend/requirements.txt`, `backend/scripts/check_openapi_drift.py`), and invokes root-level commands (`npx playwright test`) that fail in a monorepo structure.
4. **Abstract Verification & Evaluation:** Test specifications lack concrete payloads, status codes, and mock assertions. Benchmark instructions call `python evals/run_evals.py` to "satisfy agreed baseline thresholds" without defining numerical pass/fail thresholds.

---

## 2. Prioritized Findings Matrix

| ID | Severity | Lens | Affected Scope | Title / Summary |
| :--- | :--- | :--- | :--- | :--- |
| **IR-01** | 🔴 Blocker | Tech Lead | Lines 438–493 | Flat file list lacks phased, dependency-ordered implementation waves |
| **IR-02** | 🔴 Blocker | Tech Lead | Lines 461–470 | Missing mandatory services: `Conflict Resolver` & `Evidence Gap Diagnoser` |
| **IR-03** | 🔴 Blocker | Quality Auditor | Line 443 | `pydantic-settings` missing from dependencies (crashes startup on Pydantic v2) |
| **IR-04** | 🔴 Blocker | Quality Auditor / Copy Editor | Lines 477–485 | Incomplete frontend application skeleton & missing Vite/TypeScript scaffolding |
| **IR-05** | 🔴 Blocker | Copy Editor / Quality Auditor | Lines 457, 507 | API route contract inconsistency (`POST /export`) & missing drift script declaration |
| **IR-06** | 🔴 Blocker | Tech Lead | Lines 442–485 | File summaries lack class interfaces, method signatures, inputs, and return types |
| **IR-07** | 🟡 Major | Quality Auditor | Line 443 | Missing ASGI server (`uvicorn`) in `pyproject.toml` |
| **IR-08** | 🟡 Major | Quality Auditor / Copy Editor | Lines 443, 504 | Dependency tooling contradiction: `pyproject.toml` vs non-existent `requirements.txt` |
| **IR-09** | 🟡 Major | Quality Auditor | Lines 452–454 | SQLite async concurrency, missing WAL mode, and foreign key cascade omission |
| **IR-10** | 🟡 Major | Quality Auditor | Lines 443, 466, 469 | Missing MinHash (`datasketch`) and HTML parsing (`beautifulsoup4`) dependencies |
| **IR-11** | 🟡 Major | Quality Auditor | Line 447, Lines 285–299 | HTTPX IP-pinning TLS/SNI certificate verification gotcha |
| **IR-12** | 🟡 Major | Tech Lead / Quality Auditor | Lines 487–488, 499–501 | Abstract test plan lacking test fixtures, boundary values, and mock assertions |
| **IR-13** | 🟡 Major | Tech Lead / Copy Editor | Lines 489–490, 513 | Undefined benchmark schema and missing numerical CI baseline thresholds |
| **IR-14** | 🟡 Major | Copy Editor | Line 511 | Frontend Playwright execution context discrepancy (`npx playwright test` vs `npm --prefix frontend`) |
| **IR-15** | 🟢 Nit | Quality Auditor | Line 443 | Unverified exact FastAPI version pinning (`fastapi==0.162.0`) |
| **IR-16** | 🟢 Nit | Copy Editor | Line 464 | Unescaped LaTeX math syntax (`$\le 5$`) |
| **IR-17** | 🟢 Nit | Quality Auditor | Lines 491, 511 | Playwright browser binary installation missing from CI plan |
| **IR-18** | 🟢 Nit | Copy Editor | Line 517 | Meta boilerplate watermark (`*Drafted with EGM*`) |

---

## 3. Detailed Audit Findings

### 🔴 Blockers

#### IR-01: Flat File List Lacks Phased, Dependency-Ordered Implementation Waves
* **Reviewer Lens:** Pragmatic Tech Lead (`egm-implementation-readiness`)
* **Affected Scope:** Lines 438–493 (`Target Files to Create / Modify`)
* **Discrepancy:** The plan lists target files in a flat categorization grouped by architectural layers (Backend Core, Schemas, Routes, Services, Adapters, Frontend, Tests). There is no execution sequence, no dependency graph, and no incremental phasing. An engineer starting at item 1 cannot compile or test anything until all 23 files are written.
* **Remediation:** Replace the static file list with an ordered, phased execution plan partitioned into 8 incremental stages, where each stage leaves the repository buildable and testable:
  - Phase 1: Project Scaffolding & Core Foundations
  - Phase 2: Data Models & Persistence
  - Phase 3: External Provider Adapters & Mock Harness
  - Phase 4: Request Budget & Security Utilities
  - Phase 5: Pipeline Services
  - Phase 6: Pipeline Orchestration & API Routes
  - Phase 7: Frontend Application Shell & Components
  - Phase 8: End-to-End Tests & CI Benchmark Harness

#### IR-02: Missing Mandatory Core Pipeline Services (`Conflict Resolver` & `Evidence Gap Diagnoser`)
* **Reviewer Lens:** Pragmatic Tech Lead (`egm-implementation-readiness`)
* **Affected Scope:** Lines 461–470 (`Pipeline Services & Logic`), Lines 87, 96, 147, 183–186
* **Discrepancy:** Section 1 flowchart specifies `ConflictMod[Conflict & Disagreement Resolver]`, CUJ 2 invokes the Conflict Resolver to assign `mixed`, and CUJ 3 invokes the `Evidence Gap Diagnoser`. Neither service is listed under `backend/app/services/`.
* **Remediation:** Explicitly declare `backend/app/services/conflict.py` (with class `ConflictResolver` and method `resolve_conflicts`) and `backend/app/services/gap_diagnoser.py` (with class `EvidenceGapDiagnoser` and method `diagnose_gap`), or explicitly specify their inlined locations if unified per Intermediate Zoom Out.

#### IR-03: `pydantic-settings` Missing from Dependencies
* **Reviewer Lens:** Pedantic Technical Quality Auditor (`egm-codebase-details`)
* **Affected Scope:** Line 443 (`backend/pyproject.toml`), Line 445 (`backend/app/core/config.py`)
* **Discrepancy:** In Pydantic v2 (`>=2.0`), `BaseSettings` and `.env` parsing were split into an independent library: `pydantic-settings`. Calling `from pydantic_settings import BaseSettings` without `pydantic-settings` installed raises an immediate `ModuleNotFoundError: No module named 'pydantic_settings'`, preventing FastAPI from starting.
* **Remediation:** Add `pydantic-settings>=2.5` to `backend/pyproject.toml`.

#### IR-04: Missing Critical Frontend Scaffolding, TypeScript, and Build Files
* **Reviewer Lens:** Pedantic Technical Quality Auditor (`egm-codebase-details`) & Copy Editor (`egm-style`)
* **Affected Scope:** Lines 477–485 (`Frontend Application`), Lines 498, 501, 511
* **Discrepancy:** The plan lists `frontend/package.json` and five isolated React components, but omits:
  - `frontend/index.html` (Vite SPA HTML entry point)
  - `frontend/vite.config.ts` (Build config, React plugin, and `/api/v1` proxy)
  - `frontend/tsconfig.json` & `frontend/tsconfig.node.json` (Required for `npm run typecheck`)
  - `frontend/src/main.tsx` & `frontend/src/App.tsx` (Root React DOM mount)
  - `frontend/src/index.css` (Tailwind CSS v4 `@import "tailwindcss";` entry point)
  - `frontend/playwright.config.ts` (Required for Playwright E2E tests)
* **Remediation:** Declare all 7 missing frontend scaffolding files in the manifest.

#### IR-05: Route Contract Inconsistency & Missing Drift Script Declaration
* **Reviewer Lens:** Technical Copy Editor (`egm-style`) & Quality Auditor (`egm-codebase-details`)
* **Affected Scope:** Line 457 (`backend/app/api/routes/verifications.py`), Line 507
* **Discrepancy:** Line 457 lists `POST /export` in `verifications.py`, dropping the canonical prefix `/api/v1` and the required resource ID parameter `{id}` (specified in Section 8 as `POST /api/v1/verifications/{id}/export`). Furthermore, Line 507 mandates executing `python backend/scripts/check_openapi_drift.py`, but this script is never declared in the file manifest.
* **Remediation:** Standardize route paths to `POST /api/v1/verifications/{id}/export` (or prune if cutting export per Intermediate Zoom Out), and declare `backend/scripts/check_openapi_drift.py` under a dedicated `Tooling & Automation Scripts` section.

#### IR-06: File Summaries Lack Method Signatures, Types, and Concrete Contracts
* **Reviewer Lens:** Pragmatic Tech Lead (`egm-implementation-readiness`)
* **Affected Scope:** Lines 442–485
* **Discrepancy:** The file descriptions are descriptive one-liners without class names, function signatures, input parameters, or return types. An implementer must invent all interfaces.
* **Remediation:** Provide concrete Python typing and abstract base classes for all provider adapters (`SearchProvider`, `ModelProvider`), pipeline services (`SufficiencyGate`, `CitationValidator`), and request handlers.

---

### 🟡 Majors

#### IR-07: Missing ASGI Server (`uvicorn`) in `backend/pyproject.toml`
* **Affected Scope:** Line 443
* **Discrepancy:** FastAPI does not include an ASGI server. Without `uvicorn`, the backend cannot be launched locally (`uvicorn app.main:app`) or spawned in CI test suites.
* **Remediation:** Add `uvicorn[standard]>=0.30` to `backend/pyproject.toml`.

#### IR-08: `pip-audit` Targets Non-Existent `requirements.txt`
* **Affected Scope:** Line 443 vs Line 504
* **Discrepancy:** Line 504 instructs `pip-audit -r backend/requirements.txt`, but packaging uses `backend/pyproject.toml`. No `requirements.txt` exists.
* **Remediation:** Update command to `pip-audit --project backend/`.

#### IR-09: SQLite Async Concurrency, Missing WAL Mode, and Foreign Key Cascade Omission
* **Affected Scope:** Lines 452–454, Lines 362, 434
* **Discrepancy:** SQLite in async mode (`aiosqlite`) defaults to disabled foreign keys (causing cascading deletes to orphan child records) and `journal_mode=DELETE` (locking the DB file during concurrent writes). Furthermore, default Alembic `env.py` is synchronous and crashes on `sqlite+aiosqlite://`.
* **Remediation:** Explicitly mandate that `backend/app/db/session.py` register an engine event listener setting `PRAGMA foreign_keys=ON;`, `PRAGMA journal_mode=WAL;`, and `PRAGMA busy_timeout=5000;`, and specify that Alembic use the async template.

#### IR-10: Missing MinHash and HTML Text Extraction Dependencies
* **Affected Scope:** Line 443, Line 466, Line 469
* **Discrepancy:** The plan specifies 64-bit MinHash text fingerprinting (Line 466) and full-page HTML text extraction (Line 469), but `backend/pyproject.toml` omits `datasketch` and HTML extraction libraries (`beautifulsoup4` or `selectolax`).
* **Remediation:** Add `datasketch>=1.6` and `beautifulsoup4>=4.12` to `pyproject.toml` (or adopt the Skeptical Architect's recommendation to replace MinHash with token-set Jaccard and drop raw HTML extraction in favor of Brave snippets).

#### IR-11: HTTPX IP-Pinning TLS/SNI Host Mismatch Gotcha
* **Affected Scope:** Line 447, Lines 285–299
* **Discrepancy:** Connecting directly to an IP over HTTPS (e.g., `http://198.51.100.24:443/article` with `Host: example.com`) causes Python's `ssl` module to validate the certificate against the IP address rather than `example.com`, throwing `SSLCertVerificationError`.
* **Remediation:** Detail the SSL context `server_hostname` override in `backend/app/core/security.py`, or adopt the Skeptical Architect's recommendation to eliminate raw web page fetching entirely.

#### IR-12: Abstract Test Plan Lacking Fixtures and Assertions
* **Affected Scope:** Lines 487–488, 499–501
* **Discrepancy:** Unit test descriptions list covered areas without providing concrete test case names, mock payloads, or expected assertion values.
* **Remediation:** Detail specific test cases for SSRF IP blocking, budget pre-reservation exhaustion, normalized citation matching, and API endpoint integration.

#### IR-13: Undefined Benchmark Schema and Missing Numerical CI Baseline Thresholds
* **Affected Scope:** Lines 489–490, 513
* **Discrepancy:** Line 513 mandates verifying that reasoning and retrieval "satisfy agreed baseline thresholds", but no numerical thresholds are defined anywhere in the plan.
* **Remediation:** Define the exact JSON schema for `evals/cases.jsonl` and document numerical CI pass criteria: Citation Entailment Precision $\ge 90\%$, False-Support Rate $\le 5\%$, Counterevidence Recall $\ge 80\%$.

#### IR-14: Frontend Playwright Execution Context Discrepancy
* **Affected Scope:** Line 511
* **Discrepancy:** Frontend commands use `npm --prefix frontend run <cmd>`, but Line 511 invokes `npx playwright test` directly from root, failing to locate `frontend/tests/e2e/`.
* **Remediation:** Update command to `npm --prefix frontend run test:e2e -- --project=chromium,firefox`.

---

### 🟢 Nits

#### IR-15: Exact FastAPI Version Pinning `fastapi==0.162.0`
* **Affected Scope:** Line 443
* **Discrepancy:** Hard-pins an unverified version `0.162.0` while other packages use ranges.
* **Remediation:** Use `fastapi>=0.115.0,<1.0.0`.

#### IR-16: Unescaped LaTeX Math Syntax
* **Affected Scope:** Line 464
* **Discrepancy:** Uses raw LaTeX `$\le 5$` in plain markdown.
* **Remediation:** Replace with Unicode `≤ 5`.

#### IR-17: Playwright Browser Binary Installation Missing from CI Plan
* **Affected Scope:** Lines 491, 511
* **Discrepancy:** Running Playwright tests without installing browser binaries fails in fresh environments.
* **Remediation:** Add `npx playwright install --with-deps chromium firefox` to the setup step.

#### IR-18: Meta Boilerplate Watermark Fluff
* **Affected Scope:** Line 517
* **Discrepancy:** Trailing `*Drafted with EGM*` watermark adds no technical value.
* **Remediation:** Delete line 517.


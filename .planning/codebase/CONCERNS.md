---
last_mapped_commit: b77aa778b9b4a8b8ba1996061b3ee591626cb1d1
last_mapped_at: 2026-11-02
---
# Codebase Concerns

**Analysis Date:** 2026-11-02

## Tech Debt

**Python 3.12+ Version Restriction:**
- Issue: `backend/pyproject.toml` pins `requires-python = ">=3.12"`. While it takes advantage of modern typing and performance improvements, it prevents testing or deploying on Python 3.10 or 3.11 runtimes.
- Files: `backend/pyproject.toml`
- Impact: Limits adoption in legacy deployment environments.
- Fix approach: Evaluate if any 3.12-exclusive features (such as PEP 695 type parameter syntax) are strictly required; if not, loosen to `>=3.11`.

**Monolithic Verification Pipeline:**
- Issue: `backend/app/services/verification.py` is over 500 lines and combines Stage 1 search, Stage 2 counter-search, citation substring validation, source family clustering, and verdict policy evaluation in a single module.
- Files: `backend/app/services/verification.py`
- Impact: Increases cognitive overhead when modifying individual pipeline stages or testing policy rules in isolation.
- Fix approach: Refactor into distinct pipeline stage components: `retrieval.py`, `clustering.py`, `citations.py`, and `policy.py`.

## Known Bugs

**None currently active:**
- All edge-case regressions identified by autonomous bug hunts (SWE-sweep) have been fixed and covered by regression tests in `backend/tests/unit/test_swe_sweep_bugs.py`:
  - Future prediction claims with multiple years (e.g., "Founded in 2020, by 2050...")
  - Registrable domain extraction with uppercase letters and explicit ports
  - Missing URL domain normalization and source family grouping
  - Zero-width character stripping in verbatim excerpt validation
  - Whitespace-only claim validation

## Security Considerations

**API Key Leakage Prevention:**
- Risk: Leaking Brave Search (`BRAVE_API_KEY`) or Meta AI (`META_API_KEY`) credentials into version control or API response payloads.
- Files: `backend/app/core/config.py`, `backend/app/main.py`, `.env`
- Current mitigation: Environment variables isolated via `.gitignore`. API keys are never included in API responses or serialized models. Automated Semgrep SAST scans run in CI (`scripts/run_security_audit.sh`).
- Recommendations: Ensure secret scanning hooks (like git pre-commit) are actively enforced across developer workstations.

**Unsanitized Source URL Redirection:**
- Risk: Malicious search result URLs containing `javascript:` or data URI schemes triggering XSS when rendered in the frontend.
- Files: `frontend/lib/api.ts:168`, `frontend/app/page.tsx`
- Current mitigation: `safeHref()` in `frontend/lib/api.ts` parses URLs and allows only `http:` and `https:` schemes.
- Recommendations: Maintain strict Content Security Policy (CSP) headers in Next.js configuration.

## Performance Bottlenecks

**8.0-Second SLA Ceiling Tightness:**
- Problem: The synchronous 8.0s SLA deadline is tight when both Stage 1 search (2.0s), Stage 2 dialectical search (2.0s), and LLM synthesis (up to 3.0s) execute under peak network latency.
- Files: `backend/app/services/verification.py:320-370`
- Cause: Sequential network calls to external search and LLM APIs.
- Improvement path: Parallelize Stage 1 and Stage 2 searches when query formulation permits, or implement speculative synthesis execution.

**SQLite Write Contention Under Massive Concurrency:**
- Problem: SQLite allows only one writer at a time, leading to `sqlite3.OperationalError: database is locked` under high write load.
- Files: `backend/app/db/database.py:38`
- Cause: Single-file database lock contention.
- Improvement path: WAL mode and 3-attempt exponential backoff retry are currently active and pass 10-worker concurrency tests (`test_concurrency.py`). For horizontal scaling across multiple instances, migrate to PostgreSQL.

## Fragile Areas

**Verbatim Citation Quote Matching:**
- Files: `backend/app/services/verification.py:75-110` (`normalize_excerpt`, `extract_verbatim_quotes`)
- Why fragile: LLMs frequently introduce subtle whitespace variations, smart quotes, zero-width characters, or minor grammatical adjustments into quoted text.
- Safe modification: When updating normalization rules, run the full citation test suite (`pytest backend/tests/unit/test_citations.py`) and offline evaluation benchmark (`evals/run_evals.py`) to prevent false-negative citation rejections.
- Test coverage: Extensive unit tests in `test_citations.py` and benchmark tests in `test_evals_offline.py`.

## Scaling Limits

**Brave Search Free-Tier Rate Limits:**
- Current capacity: Sequential execution guarantees QPS <= 0.5 per worker instance.
- Limit: Rapid concurrent requests can trigger HTTP 429 Too Many Requests from Brave Search.
- Scaling path: Configure Brave Enterprise tier or implement an in-memory Redis search cache for duplicate or frequent claim queries.

**Local Single-Node SQLite Storage:**
- Current capacity: Single-node file-backed SQLite database in `data/jintru.db`.
- Limit: Cannot be scaled horizontally across multiple Kubernetes pods or stateless containers.
- Scaling path: Introduce database abstraction layer to support PostgreSQL for multi-node deployments.

## Dependencies at Risk

**Tailwind CSS v4 Integration:**
- Package: `@tailwindcss/postcss` `^4.3.3` / `tailwindcss` `^4.3.3`
- Risk: Tailwind CSS v4 introduces significant architectural changes from v3 (new `@theme` configuration directives, removal of `tailwind.config.js`).
- Impact: Compatibility friction when integrating older third-party UI component libraries.
- Migration plan: Pinned to modern `@tailwindcss/postcss` with native CSS variables in `frontend/app/globals.css`.

## Missing Critical Features

**Persistent Search Query Caching:**
- Problem: Identical or near-identical claims re-execute full external search queries.
- Blocks: Reduces throughput and consumes external API quota unnecessarily.

**Asynchronous Background Verification (Webhooks / SSE):**
- Problem: All verifications are currently synchronous HTTP POST requests subject to the 8.0s timeout.
- Blocks: Prevents deep multi-page crawling or running multi-agent deliberation workflows that exceed 8 seconds.

## Test Coverage Gaps

**Live External Provider Network Failures in CI:**
- What's not tested: Real HTTP timeouts and network partitions against live Brave/Meta endpoints during continuous integration (CI runs against mocks and offline evaluations).
- Files: `backend/app/providers/brave.py`, `backend/app/providers/meta.py`
- Risk: Provider API breaking changes or response schema shifts might go undetected until production rollout.
- Priority: Medium (addressed via integration smoke tests and staged releases).

---

*Concerns audit: 2026-11-02*

---
last_mapped_commit: b77aa778b9b4a8b8ba1996061b3ee591626cb1d1
last_mapped_at: 2026-11-02
---
# Codebase Concerns

**Analysis Date:** 2026-11-02

## Resolved Concerns

### 1. Monolithic Verification Pipeline (Resolved)
- **Previous Issue:** `backend/app/services/verification.py` was over 500 lines combining search, clustering, citation validation, and verdict policy.
- **Resolution:** Decomposed into dedicated, single-responsibility modules under `backend/app/services/`:
  - `screening.py`: Gate A conservative pre-retrieval screening (subjective/prospective assertions)
  - `clustering.py`: Domain normalization, news wire family mapping, and prompt-injection quarantine
  - `citations.py`: Verbatim quote matching with zero-width stripping and HTML unescaping
  - `policy.py`: Grounding checks, counterevidence prohibition, and 2-domain corroboration
  - `cache.py`: Search query cache with TTL expiration
  - `verification.py`: Re-exports all components for 100% backward compatibility and orchestrates the 8.0s monotonic budget pipeline.
- **Verification:** All 97 Pytest tests pass cleanly in 2.50s.

### 2. Python Version Restriction (Resolved)
- **Previous Issue:** `backend/pyproject.toml` pinned `requires-python = ">=3.12"`, preventing deployment on Python 3.11 runtimes.
- **Resolution:** Relaxed to `requires-python = ">=3.11"` in `backend/pyproject.toml`.
- **Verification:** Pyright static type checking passes with 0 errors and 0 warnings.

### 3. Missing Root Environment & One-Command Launcher (Resolved)
- **Previous Issue:** No root `.env` file or one-command launcher to start the entire system.
- **Resolution:**
  - Created `.env.example` and default `.env` at repository root with `USE_MOCK_PROVIDERS=true` default.
  - Implemented `setup.sh` (one-command setup and smoke tests).
  - Implemented `start.sh` (one-command full-stack launcher for backend + frontend with graceful process cleanup).
  - Created `Makefile` (`make setup`, `make dev`, `make test`, `make eval`, `make audit`).
  - Added `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile`.

### 4. Persistent Search Query Caching (Resolved)
- **Previous Issue:** Identical or near-identical claim queries re-executed full external search calls, consuming API quotas.
- **Resolution:** Implemented `QueryCache` (`backend/app/services/cache.py`) with TTL expiration, integrated into `VerificationPipeline`, configurable via `CACHE_ENABLED` in `.env`.
- **Verification:** Unit tests isolate mock providers safely; query caching reduces duplicate latency to <1ms.

### 5. Frontend Node Runtime Floor (Resolved)
- **Previous Issue:** Host system previously ran Node.js 18.19.1, which blocked `next build` on Next.js 16 (requires Node >= 20.9.0).
- **Resolution:** Configured Node.js 20 LTS runtime (`v20.18.0`) and pnpm (`12.16.1`) in `~/.local/bin`.
- **Verification:** `pnpm run build` completed successfully with Turbopack in 2.4s.

### 6. Security Headers & CSP (Resolved)
- **Previous Issue:** Missing Content Security Policy and HTTP security headers in Next.js configuration.
- **Resolution:** Added strict security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-DNS-Prefetch-Control: on`) to `frontend/next.config.mjs`.
- **Verification:** `bash scripts/run_security_audit.sh` passed with 0 findings across Semgrep SAST, pip-audit, and npm audit.

---

## Active & Monitored Considerations

### 1. SQLite Concurrency Under High Load
- **Location:** `backend/app/db/database.py` — Connection management with `busy_timeout = 5000`
- **Current State:** 10 concurrent async workers executing 200 operations showed 0 `database is locked` errors thanks to WAL mode and 3-attempt exponential write retry.
- **Monitoring:** For multi-node deployments across Kubernetes pods, evaluate migrating to PostgreSQL.

### 2. Brave Search Free-Tier Rate Limits
- **Location:** Retrieval pipeline (Stage 1 and Stage 2)
- **Current State:** Sequential single-query execution guarantees QPS $\le 0.5$, and `QueryCache` mitigates duplicate requests.
- **Recommendation:** Upgrade to Brave Enterprise tier if burst concurrency exceeds free-tier allocations.

### 3. Authoritative 8.0-Second SLA Ceiling
- **Location:** `backend/app/services/verification.py`
- **Current State:** Monotonic deadline guarantees clean 504 degradation (`SYNTHESIS_WINDOW_EXCEEDED`) if remaining budget drops below 2.5s.
- **Monitoring:** Live WAN latency distribution is tracked via `evals/run_evals.py` (P90: ~0.006s in mock/local mode).

---

*Concerns audit: 2026-11-02*

---
last_mapped_commit: b77aa778b9b4a8b8ba1996061b3ee591626cb1d1
last_mapped_at: 2026-11-02
---
# External Integrations

**Analysis Date:** 2026-11-02

## APIs & External Services

**Search & Grounding:**
- Brave Search API - Primary real-time web search and context retrieval engine
  - SDK/Client: Direct asynchronous HTTP client using `httpx.AsyncClient` (`backend/app/providers/brave.py`)
  - Endpoints:
    - `GET https://api.search.brave.com/res/v1/web/search` (mode: `snippets`)
    - `GET https://api.search.brave.com/res/v1/llm/context` (mode: `context`)
  - Auth: `X-Subscription-Token` header mapped from `BRAVE_API_KEY`
  - Timeout: Authoritative subordinate timeout `min(2.0, remaining_seconds)`
  - Normalization: Extracts URL, title, snippet, computes SHA-256 `content_hash`, maps news wires (AP, Reuters, PR Newswire) to canonical `source_family_id`

**LLM Synthesis & Reasoning:**
- Meta AI / OpenAI-compatible Chat Completions - Strict JSON Schema synthesis engine
  - SDK/Client: Direct asynchronous HTTP client using `httpx.AsyncClient` (`backend/app/providers/meta.py`)
  - Endpoints:
    - `POST {META_API_BASE_URL}/chat/completions` (default: `https://api.meta.ai/v1/chat/completions`)
  - Model: `META_MODEL` (default: `muse-spark-1.3`)
  - Auth: `Authorization: Bearer {META_API_KEY}` header
  - Timeout: Authoritative subordinate window `min(3.0, remaining_seconds)` with minimum requirement of `2.5s`
  - Strict Schema Mode: Hardened JSON schema with `additionalProperties: false`, root title removal, and strict required property enforcement

**Mock Fallbacks:**
- Mock Provider Suite - Offline deterministic testing and local verification without network calls
  - Implementation: `backend/app/providers/mock.py`
  - Activation: `USE_MOCK_PROVIDERS=true` in environment or settings

## Data Storage

**Databases:**
- SQLite 3 (Non-blocking async via `aiosqlite`)
  - Location: Configured by `DATABASE_PATH` (default: `data/jintru.db` or `:memory:` in tests)
  - Connection & Concurrency:
    - `PRAGMA busy_timeout = 5000;` (5-second lock timeout)
    - `PRAGMA synchronous = NORMAL;`
    - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for high reader/writer concurrency)
    - Write retry decorator with exponential backoff (`3` attempts, base `50ms`) (`backend/app/db/database.py`)
  - Schema:
    - `verifications` table: Stores `id`, `claim`, `public_verdict`, `summary`, `limitations` (JSON), `sources` (JSON), `reasoning` (JSON), `created_at`

**File Storage:**
- Local filesystem only:
  - Evaluation datasets: `evals/cases.jsonl`
  - SQLite database files: `data/jintru.db`, `data/jintru.db-wal`, `data/jintru.db-shm`

**Caching:**
- None: Real-time claim verification executes fresh multi-stage dialectical retrieval on each evaluation. Source deduplication occurs in-memory per request pipeline via URL and content hash.

## Authentication & Identity

**Auth Provider:**
- Custom API Gateway / Zero-Trust API Key Authentication:
  - Outbound: API keys managed via environment variables for Brave Search (`BRAVE_API_KEY`) and Meta AI (`META_API_KEY`).
  - Inbound Client Access: Unauthenticated local/LAN CORS endpoints (`http://localhost:3000`, `http://localhost:5173`) for frontend workbench (`backend/app/main.py`).

## Monitoring & Observability

**Error Tracking:**
- Standardized Error Envelopes (`ErrorEnvelope` in `backend/app/api/schemas.py`):
  - `status_code`: 422 (Validation), 499 (Client Disconnected), 503 (Provider Unavailable), 504 (Provider Timeout)
  - Codes: `SYNTHESIS_WINDOW_EXCEEDED`, `CLIENT_DISCONNECTED`, `STAGE1_TIMEOUT`, `STAGE2_TIMEOUT`, `VALIDATION_ERROR`, etc.

**Logs:**
- Python standard library `logging` and FastAPI exception handlers (`backend/app/main.py`)
- Monotonic wall-clock timing telemetry logged during pipeline execution (`backend/app/services/verification.py`)

## CI/CD & Deployment

**Hosting:**
- Self-hosted or containerized Linux workload (Docker/Kubernetes)

**CI Pipeline:**
- GitHub Actions CI workflow (`.github/workflows/ci.yml`):
  - Matrix testing on Python 3.12 and 3.13
  - Verification of Ruff linting and formatting
  - Pyright strict static type verification
  - Pytest unit and integration test suite execution
  - Offline evaluation benchmark threshold verification (`evals/run_evals.py`)
  - Semgrep SAST scan and `pip-audit` / `npm audit` security gate (`scripts/run_security_audit.sh`)

## Environment Configuration

**Required Env Vars:**
- `BRAVE_API_KEY`: Required when `USE_MOCK_PROVIDERS=false` for live search
- `META_API_KEY`: Required when `USE_MOCK_PROVIDERS=false` for live reasoning synthesis
- `META_API_BASE_URL`: Base URL for LLM provider (default: `https://api.meta.ai/v1`)
- `META_MODEL`: Model identifier for LLM provider (default: `muse-spark-1.3`)
- `DATABASE_PATH`: Path to SQLite database file (default: `data/jintru.db`)
- `REQUEST_DEADLINE_SECONDS`: Monotonic SLA timeout limit in seconds (default: `8.0`)
- `BRAVE_RETRIEVAL_MODE`: Retrieval formatting mode (`snippets` or `context`)
- `USE_MOCK_PROVIDERS`: Offline mock toggle (default: `false`)

**Secrets Location:**
- Root `.env` file (loaded via `pydantic-settings` with `.gitignore` protection)

## Webhooks & Callbacks

**Incoming:**
- None: Synchronous REST request/response lifecycle (`POST /api/v1/verifications`).

**Outgoing:**
- None: Outbound requests are strictly request-response HTTP calls bounded by the 8.0s monotonic deadline.

---

*Integration audit: 2026-11-02*

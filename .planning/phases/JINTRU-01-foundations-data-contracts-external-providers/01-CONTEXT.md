# Phase 1: Foundations, Data Contracts & External Providers - Context

**Gathered:** 2026-10-31  
**Status:** Ready for planning  
**Phase Directory:** `JINTRU-01-foundations-data-contracts-external-providers`

<domain>
## Phase Boundary

Phase 1 establishes the backend foundation, data contracts, persistence layer, and external search/synthesis provider adapters for Reality Check AI (`jintru`). It delivers a compiling, testable Python 3.12 workspace that establishes prerequisites for Phase 2 verification pipeline orchestration.

</domain>

<decisions>
## Implementation Decisions

### Project Scaffolding & Tooling (REQ-FOUND-01)
- **D-01 (Python & Packaging):** Use Python 3.12 with `hatchling` as the build backend in `backend/pyproject.toml` with explicit `[tool.hatch.build.targets.wheel] packages = ["app"]`.
- **D-02 (Core Dependencies):** `fastapi>=0.115.0,<1.0.0`, `uvicorn[standard]>=0.30.0`, `pydantic>=2.9.0`, `pydantic-settings>=2.5.0`, `httpx>=0.27.0`, `aiosqlite>=0.20.0`.
- **D-03 (Dev Dependencies):** `ruff>=0.6.0`, `pyright>=1.1.380`, `pytest>=8.3.0`, `pytest-asyncio>=0.24.0`, `pip-audit>=2.7.0`, `semgrep>=1.80.0`. Standardize provider unit testing on `httpx.MockTransport` and `unittest.mock` (zero extra dependencies; omit `respx`).
- **D-04 (Pytest Config):** `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`, `testpaths = ["tests"]`, `pythonpath = ["."]`, supplemented by `backend/tests/conftest.py` ensuring `backend/` is on `sys.path`.

### Configuration (REQ-FOUND-02)
- **D-05 (Settings):** `backend/app/core/config.py` inherits from `BaseSettings` (`pydantic-settings`):
  - `BRAVE_API_KEY: str = ""`
  - `META_API_KEY: str = ""`
  - `META_API_BASE_URL: str = "https://api.meta.ai/v1"`
  - `META_MODEL: str = "muse-spark-1.3"`
  - `DATABASE_PATH: str = "data/jintru.db"`
  - `REQUEST_DEADLINE_SECONDS: float = 8.0`
  - `BRAVE_RETRIEVAL_MODE: str = "snippets"`
  - `USE_MOCK_PROVIDERS: bool = False`

### Pydantic Data Contracts (REQ-FOUND-03)
- **D-06 (Data Models in `backend/app/api/schemas.py`):**
  - `PublicVerdict = Literal["supported", "contradicted", "mixed", "insufficient_evidence", "not_verifiable"]`
  - `SourceStance = Literal["supports", "refutes", "neutral"]`
  - `VerificationRequest`: `claim: str` (min_length=5, max_length=500).
  - `SourceItem`: Includes `source_id`, `url`, `domain`, `title`, `snippet`, `stance`, `source_family_id`, `retrieved_at`, `published_at`, `source_type`, `content_hash`, `extraction_status`, `is_quarantined: bool = False`, `relevance: Optional[Literal["direct", "indirect", "contextual", "irrelevant"]] = None`, `exact_quote: Optional[str] = None`.
  - `ReasoningStatement`: Includes `statement: str`, `citation_ids: list[str] = Field(default_factory=list)`, `quoted_excerpt: Optional[str] = None`.
  - `SourceEvaluationItem`: Schema matching Meta LLM synthesis item evaluation (`source_id`, `stance`, `relevance`, `exact_quote`, `relationship_explanation`).
  - `VerificationSynthesisPayload`: Proposed verdict, summary, limitations, source evaluations, reasoning statements, temporal qualification, abstention reason.
  - `VerificationResponse`: `id: str`, `claim: str`, `public_verdict: PublicVerdict`, `summary: str`, `limitations: list[str]`, `sources: list[SourceItem]`, `reasoning: list[ReasoningStatement]`, `created_at: str`.
  - `VerificationListItem`: `id: str`, `claim: str`, `public_verdict: PublicVerdict`, `created_at: str`.
  - `PaginatedVerificationResponse`: `items: list[VerificationListItem]`, `total: int`.
  - `HealthResponse`: `status: str`, `providers: dict[str, str]`.
  - `ErrorEnvelope`: `error: str`, `code: str`, `detail: Optional[str] = None`.

### SQLite Persistence (REQ-DATA-01)
- **D-07 (Connection Configuration & Pragmas):** `backend/app/db/database.py` defines `@asynccontextmanager async def _connect(self)` that executes `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;` on **every** opened connection.
- **D-08 (WAL Mode):** `init_db()` executes `PRAGMA journal_mode=WAL;` and creates table `verifications` with JSON columns (`limitations`, `sources`, `reasoning`). Explicitly call `await db.commit()` on DDL/DML executions.
- **D-09 (JSON Deserialization):** `Database.get_verification(id)` parses `limitations`, `sources`, and `reasoning` via `json.loads()` before returning dict rows.
- **D-10 (Write Retry):** Bounded exponential backoff (up to 3 retries with 50ms base backoff) on `sqlite3.OperationalError` write contention. Test suites use `tmp_path` fixture files rather than `:memory:` to preserve multi-connection state.

### External Providers & Mocks (REQ-PROV-01, REQ-PROV-02)
- **D-11 (Abstract Interfaces):** `backend/app/providers/base.py`:
  - `SearchProvider.search(query: str, count: int = 5, mode: str = "snippets", timeout: float = 3.0) -> list[dict]`
  - `ModelProvider.synthesize(claim: str, snippets: list[dict], timeout: float = 4.0) -> VerificationSynthesisPayload`
- **D-12 (Brave Search Adapter):** `backend/app/providers/brave.py`:
  - `mode == "snippets"`: Queries `https://api.search.brave.com/res/v1/web/search`.
  - `mode == "context"`: Queries `https://api.search.brave.com/res/v1/llm/context` and extracts passages under `grounding.generic[].snippets` into `SourceItem.snippet`, concatenating multiple passages per URL item with `"\n\n"`. Explicitly slice final extracted passages to `[:count]` to enforce the ≤ 5 snippet retrieval invariant.
  - Common normalization: `source_id = f"src_{idx+1}"`, `domain = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")`, SHA-256 `content_hash = hashlib.sha256(snippet.encode()).hexdigest()`.
  - Wire attribution tokens mapped with regex word boundaries to prevent false substring matches (e.g., "AP" in "Apple" or "API"):
    `r"\b(?:Associated Press|AP)\b" -> "associated_press"`, `r"\bReuters\b" -> "reuters"`, `r"\bPR Newswire\b" -> "pr_newswire"`.
- **D-13 (Meta Model Adapter):** `backend/app/providers/meta.py`:
  - Queries `POST {settings.META_API_BASE_URL}/chat/completions` via `async with httpx.AsyncClient() as client:` with Bearer auth, model `muse-spark-1.3`, `temperature: 0.0`.
  - Formats chat messages: `[{"role": "system", "content": "..."}, {"role": "user", "content": "Claim: {claim}\n\nEvidence Snippets:\n..."}]`. Encloses snippets in `<evidence_snippet id="{src_id}">`.
  - Enforces structured JSON output via `response_format: {"type": "json_schema", "json_schema": {"name": "verification_synthesis", "strict": True, "schema": VerificationSynthesisPayload.model_json_schema()}}`.
  - Unpacks completion content at `response.json()["choices"][0]["message"]["content"]` and validates via `VerificationSynthesisPayload.model_validate_json()`.
- **D-14 (Deterministic Mocks & Factory):** `backend/app/providers/mock.py` and factory functions in `backend/app/providers/__init__.py`:
  - `MockSearchProvider`: returns 2 distinct domain snippets (`example.com`, `reuters.com`) with valid SHA-256 hashes and `stance="supports"`.
  - `MockModelProvider`: returns deterministic `VerificationSynthesisPayload` with `proposed_verdict="supported"`.
  - Provider factory functions: `get_search_provider(settings)` and `get_model_provider(settings)` routing to mock or real provider instances based on `settings.USE_MOCK_PROVIDERS`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Executable Specification & Interface Contracts
- `misc/docs/designs/jintru_claim_verification.md` § 3.6, § 3.7 — Network boundary, flat SQLite schema, and provider security
- `misc/docs/designs/jintru_claim_verification.md` § Phase 1 — Project Scaffolding & Core Foundations (`pyproject.toml`, `config.py`, `errors.py`)
- `misc/docs/designs/jintru_claim_verification.md` § Phase 2 — Persistence & Data Contracts (`schemas.py`, `database.py`)
- `misc/docs/designs/jintru_claim_verification.md` § Phase 3 — External Provider Adapters & Deterministic Mocks (`base.py`, `brave.py`, `meta.py`, `mock.py`)

### Architectural Decisions & Standards
- `misc/docs/designs/concepts_brief.md` § ADR-001, ADR-003 — Bounded retrieval and snippet-first ingestion
- `misc/docs/specification.md` § ADR-003, ADR-004 — Security boundaries and structured synthesis contracts

### Audit & Review Resolutions
- `misc/consolidated_review_report.md` § Traceability Matrix — Findings IR-01 (ReasoningStatement excerpt), IR-02 (SQLite pragmas & JSON decoding), IR-04 (subordinate timeouts), IR-06 (build-system & pytest), IR-07 (mock toggle), IR-18 (Meta API contract), IR-20 (Brave LLM context mapping)
- `misc/goldfish_review_report.md` — Item 1 (Meta API contract), Item 3 (Brave LLM Context mapping)
- `AGENTS.md` — Repository Engineering Rules 1, 4, 5, 9, 10

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None (Greenfield backend).

### Established Patterns
- Monorepo layout with `backend/` root.
- Strict Pydantic v2 schemas for all API and DB interfaces.
- Connection-scoped SQLite pragmas using context managers.

</code_context>

<deferred>
## Deferred Ideas

- Verification pipeline orchestration, Gate A pre-retrieval classification, and dialectical search (deferred to Phase 2).
- FastAPI gateway routes and endpoints (deferred to Phase 2).
- React 19 Frontend workbench (deferred to Phase 3).
- Offline evals and Playwright test automation (deferred to Phase 4).

</deferred>

---

*Phase: JINTRU-01-foundations-data-contracts-external-providers*  
*Context gathered: 2026-10-31*


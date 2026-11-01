---
last_mapped_commit: 4f658919c9cc583eaac17089285a1e895b404205
last_mapped_at: 2026-11-02
---
# Testing Patterns

**Analysis Date:** 2026-11-02

## Test Framework

**Runner:**
- Backend: Pytest `>=8.3.0` with `pytest-asyncio>=0.24.0`
- Config: `backend/pyproject.toml` under `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`, `testpaths = ["tests"]`)
- Frontend: Playwright `@playwright/test` `^1.64.1` with `frontend/playwright.config.ts`

**Assertion Library:**
- Standard Python `assert` with pytest failure introspection
- Playwright `expect()` matchers for E2E assertions

**Run Commands:**

```bash
# Run all backend unit & integration tests (97 tests)
pytest backend/tests

# Run unit tests only
pytest backend/tests/unit

# Run concurrency & integration tests
pytest backend/tests/integration

# Check backend code style, formatting, and types
ruff check backend/ && ruff format --check backend/ && pyright -p backend

# Check frontend lint and typecheck
pnpm --prefix frontend run lint && pnpm --prefix frontend run typecheck

# Build frontend production bundle
pnpm --prefix frontend run build

# Run offline factuality and SLA benchmark evaluation (27 cases)
python evals/run_evals.py --cases evals/cases.jsonl

# Run frontend Playwright E2E tests
pnpm --prefix frontend test:e2e

# Run security SAST & vulnerability audits
bash scripts/run_security_audit.sh
```

## Test File Organization

**Location:**
- Backend: Separate root `backend/tests/` hierarchy split into `unit/` and `integration/`
- Frontend: `frontend/tests/e2e/` for browser end-to-end scenarios

**Naming:**
- Backend: `test_*.py` matching the subsystem tested (`test_budget.py`, `test_citations.py`, `test_concurrency.py`)
- Frontend: `*.spec.ts` (`workbench.spec.ts`)

**Structure:**

```
backend/tests/
├── conftest.py                  # Global test fixtures and environment overrides
├── integration/
│   ├── test_api.py              # HTTP client tests for FastAPI endpoints
│   └── test_concurrency.py      # Multi-worker async SQLite lock contention tests
└── unit/
    ├── test_budget.py           # Monotonic deadline and timeout guard enforcement
    ├── test_citations.py        # Strict verbatim substring quote matching
    ├── test_classification.py   # Empirical vs. subjective/prospective filtering
    ├── test_db.py               # Database CRUD, migration, and retry logic
    ├── test_evals_offline.py    # Offline evaluation SLA and accuracy metrics
    ├── test_pipeline.py         # Verification pipeline execution
    ├── test_policy.py           # Verdict policy rules and limitations
    ├── test_providers.py        # Brave, Meta, and Mock provider tests
    ├── test_schemas.py          # Request validation, bounds, and error envelopes
    └── test_swe_sweep_bugs.py   # Regressions and edge cases discovered by SWE-sweep
```

## Test Structure

**Suite Organization:**

```python
import pytest
from app.api.schemas import VerificationRequest
from app.services.verification import VerificationPipeline

@pytest.mark.asyncio
async def test_claim_verification_flow(test_db, mock_pipeline):
    """Verify standard empirical claim produces supported verdict with citations."""
    claim = "The speed of light in vacuum is approximately 299,792 km/s."
    response = await mock_pipeline.verify(claim)
    assert response.public_verdict == "supported"
    assert len(response.sources) >= 2
    assert len(response.reasoning) > 0
```

**Patterns:**
- **Setup Pattern:** Fixtures in `conftest.py` instantiate in-memory SQLite instances (`:memory:`) or isolated test databases.
- **Teardown Pattern:** Automatic resource cleanup handled by pytest fixture context managers.
- **Assertion Pattern:** Assert public verdict, presence of limitations, source family independence, and exact error envelope codes.

## Mocking

**Framework:**
- Native custom mock classes implementing ABC interfaces (`MockSearchProvider`, `MockModelProvider` in `backend/app/providers/mock.py`)
- `unittest.mock.patch` and `unittest.mock.AsyncMock` for simulating network delays or clock manipulation.

**Patterns:**

```python

# Testing synthesis timeout guard via simulated clock advancement

from unittest.mock import patch

with patch("time.monotonic", side_effect=[0.0, 5.6, 5.7, 5.8]):
    with pytest.raises(ProviderTimeoutError) as exc_info:
        await pipeline.verify(claim)
    assert exc_info.value.code == "SYNTHESIS_WINDOW_EXCEEDED"
```

**What to Mock:**
- Outbound third-party network requests (Brave Search API, Meta AI completion endpoints)
- Time advances when testing SLA timeout boundaries and latency limits

**What NOT to Mock:**
- The database: Use real `aiosqlite` with `:memory:` or temporary SQLite files to test real SQL queries, migrations, and concurrency locks
- Verification policy logic: Never mock `apply_verdict_policy`, `group_sources`, or `classify_input`
- JSON Schema serialization and Pydantic validation

## Fixtures and Factories

**Test Data:**
- Curated ground truth evaluation cases located in `evals/cases.jsonl`
- Reusable fixtures defined in `backend/tests/conftest.py` (`test_db`, `mock_search`, `mock_model`)

**Location:**
- `backend/tests/conftest.py`: Root pytest fixtures
- `evals/cases.jsonl`: Standardized evaluation dataset

## Coverage

**Requirements:**
- High test coverage across verification policy, budget guards, citation validation, and API schemas
- Offline evaluation metrics: Citation precision >= 90%, false-support rate <= 5%, counterevidence recall >= 80%

**View Coverage:**

```bash
pytest --cov=backend/app backend/tests
```

## Test Types

**Unit Tests:**
- Test individual algorithmic components in isolation: `test_citations.py`, `test_budget.py`, `test_classification.py`, `test_policy.py`.
- Fast execution with zero external I/O.

**Integration Tests:**
- Test end-to-end API routes via `httpx.AsyncClient` with ASGI transport: `test_api.py`.
- Test multi-worker SQLite concurrent write contention under load: `test_concurrency.py` (spawns 10 parallel workers running 200 operations).

**E2E Tests:**
- Playwright browser tests in `frontend/tests/e2e/workbench.spec.ts` verifying UI form submission, verdict card rendering, and citation expansion.

## Common Patterns

**Async Testing:**

```python
@pytest.mark.asyncio
async def test_concurrent_writes(database):
    tasks = [database.insert_verification(record) for record in records]
    results = await asyncio.gather(*tasks)
    assert len(results) == len(records)
```

**Error Testing:**

```python
@pytest.mark.asyncio
async def test_empty_whitespace_claim_rejected():
    with pytest.raises(ValidationError):
        VerificationRequest(claim="   \t\n  ")
```

---

*Testing analysis: 2026-11-02*

---
phase: JINTRU-01-foundations-data-contracts-external-providers
reviewed: 2026-10-30T21:21:09Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - .gitignore
  - backend/app/__init__.py
  - backend/app/api/__init__.py
  - backend/app/api/schemas.py
  - backend/app/core/__init__.py
  - backend/app/core/config.py
  - backend/app/core/errors.py
  - backend/app/db/__init__.py
  - backend/app/db/database.py
  - backend/app/providers/__init__.py
  - backend/app/providers/base.py
  - backend/app/providers/brave.py
  - backend/app/providers/meta.py
  - backend/app/providers/mock.py
  - backend/pyproject.toml
  - backend/tests/__init__.py
  - backend/tests/conftest.py
  - backend/tests/unit/__init__.py
  - backend/tests/unit/test_db.py
  - backend/tests/unit/test_providers.py
  - backend/tests/unit/test_schemas.py
  - implementation_readiness_report.md
findings:
  critical: 1
  warning: 4
  info: 7
  total: 12
status: issues_found
---

# Phase JINTRU-01: Code Review Report

**Reviewed:** 2026-10-30T21:21:09Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Phase 1 delivers the FastAPI-backend scaffolding, Pydantic data contracts, aiosqlite WAL persistence, and Brave/Meta provider adapters. Cross-referenced against the SSOT contract (`misc/docs/designs/jintru_claim_verification.md`) and `AGENTS.md` engineering rules.

Overall the implementation is a faithful, quality execution of the SSOT reference code: the schema definitions match §7/§8 field-for-field, the readiness report's blockers (unbounded LLM-context retrieval — sliced via `brave.py:128`; wire-token substring collides — fixed with word-boundary regex at `brave.py:12-16`) and majors (pytest discovery, provider factories, `tmp_path` isolation) are all addressed. Pragmas (`busy_timeout`, `synchronous`) run per-connection as `AGENTS.md` Rule 10 mandates, the retry loop is bounded at 3 attempts, and all 20 tests pass.

That said, the review surfaced one genuine crash-path defect (unhandled exceptions on anomalous provider payloads escape as raw `ValueError`/`AttributeError`, breaking the structured-error-envelope reliability contract), a strict-mode structured-output schema that will likely be rejected by the Meta API on every production synthesis call, blanket retry semantics in the persistence layer, and SLA-budget drift latent in the provider interface defaults. These must be fixed before Phase 2 builds on top of this code.

No source files were modified during this review. Verification run: `pytest -q` → 20 passed in 0.23s (backend/.venv).

## Critical Issues

### CR-01: Anomalous provider payloads escape as unhandled raw exceptions instead of the structured error envelope

**File:** `backend/app/providers/brave.py:55,71,82,88` and `backend/app/providers/meta.py:75,90`

**Issue:** Both providers only catch `httpx.TimeoutException` and `(httpx.HTTPStatusError, httpx.RequestError)`. Everything that happens *after* a successful HTTP response is unguarded against payload anomalies:

1. `brave.py:55` / `meta.py:75` — `response.json()` raises `json.JSONDecodeError` (a `ValueError`, not a `RequestError`) when the provider returns HTTP 200 with a malformed body. It propagates to the caller uncaught, bypassing the `ProviderUnavailableError` mapping entirely.
2. `brave.py:71` / `brave.py:82` — `data.get("grounding", {})` / `data.get("web", {})` return **None** when the JSON body contains `"grounding": null` or `"web": null`; the subsequent `.get("generic", [])` then raises raw `AttributeError: 'NoneType' object has no attribute 'get'`.
3. `meta.py:90` — `content` can be a non-string (e.g. `choices[].message.content` as null); `model_validate_json(None)` raises raw `pydantic_core.ValidationError`.

SSOT § Non-Functional Requirements ("Fault Containment: Unhandled exceptions or provider outages return structured error envelopes (`PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`) rather than 500 server crashes") and the `ProviderUnavailableError` docstring ("HTTP **or connection error**") promise this class of failure is contained. Demonstrably it is not: a single 200-with-garbage response from Brave or Meta surfaces as a 500 to the client. The existing unit tests (200 + well-formed bodies, and transport-level timeout/HTTP-status errors) never exercise this gap.

**Fix:**

```python
# brave.py — wrap response decode + shape in the same try as the request
        try:
            if self._client is not None:
                response = await self._client.get(url, params=params, headers=headers, timeout=timeout)
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                raise ProviderUnavailableError(
                    "Brave returned a malformed JSON body",
                    code="BRAVE_UNAVAILABLE", detail=str(exc),
                ) from exc
            if not isinstance(data, dict):
                raise ProviderUnavailableError(
                    "Brave response payload is not an object",
                    code="BRAVE_UNAVAILABLE", detail=f"got {type(data).__name__}",
                )
        except httpx.TimeoutException as exc:
            ...
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            ...

        # null-shape tolerance at the extraction site
        if mode == "context":
            generic = (data.get("grounding") or {}).get("generic") or []
        else:
            results = (data.get("web") or {}).get("results") or []
```

Apply the analogous guard in `meta.py` (guard the `data["choices"][0]["message"]["content"]` chain — that block exists but is entered only for `ValueError`-class failures; ensure `response.json()` decode is inside it or similarly wrapped, and validate `isinstance(data, dict)` before key access).

## Warnings

### WR-01: `strict: true` structured-output schema is non-conformant — pydantic `model_json_schema()` output will likely be rejected on every synthesis call

**File:** `backend/app/providers/meta.py:50-57`

**Issue:** The payload embeds `VerificationSynthesisPayload.model_json_schema()` raw. Strict structured-output APIs (the OpenAI-compatible contract `api.meta.ai/v1` is modeled on) require: (a) `additionalProperties: false` on *every* object schema including `$defs`/nested ones, and (b) every property listed in `required`. The pydantic-generated schema satisfies neither: default-valued fields (`limitations`, `source_evaluations`, `reasoning_statements`, `temporal_qualification`, `abstention_reason`) are omitted from `required`, no `additionalProperties` keys are emitted, and nested `$defs` entries (`SourceEvaluationItem`, `ReasoningStatement`) inherit both defects. If the Meta API enforces strict-mode validation, **every** production synthesis call fails with a 400 before any LLM inference happens — and no test catches it because `httpx.MockTransport` accepts whatever the handler builds. SSOT §5 mandates exactly this `response_format` shape, so the schema content, not the transport, is the defect.

**Fix:** Author the JSON Schema explicitly (or post-process the pydantic schema), e.g.:

```python
def _strict_json_schema() -> dict:
    schema = VerificationSynthesisPayload.model_json_schema()

    def harden(node: dict) -> dict:
        if node.get("type") == "object":
            props = node.get("properties", {})
            node["additionalProperties"] = False
            node["required"] = list(props.keys())
        for value in node.get("properties", {}).values():
            harden(value)
        for value in node.get("$defs", {}).values():
            harden(value)
        return node

    schema.pop("title", None)
    return harden(schema)

# in the payload:
"json_schema": {"name": "verification_synthesis", "strict": True, "schema": _strict_json_schema()},
```

Also add a unit test asserting every object node in the emitted schema carries `additionalProperties: False` and a complete `required` list, so regression is caught offline.

### WR-02: Blanket `sqlite3.OperationalError` retry retries non-contention errors; delete/purge bypass retry entirely

**File:** `backend/app/db/database.py:52-80,121-130`

**Issue:** The SSOT §7 / Risk table scope the 3-attempt backoff to **write-lock contention** (`database is locked`). `save_verification` however retries *any* `OperationalError` — verified empirically: after dropping the table, a save burns ~0.16s of the 8.0s SLA through 3 futile retries before re-raising (`no such table`). Real contention errors, non-locking failures, and programming errors are conflated; transient disk-full / I/O errors get retried too. Conversely, `delete_verification` and `purge_verifications` perform writes with **zero** retry, so contention on a delete raises `database is locked` straight out of the persistence layer. Inconsistent handling of the same failure mode across methods.

**Fix:**

```python
import time

def _is_contention(exc: sqlite3.OperationalError) -> bool:
    msg = str(exc).lower()
    return "locked" in msg or "busy" in msg

async def save_verification(self, record: VerificationResponse) -> None:
    last: Exception | None = None
    for attempt in range(3):
        try:
            async with self._connect() as db:
                await db.execute(...)
                await db.commit()
                return
        except sqlite3.OperationalError as exc:
            if not _is_contention(exc):
                raise                      # no-such-table, disk I/O, etc. — fail fast
            last = exc
            await asyncio.sleep(0.05 * (2 ** attempt))
    raise last  # pragma: no cover — all 3 contention retries exhausted
```

Extract the loop into a shared `_with_write_retry(coro_gen)` helper and use it in `save_verification`, `delete_verification`, and `purge_verifications`.

### WR-03: Unknown Brave retrieval `mode` silently executes the snippets branch — config typos are masked

**File:** `backend/app/providers/brave.py:36-44` (also `backend/app/core/config.py:13`)

**Issue:** The `else` branch (lines 42-44) duplicates the snippets branch verbatim, so `mode="contexts"`, `mode="snipets"`, or any typo in `BRAVE_RETRIEVAL_MODE` silently falls back to snippets mode with no log and no error. `BRAVE_RETRIEVAL_MODE` is typed as plain `str` in `Settings`, so a mis-set environment variable (the design intends `"snippets" | "context"` per OQ-1) produces a silently different retrieval strategy — a benchmark/perf-eval mode drift that Phase 8 will be unable to diagnose.

**Fix:** Fail fast and validate at both layers:

```python
# config.py
BRAVE_RETRIEVAL_MODE: Literal["snippets", "context"] = "snippets"

# brave.py
if mode == "snippets":
    ...
elif mode == "context":
    ...
else:
    raise RequestConstraintError(
        f"Unsupported Brave retrieval mode: {mode!r}",
        code="BRAVE_BAD_MODE",
    )
```

Delete the duplicated third branch (it is currently dead-by-equivalence).

### WR-04: Provider interface timeout defaults (3.0s search / 4.0s synthesis) exceed their SLA stage budgets — the contract depends entirely on Phase 2 remembering to override

**File:** `backend/app/providers/base.py:8-15,18-26`

**Issue:** The SSOT SLA layout allocates 2.3s to Stage-1 search (with a 2.0s subordinate timeout) and 3.0s to synthesis under an unyielding 8.0s ceiling, yet the abstract interfaces default to `timeout: float = 3.0` (search) and `timeout: float = 4.0` (synthesis). These are the values the SSOT's own Phase-3 contract specifies, so the adapters are conformant — but any Phase 2/5 call site that relies on these defaults makes the worst-case budget exceed the SLA even before the counter-search stage (0.2 + 3.0 + 2.0 + 4.0 = 9.2s), which only the 504-orchestrator could mask. This is a latent SLA-breach trap: correctness hinges on every future caller remembering `min(stage_timeout, remaining_time)` (SSOT "Timeout Governance").

**Fix:** Tighten the defaults to the budgeted values and document the orchestrator override obligation:

```python
class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, count: int = 5, mode: str = "snippets",
                     timeout: float = 2.0) -> list[dict]:
        """Search external index. NOTE: callers must pass
        min(stage_budget, remaining_time); the default equals the
        Stage-1 subordinate ceiling, never the 8.0s request budget."""
```

(same treatment for `synthesize`, default `3.0`), or — stronger — assert in the adapters that `timeout <= REQUEST_DEADLINE_SECONDS - already_consumed` and raise `ProviderTimeoutError` if not.

## Info

### IN-01: Overbroad `except Exception` conflates coding errors with provider response faults

**File:** `backend/app/providers/meta.py:92`
**Issue:** The parse block catches `Exception`, so an `AttributeError` introduced by a later refactor is misreported as `META_UNAVAILABLE` provider outage, muddying diagnostics. Also, LLM content routinely arrives wrapped in markdown fences (```json … ```), which `model_validate_json` rejects — surviving responses could fail at this boundary.
**Fix:** Narrow to `except (KeyError, IndexError, TypeError, ValidationError)`; strip code fences (`content.strip().removeprefix("```json").removesuffix("```")`) before `model_validate_json`.

### IN-02: `PRAGMA journal_mode=WAL` is set only in `init_db`, not per-connection as the SSOT's §7 wording prescribes

**File:** `backend/app/db/database.py:20-25,29`
**Issue:** SSOT §7 states "All SQLite connections enforce" all three pragmas. Since WAL mode is persisted in the database header, setting it once in `init_db` is functionally sufficient *provided* `init_db` is always invoked before any other operation — which is currently implicit, never asserted.
**Fix:** Either document the initializer obligation on `Database.__init__` (docstring: "call `init_db` before any CRUD use"), or move `PRAGMA journal_mode=WAL;` into `_connect()` for literal SSOT conformance.

### IN-03: `Database.__init__` binds the settings snapshot at import time

**File:** `backend/app/db/database.py:14`
**Issue:** `db_path: str = settings.DATABASE_PATH` evaluates the default once at class-definition/import time; later mutation of `settings.DATABASE_PATH` (e.g. in tests or tooling) is ignored by `Database()`.
**Fix:** Use a sentinel: `def __init__(self, db_path: str | None = None): self.db_path = db_path or settings.DATABASE_PATH`.

### IN-04: Duplicate/dead `PRAGMA synchronous` execution in the pragma test

**File:** `backend/tests/unit/test_db.py:28-30`
**Issue:** Line 28 executes `PRAGMA synchronous;` and assigns a cursor that is immediately overwritten on line 29; the first execution is dead. The dead cursor is also unfetched, which makes the unread rows incidental.
**Fix:** Delete line 28's execute and keep the single live one.

### IN-05: Raw `sqlite3.OperationalError` propagates from the persistence layer unwrapped

**File:** `backend/app/db/database.py:79,123,130`
**Issue:** After the retry budget is exhausted, `save_verification` re-raises a raw `sqlite3.OperationalError`; deletes/purges raise immediately. The domain-error discipline established in `core/errors.py` (and the "structured error envelopes rather than 500 server crashes" reliability requirement) starts at the API layer in Phase 5, but the persistence layer is the natural boundary to translate storage failures into a `JintruError` subtype so Phase 2/5 handlers have one uniform fault model.
**Fix:** Wrap final failures: `raise ProviderUnavailableError("Verification persistence failed", code="DB_WRITE_FAILED", detail=str(exc)) from exc` (or introduce a dedicated `PersistenceError(JintruError)`).

### IN-06: Redundant `@pytest.mark.asyncio` decorators under `asyncio_mode = "auto"`

**File:** `backend/tests/unit/test_providers.py:24,43,77,117,163,195,220,278`
**Issue:** `pyproject.toml:33` sets `asyncio_mode = "auto"`, so every `@pytest.mark.asyncio` is a redundant no-op that can invite confusion when mixed with plain async tests elsewhere.
**Fix:** Remove the decorators for consistency with `test_db.py`, which correctly omits them.

### IN-07: `is_quarantined: False` is unconditionally hardcoded in both providers — prompt-injection quarantine must not be forgotten in Phase 4

**File:** `backend/app/providers/brave.py:124`, `backend/app/providers/mock.py:40,56`
**Issue:** SSOT G-6 / `AGENTS.md` Rule 9 require snippets matching high-risk injection phrases (`system prompt:`, `override verdict`, `ignore instructions`) to be flagged `is_quarantined = True` and excluded from the synthesis prompt. The design schedules this in Phase 4 (`sanitize_and_quarantine` in `services/verification.py`, SSOT line 687), so hardcoding false here is phase-conformant — but it leaves the injection defense unimplemented in this vertical slice while the provider boundary already manufactures the `SourceItem` dicts.
**Fix:** None required now. Add a tracking note (or TODO referencing SSOT line 687) at `brave.py:124` so the Phase 4 planner cannot miss it, and ensure `MockSearchProvider` grows a quarantined-snippet fixture in Phase 4 to exercise exclusion behavior.

---

_Reviewed: 2026-10-30T21:21:09Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_

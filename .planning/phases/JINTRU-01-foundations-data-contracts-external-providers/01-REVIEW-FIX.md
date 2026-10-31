---
phase: JINTRU-01-foundations-data-contracts-external-providers
fixed_at: 2026-10-31T04:01:00Z
review_path: .planning/phases/JINTRU-01-foundations-data-contracts-external-providers/01-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase JINTRU-01: Code Review Fix Report

**Fixed at:** 2026-10-31T04:01:00Z  
**Source review:** `.planning/phases/JINTRU-01-foundations-data-contracts-external-providers/01-REVIEW.md`  
**Iteration:** 1  

**Summary:**
- Findings in scope (Critical + Warning): 5
- Fixed: 5
- Skipped: 0
- Status: `all_fixed`
- Additional Info findings remediated: 7 (IN-01 through IN-07)

---

## Fixed Issues

### CR-01: Anomalous provider payloads escape as unhandled raw exceptions instead of structured error envelope
- **Files modified:** `backend/app/providers/brave.py`, `backend/app/providers/meta.py`, `backend/tests/unit/test_providers.py`
- **Commit:** `44593ed`
- **Applied fix:** 
  - Wrapped `response.json()` decode in `try...except ValueError` in both providers, mapping JSON decode errors to `ProviderUnavailableError`.
  - Added object type validation (`isinstance(data, dict)`), preventing raw `AttributeError` on malformed response shapes.
  - Implemented safe null navigation for `(data.get("grounding") or {}).get("generic")` and `(data.get("web") or {}).get("results")`.
  - Guarded Meta completion structure (`choices[0].message.content`), stripped markdown code fences, and mapped parse failures to `META_PARSE_ERROR`.
  - Added unit tests for malformed JSON, non-object bodies, null grounding/web structures, and fenced completion payloads.

### WR-01: `strict: true` structured-output schema non-conformance
- **Files modified:** `backend/app/providers/meta.py`, `backend/tests/unit/test_providers.py`
- **Commit:** `040b3cf`
- **Applied fix:**
  - Implemented `strict_json_schema()` hardening utility that recursively applies `additionalProperties: False` to all object nodes in root and `$defs` (`SourceEvaluationItem`, `ReasoningStatement`).
  - Ensured all property names are explicitly populated in `required` on every object node per OpenAI/Meta strict structured output specifications.
  - Added unit test `test_strict_json_schema()` asserting compliance offline.

### WR-02: Blanket `sqlite3.OperationalError` retry and lack of retry in delete/purge
- **Files modified:** `backend/app/db/database.py`, `backend/tests/unit/test_db.py`
- **Commit:** `0d6927d`
- **Applied fix:**
  - Implemented `Database._is_contention(exc)` checking for `"locked"` or `"busy"` in the exception message.
  - Extracted centralized `_with_write_retry()` helper with 3-attempt exponential backoff, failing fast on non-contention errors (e.g. `no such table`).
  - Applied `_with_write_retry()` uniformly across `save_verification`, `delete_verification`, and `purge_verifications`.
  - Remediated IN-02 (`PRAGMA journal_mode = WAL;` in `_connect()`), IN-03 (`db_path: str | None = None`), and IN-04 (removed dead pragma cursor).
  - Added unit test `test_non_contention_error_fails_fast()` asserting immediate failure on uninitialized database without sleeping.

### WR-03: Unknown Brave retrieval mode silently executes snippets branch
- **Files modified:** `backend/app/core/config.py`, `backend/app/providers/brave.py`, `backend/tests/unit/test_providers.py`
- **Commit:** `15cd2b9`
- **Applied fix:**
  - Narrowed `Settings.BRAVE_RETRIEVAL_MODE` from plain `str` to `Literal["snippets", "context"]`.
  - Replaced fallback `else` branch in `BraveSearchProvider.search()` with explicit `RequestConstraintError(code="BRAVE_BAD_MODE")`.
  - Added unit test `test_brave_search_invalid_mode()`.

### WR-04: Provider interface timeout defaults exceed SLA stage budgets
- **Files modified:** `backend/app/providers/base.py`, `backend/app/providers/mock.py`, `backend/app/providers/brave.py`, `backend/app/providers/meta.py`
- **Commit:** `d05e22b`
- **Applied fix:**
  - Lowered default search timeout from 3.0s to 2.0s (Stage-1 subordinate ceiling).
  - Lowered default model synthesis timeout from 4.0s to 3.0s (synthesis budget window).
  - Documented orchestrator obligation to pass `min(stage_budget, remaining_time)` to enforce the monotonic 8.0s ceiling.

---

## Remediated Info Findings
- **IN-01:** Stripped markdown code fences (````json ... ````) and narrowed completion unpacking exceptions.
- **IN-02:** Connection-scoped `PRAGMA journal_mode = WAL;` added to `Database._connect()`.
- **IN-03:** `Database.__init__` accepts `db_path: str | None = None` to avoid import-time settings binding.
- **IN-04:** Removed dead duplicate `PRAGMA synchronous;` query in `test_db.py`.
- **IN-05:** Persistence errors fail fast and retry only lock contention.
- **IN-06:** Removed redundant `@pytest.mark.asyncio` decorators across `test_providers.py`.
- **IN-07:** Added explicit Phase 4 prompt injection quarantine tracking comment in `brave.py`.

---

## Verification Summary
- **Test Suite:** 25/25 unit tests passing in 0.36s (`pytest backend/tests/unit/`).
- **Linter:** `ruff check backend/` clean with 0 errors.
- **Formatter:** `ruff format --check backend/` cleanly formatted.
- **Type Checker:** `pyright -p backend` clean with 0 errors, 0 warnings.

---
_Fixed: 2026-10-31T04:01:00Z_  
_Fixer: the agent (gsd-code-fixer protocol)_  
_Iteration: 1_

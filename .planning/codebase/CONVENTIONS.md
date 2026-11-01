---
last_mapped_commit: 77be68abbe401e7aa8296dc3cd0bfe40f4d2c320
last_mapped_at: 2026-11-02
---
# Coding Conventions

**Analysis Date:** 2026-11-02

## Naming Patterns

**Files:**
- Backend: Lowercase snake_case for all modules and test files (`verification.py`, `test_concurrency.py`, `schemas.py`)
- Frontend: Lowercase camelCase for utilities (`api.ts`, `utils.ts`), PascalCase or lowercase for components (`page.tsx`, `button.tsx`)
- Cross-platform root runners: Python executable entrypoints (`setup.py`, `run.py`) with thin POSIX shell wrappers (`setup.sh`, `start.sh`)

**Functions:**
- Backend: Lowercase snake_case (`classify_input`, `group_sources`, `normalize_excerpt`). Private helpers prefixed with single underscore (`_registrable_domain`, `_enforce_synthesis_guard`, `_with_write_retry`).
- Frontend: Lowercase camelCase (`createVerification`, `safeHref`, `normalizeVerification`, `toApiError`).

**Variables & Constants:**
- Local variables: Lowercase snake_case in Python (`remaining_time`, `source_map`); camelCase in TypeScript (`controller`, `timer`, `response`).
- Global Constants: UPPER_SNAKE_CASE in Python (`STAGE1_TIMEOUT_SECONDS = 2.0`, `SYNTHESIS_TIMEOUT_SECONDS = 3.0`, `MIN_SYNTHESIS_WINDOW_SECONDS = 2.5`); UPPER_SNAKE_CASE in TypeScript (`API_BASE`, `CLIENT_TIMEOUT_MS`).

**Types & Classes:**
- Backend: UpperCamelCase for Pydantic models, ABCs, and exception types (`VerificationRequest`, `SearchProvider`, `ProviderTimeoutError`, `VerificationResponse`). Type aliases use PascalCase or lowercase Literal unions (`PublicVerdict = Literal[...]`, `SourceStance = Literal[...]`).
- Frontend: UpperCamelCase for interfaces and type aliases (`PublicVerdict`, `SourceItem`, `VerificationResponse`, `ApiError`).

## Code Style

**Formatting:**
- Backend: Managed via Ruff (`ruff>=0.6.0`). Target Python 3.12 (`target-version = "py312"`), line length 100 characters (`line-length = 100` in `backend/pyproject.toml`). Enforced via `ruff format --check backend/`.
- Frontend: Prettier-compatible formatting with 2-space indentation, single quotes, no trailing semicolons.

**Linting:**
- Backend: Ruff (`ruff check backend/`) with zero warnings tolerated. Pyright strict static type checker (`pyright -p backend`) with zero type errors.
- Frontend: TypeScript strict mode (`"strict": true` in `frontend/tsconfig.json`), ESLint 9 Flat Config (`npm run lint` via `frontend/eslint.config.mjs`) with zero warnings/errors.

## Import Organization

**Order (Backend - PEP 8 / Ruff enforced):**
1. Standard library imports (`asyncio`, `hashlib`, `html`, `re`, `time`, `uuid`, `urllib.parse`)
2. Third-party library imports (`aiosqlite`, `fastapi`, `httpx`, `pydantic`, `pydantic_settings`)
3. Local application imports (`app.api.schemas`, `app.core.config`, `app.core.errors`, `app.db.database`)

**Path Aliases:**
- Backend: Absolute package imports from root package (`from app.api.schemas import ...`). Tests set `pythonpath = ["."]`.
- Frontend: `@/*` alias mapped to `./*` (`@/lib/api`, `@/components/ui/button` via `tsconfig.json`).

## Error Handling

**Patterns:**
- Typed domain exceptions defined in `backend/app/core/errors.py` inheriting from `DomainError`:
  - `ProviderTimeoutError(message, code, detail)`
  - `ProviderUnavailableError(message, code, detail)`
  - `ClientDisconnectedError(message, code, detail)`
  - `RequestConstraintError(message, code, detail)`
- Centralized exception handlers registered in `backend/app/main.py` translating domain exceptions into standardized `ErrorEnvelope` JSON payloads.
- Asynchronous database write operations wrapped with `_with_write_retry` to handle transient `sqlite3.OperationalError: database is locked` contention with exponential backoff (`backend/app/db/database.py`).
- Client-side error handling: `ApiError` class in `frontend/lib/api.ts` parses `code`, `status`, `message`, and `detail` consistently.

## Logging

**Framework:** Python standard library `logging` (`logger = logging.getLogger(__name__)`).

**Patterns:**
- Log state transitions, provider fallback events, and latency breakdowns.
- Never log raw API tokens, authorization headers, or sensitive user inputs.
- Log timeouts and degradation triggers with explicit timing details (`logger.warning("Synthesis window exceeded: %.2fs remaining", remaining)`).

## Comments

**When to Comment:**
- Explain architectural constraints, budget limits, or normative standards (e.g. references to ADRs or system invariants like `# Authoritative 8.0s budget stage allocations`).
- Document complex regular expressions and wire service attribution patterns.
- Avoid obvious comments that simply restate function or variable names.

**JSDoc/TSDoc & Python Docstrings:**
- Python: Module-level and class-level docstrings describing purpose and ADR compliance.
- TypeScript: TSDoc comments for public exported client functions (`createVerification`, `safeHref`).

## Function Design

**Size:** Focused, single-responsibility functions. Complex algorithms (like `apply_verdict_policy` or `group_sources`) are decomposed into testable sub-functions.

**Parameters:** Use keyword arguments and explicit type annotations for all parameters. Avoid mutable default arguments.

**Return Values:** Explicitly type-annotated return signatures. Async functions return `Awaitable` coroutines.

## Module Design

**Exports:**
- Explicit exports defined in `__all__` or cleanly re-exported in package `__init__.py` files (e.g. `backend/app/providers/__init__.py`).
- Avoid wild card (`from module import *`) imports.

**Barrel Files:**
- Avoid barrel files that cause circular dependencies. Explicit module import paths preferred.

---

*Convention analysis: 2026-11-02*

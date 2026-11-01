---
phase: JINTRU-02-verification-engine-citation-validation-api-gateway
fixed: 4
skipped: 0
findings_in_scope: 4
status: all_fixed
iteration: 1
---

# Phase JINTRU-02: Code Review Fix Report

**Source review:** `02-REVIEW.md` (status: issues_found — 1 critical, 3 warnings, 6 info)
**Fix scope:** critical_warning (default; Info findings intentionally out of scope)
**Fixed:** 4 / 4 in scope
**Verification:** `pytest backend/tests/ -q` → 84 passed · `ruff check backend/` → clean · `pyright -p backend` → 0 errors

## Disposition

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| CR-01 | critical | Source-family clustering used the raw hostname, so one publisher's subdomains satisfied the two-domain guardrail | fixed |
| WR-01 | warning | `content_hash` identified raw provider text instead of the stored snippet | fixed |
| WR-02 | warning | `mixed` validation was asymmetric (support relevance-filtered, refutations not) | fixed |
| WR-03 | warning | No client-disconnect check between pipeline stages | fixed |
| IN-01 | info | URL-less sources collapse into a shared `"unknown"` family | open (out of scope) |
| IN-02 | info | Future-year detection capped at 2099 / needs a preposition | open (out of scope) |
| IN-03 | info | `extraction_status` and `published_at` never populated | open (out of scope) |
| IN-04 | info | Three-token injection denylist is paraphrased around | open (accepted limitation) |
| IN-05 | info | `app.state` accessed untyped | open (out of scope) |
| IN-06 | info | `limit` capped with 422 instead of clamping | open (out of scope) |

## Fixes Applied

### CR-01 — Registered-domain source-family clustering
**Files:** `backend/app/services/verification.py`

Added `_MULTI_PART_SUFFIXES` (co.uk, org.uk, ac.uk, gov.uk, com.au, net.au, co.nz, co.jp, com.br, co.in, co.za) and `_registrable_domain(host)`, which reduces a hostname to its registrable domain, returns short (≤2 label) hosts and IP literals unchanged, and `_resolve_family_id` now clusters on that value. `SourceItem.domain` keeps the full canonical hostname (display/provenance unchanged); only `source_family_id` collapses. News/sports subdomains of one publisher now share a family and can no longer corroborate each other.

**Tests added:** `test_group_sources_collapses_publisher_subdomains_into_one_family` (unit), `test_publisher_subdomains_cannot_award_supported` (pipeline end-to-end: `supported` → `insufficient_evidence` with the single-family limitation).

### WR-01 — Hash the stored snippet, not the raw payload
**Files:** `backend/app/services/verification.py` (`group_sources`)

`content_hash` is now always `sha256` of the sanitized snippet that is actually persisted and cited; the provider-supplied hash is no longer trusted for the stored field, and de-duplication therefore compares sanitization-normalized text.

**Tests added:** `test_group_sources_hashes_the_stored_snippet` (zero-width character case: hash matches stored text, not the provider hash), `test_group_sources_deduplicates_after_sanitization` (zero-width variants collapse to one source).

### WR-02 — Symmetric `mixed` validation
**Files:** `backend/app/services/verification.py` (`apply_verdict_policy`)

The conflict check now compares stance presence on both sides (`any_supports and any_refutation`) instead of the relevance-filtered `support` list against unfiltered refutations. A claim rated `indirect` on both sides keeps its `mixed` verdict instead of aborting to `insufficient_evidence`.

**Tests added:** `test_mixed_with_indirect_stances_is_preserved` (previously would have downgraded).

### WR-03 — Client-disconnect polling between stages
**Files:** `backend/app/services/verification.py`, `backend/app/api/routes.py`, `backend/app/core/errors.py`, `backend/app/main.py`

`VerificationPipeline.verify()` accepts an optional `is_disconnected: Callable[[], Awaitable[bool]]` and polls it at two boundaries — before Stage 2 dispatch and before synthesis dispatch — raising the new `ClientDisconnectedError` (code `CLIENT_DISCONNECTED`) rather than spending another paid call. `POST /api/v1/verifications` passes `request.is_disconnected`; `main.py` maps the error to HTTP 499 with an `ErrorEnvelope`. Abandoned requests now stop after at most the Stage-1 query.

**Tests added:** `test_client_disconnect_aborts_before_synthesis` (one search call, zero synthesis calls, nothing persisted), plus the 499/`CLIENT_DISCONNECTED` case in the API domain-error matrix.

## Notes

- All four fixes landed in a single source commit because they overlap in `services/verification.py`; per-finding commits would have required staging partial file state that no longer exists after the edits.
- The `code_review_disposition` ledger step was not run (no per-finding ledger exists for Phase 2 yet); this table is the disposition record.
- No Info finding was modified, so `02-REVIEW.md` remains the authoritative review record for those six.

---
phase: JINTRU-03-frontend-wiring-full-stack-integration
fixed_at: 2026-11-01T22:27:00Z
review_path: .planning/phases/JINTRU-03-frontend-wiring-full-stack-integration/03-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase JINTRU-03: Code Review Fix Report

**Fixed at:** 2026-11-01T22:27:00Z  
**Source review:** `.planning/phases/JINTRU-03-frontend-wiring-full-stack-integration/03-REVIEW.md`  
**Iteration:** 1  

**Summary:**
- Findings in scope (Critical + Warning): 5
- Fixed: 5
- Skipped: 0
- Status: `all_fixed`
- Additional Info findings remediated: 6 (IN-01 through IN-06)

---

## Fixed Issues

### CR-01: Evidence links render an unvalidated provider URL into `href` — script execution sink
- **Files modified:** `backend/app/services/verification.py`, `backend/tests/unit/test_citations.py`, `frontend/lib/api.ts`, `frontend/app/page.tsx`
- **Applied fix:**
  - Implemented `_is_safe_http_url()` in `backend/app/services/verification.py` verifying that parsed URLs only use `http` or `https` schemes with non-empty netloc; unsafe URLs (such as `javascript:` or `data:`) are replaced with empty string `""`.
  - Added unit test `test_group_sources_sanitizes_unsafe_urls` in `backend/tests/unit/test_citations.py`.
  - Implemented `safeHref()` and `normalizeSource()` in `frontend/lib/api.ts` enforcing protocol validation at the API boundary on all responses.
  - Updated `SourceCard` in `frontend/app/page.tsx` to inspect `safeHref(source.url)` and render the anchor only when non-null and not quarantined.

### WR-01: Opening a history record overwrites whatever the user is currently drafting
- **File modified:** `frontend/app/page.tsx`
- **Applied fix:**
  - Removed `setClaim(record.claim)` from `openHistoryItem`. Opening past records preserves any in-progress draft text in the composer.

### WR-02: History rows nest a native `<button>` inside a `role="button"` container
- **Files modified:** `frontend/app/page.tsx`, `frontend/app/globals.css`
- **Applied fix:**
  - Converted `.history-item` container from a pseudo-button with `role="button"` and `tabIndex={0}` to a clean semantic container.
  - Replaced inner claim text with an explicit native `<button type="button" className="history-select-btn">` alongside the adjacent delete `<button>`.
  - Styled `.history-select-btn` and `.history-claim-text` in `globals.css` for robust focus rings and alignment.

### WR-03: The settings panel claims `aria-modal` but cannot be dismissed or navigated as a modal
- **File modified:** `frontend/app/page.tsx`
- **Applied fix:**
  - Added `Escape` key event listener closing the panel.
  - Added Tab and Shift+Tab focus trap keeping keyboard focus cycled within `section.settings-panel`.
  - Moved focus to the close button on modal open and restored focus to the settings trigger button on close.

### WR-04: Copy actions report success without checking that anything was copied
- **File modified:** `frontend/app/page.tsx`
- **Applied fix:**
  - Made `copyReport` async, awaiting `navigator.clipboard?.writeText(report)` in `try...catch` and setting `copied = true` only upon promise resolution.
  - Added per-source `copiedQuote` state and `handleCopyQuote()` in `SourceCard` with promise verification and visual feedback (`Copied` vs `Copy quote`).

---

## Remediated Info Findings
- **IN-01:** Updated history section eyebrow to show `HISTORY (SHOWING {history.length} OF {historyTotal})` when results are truncated.
- **IN-02:** Removed unreferenced scaffold placeholder files from `frontend/public/` (`placeholder.jpg`, `placeholder-logo.png`, `placeholder-logo.svg`, `placeholder.svg`, `placeholder-user.jpg`).
- **IN-03:** Updated `frontend/package.json` project name to `"jintru-frontend"` and added `"lint": "eslint ."`.
- **IN-04:** Aliased legacy color tokens `--green` and `--red` to `--emerald` and `--rose` across light and dark modes in `frontend/app/globals.css`.
- **IN-05:** Added CSS styling for `.unknown-body ul` and `.unknown-body li` (clean vertical flex list with proper indentation and line-height).
- **IN-06:** Updated `exportJson` in `frontend/app/page.tsx` to append the download anchor to `document.body` prior to `.click()` and remove it afterwards, ensuring compatibility with Safari.

---

## Verification Summary
- **Backend Tests:** 85/85 unit and integration tests passing in 0.95s (`pytest backend/tests/ -v`).
- **Python Linter:** `ruff check backend/` clean with 0 errors.
- **Python Type Checker:** `pyright -p backend` clean with 0 errors, 0 warnings.
- **Frontend Type Checker:** `cd frontend && npx tsc --noEmit` clean with 0 errors.

---
_Fixed: 2026-11-01T22:27:00Z_  
_Fixer: the agent (gsd-code-fixer protocol)_  
_Iteration: 1_

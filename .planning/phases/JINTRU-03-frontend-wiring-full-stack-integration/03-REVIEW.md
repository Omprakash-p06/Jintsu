---
phase: JINTRU-03-frontend-wiring-full-stack-integration
reviewed: 2026-11-01T18:55:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - .gitignore
  - frontend/.env.example
  - frontend/.gitignore
  - frontend/app/globals.css
  - frontend/app/layout.tsx
  - frontend/app/page.tsx
  - frontend/lib/api.ts
  - frontend/lib/utils.ts
  - frontend/next.config.mjs
  - frontend/package.json
findings:
  critical: 1
  warning: 4
  info: 6
  total: 11
status: issues_found
---

# Phase JINTRU-03: Code Review Report

**Reviewed:** 2026-11-01T18:55:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 3 replaces the prototype's fixtures with the live verification API: a typed client (`frontend/lib/api.ts`), a server-side `/api/v1` rewrite, telemetry removal, and a fully wired `app/page.tsx` plus the token and accessibility additions in `globals.css`.

The typed boundary holds up. Every call goes through one `request<T>()` helper; non-2xx bodies are parsed into `ApiError` from the backend `ErrorEnvelope`; the 12s abort backstop sits above the 8.0s server SLA so it cannot mask a legitimate 504; `verify()` refuses to start below 5 characters, above 500, or while a verification is in flight; the elapsed timer is created and cleared on the same paths, including unmount; all five verdicts and three stances carry icon + label + token; no fixture survives; nothing uses `dangerouslySetInnerHTML`; quarantined sources suppress their outbound link. `npx tsc --noEmit` passes.

One Critical issue remains: the evidence card renders a provider-supplied `url` straight into `href` without validating its scheme, giving a `javascript:` value a script-execution sink in the application origin — on a data source the backend already treats as adversarial. Four warnings cover draft-claim loss when opening history, nested interactive elements in the history list, a dialog that claims modality without enforcing it, and a copy action that reports success unconditionally.

**Build/runtime caveat:** this phase could not be exercised in a browser. `next@16.4.3` declares `engines.node >= 20.9.0` and the host runs v18.19.1, so both `next build` and `next dev` fail on an engine check. Every finding below was established by reading the source with the TypeScript analysis in hand — none was observed at runtime.

## Critical Issues

### CR-01: Evidence links render an unvalidated provider URL into `href` — a `javascript:` URL becomes script execution in the app origin

**File:** `frontend/app/page.tsx:180` (the `SourceCard` anchor), fed by `frontend/lib/api.ts:11` (`SourceItem.url`)

**Issue:** The card renders

```tsx
<a className="text-btn" href={source.url} target="_blank" rel="noopener noreferrer">
```

`source.url` travels unmodified from the search provider (`backend/app/providers/brave.py` copies the provider's `url` field) through `group_sources`, which never inspects the scheme, into SQLite, and back out through `GET /api/v1/verifications`. React escapes text but does **not** sanitise `href`, so a value such as `javascript:fetch('/api/v1/verifications',{method:'DELETE'})` runs in the workbench's own origin when a user clicks "View evidence". `target`/`rel` do not help: a `javascript:` URL executes in the current document before any navigation is considered.

This is not speculative hardening for a threat model the system otherwise ignores. The backend's entire injection posture assumes retrieved web content is adversarial — `sanitize_and_quarantine`, snippet quarantine, and threat IDs T-02-01/T-03-06 exist for exactly that reason — yet the one field that reaches a script sink is the one field no layer validates. A compromised search edge, a provider change, or any record written to the shared SQLite file is sufficient input. The payload would then run with the workbench's own origin privileges, where the API is unauthenticated by design (NG-9: single-user local mode) and exposes the purge endpoint.

**Fix:** Accept only `http:`/`https:` and drop the link otherwise:

```tsx
function safeHref(url: string): string | null {
  if (!url) return null
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? parsed.toString() : null
  } catch {
    return null
  }
}
```

Then use `const href = safeHref(source.url)` and render the anchor only when `href` is non-null. Prefer normalising once at the `lib/api.ts` boundary (a `normalizeSource()` mapper) so no future component can reintroduce the sink, and add a matching backend guard in `group_sources`, since the API is callable by anything on the machine.

## Warnings

### WR-01: Opening a history record overwrites whatever the user is currently drafting

**File:** `frontend/app/page.tsx:380-387` (`openHistoryItem`, overwrite at `:386`)

**Issue:** `openHistoryItem` restores a stored verification and ends with `setClaim(record.claim)`. A user who has typed a new claim, then opens the history drawer to inspect an earlier verification, silently loses that draft — no confirmation, no undo, and focus stays in the textarea so the replacement is easy to miss. The result panel already renders `result.claim`, so the composer write is not required to display the record.

**Fix:** Do not mutate the composer when opening a stored record. If pre-filling is wanted, expose it as an explicit action inside the opened record ("Load into composer"), which is reversible in the sense that the user chose it.

### WR-02: History rows nest a native `<button>` inside a `role="button"` container

**File:** `frontend/app/page.tsx:822-845` (row `role="button"` at `:823`, delete button at `:838-844`)

**Issue:** Each row is a `div[role="button"][tabIndex=0]` with an `onClick` and a synthetic Enter/Space handler, and it contains a real `<button>` for delete. Interactive content inside an interactive container is invalid markup and ambiguous to assistive tech: the row advertises itself as a button while containing a second button, so a screen reader may announce one control and swallow the other's name, and keyboard users tab into the row and then into the delete button with no announced grouping.

**Fix:** Make the row a plain container with two explicit controls — a select button spanning the claim text plus the delete icon button — or keep the row a button and move delete outside it (adjacent column or context menu). The first is the smaller change and keeps the current focus order.

### WR-03: The settings panel claims `aria-modal` but cannot be dismissed or navigated as a modal

**File:** `frontend/app/page.tsx:865-880` (`role="dialog"`, `aria-modal="true"`, overlay click-to-close)

**Issue:** The panel declares `role="dialog" aria-modal="true"` but has no Escape handler, moves no initial focus, does not trap Tab inside itself, and does not restore focus to the trigger on close; the only dismissal is the overlay click or the close button, neither of which a keyboard-only user reaches if focus is behind the overlay. `aria-modal="true"` therefore asserts a modality the implementation does not enforce — worse for a screen reader than not claiming it, in a phase explicitly targeting WCAG 2.2 AA (AGENTS.md rule 11). The click-outside `div` also has no keyboard equivalent.

**Fix:** Add an effect that focuses the panel on open, closes on `Escape`, restores focus to the trigger on close, and cycles Tab within the panel; keep the overlay click as a convenience.

### WR-04: Copy actions report success without checking that anything was copied

**File:** `frontend/app/page.tsx:455-457` (`copyReport`), `frontend/app/page.tsx:192-197` (per-source "Copy quote")

**Issue:** `copyReport` calls `navigator.clipboard?.writeText(report)` and then unconditionally `setCopied(true)` followed by a 1600 ms reset. Two problems follow from that: `navigator.clipboard` is `undefined` outside a secure context (plain `http://` on a LAN address, which is how this may be served past localhost), and the promise can reject on denied permission — in both cases nothing is copied while the button confirms it was. The per-source copy button has the same silent-failure path with no feedback at all. A copied "verification report" that was never copied is a reporting-integrity problem, not just polish, since the report is the artifact a user pastes into their own notes.

**Fix:** Await the promise and only flip the flag on success:

```tsx
const ok = await navigator.clipboard?.writeText(report).then(() => true).catch(() => false)
setCopied(ok === true)
```

and surface a distinct "Could not copy" state rather than silently doing nothing.

## Info

### IN-01: History shows the first 20 records with no "showing x of y" cue
**File:** `frontend/app/page.tsx:301-310` (`loadHistory`, `limit: 20` at `:304`)
**Issue:** The drawer fetches 20 records and stores the server's `total` separately; that total drives only the sidebar count and the purge prompt. With more than 20 records the list silently truncates — the count says 137 while the drawer shows 20 — and there is no paging control.
**Fix:** Render "Showing 20 of N" (or a `Load more` that advances `offset`) and keep the purge label keyed to the true total.

### IN-02: Scaffold placeholder artwork ships in `frontend/public/`
**File:** `frontend/public/placeholder.jpg`, `placeholder-logo.png`, `placeholder-logo.svg`, `placeholder.svg`, `placeholder-user.jpg`
**Issue:** Nine assets sit in the public directory; the five `placeholder-*` files are unreferenced by `app/` (the layout's metadata points only at `icon.svg`, `icon-light-32x32.png`, `icon-dark-32x32.png`, `apple-icon.png`). Unreferenced public assets are copied into every deployment.
**Fix:** Delete the `placeholder-*` files; keep the icon assets the metadata declares.

### IN-03: Package identity is still the scaffold default and no lint script exists
**File:** `frontend/package.json:2`
**Issue:** `"name": "my-project"` remains after the app became the jintru workbench, and there is no `lint` script, so Phase 4's SEC-01 audit lane has no frontend lint target to hook into.
**Fix:** Rename to `jintru-frontend` and add `"lint": "eslint ."` with a flat config when Phase 4 wires the audit tooling.

### IN-04: Two colour palettes now coexist
**File:** `frontend/app/globals.css:5-6`
**Issue:** `--emerald/--rose/--slate` were added for the verdict surface while the prototype's `--green/--red` remain in use by `.source-card`, `.stance-label`, `.graph-branch`, `.validated`, `.connected`, and chart accents. The pairs are visually close but independently defined per theme, so a palette change must be applied twice and can drift.
**Fix:** Alias the legacy names onto the new tokens (`--green: var(--emerald)`) or migrate the remaining consumers once a visual pass can confirm no regression.

### IN-05: New `<ul>` content is unstyled inside `.unknown-body`
**File:** `frontend/app/globals.css:21` (`.unknown-body`), `frontend/app/page.tsx:686-714` (reasoning/limitation lists)
**Issue:** `.unknown-body` styles only `p` and `svg`; the limitations and reasoning lists render as browser-default bullets with default indentation inside a flex row, which reads inconsistently with the paragraph it replaced and inherits the container's muted colour for markers.
**Fix:** Add `.unknown-body ul { margin:0; padding-left:18px; display:flex; flex-direction:column; gap:6px; }` plus a matching `li` line-height.

### IN-06: JSON export clicks an anchor that was never attached to the document
**File:** `frontend/app/page.tsx:460-469`
**Issue:** `anchor.click()` fires on a detached element. This works in Chromium and Firefox but is unreliable in Safari, where a detached anchor's download can be ignored — the export silently does nothing.
**Fix:** `document.body.appendChild(anchor)`, click, then `anchor.remove()` alongside the existing `URL.revokeObjectURL(url)`.

---

## Checked and cleared

- **Hydration:** `formatWhen` (`:98-103`) uses `toLocaleString()`, but it never runs during server rendering — history and results are both client-loaded, so the initial HTML is static. No mismatch.
- **Double submission:** `verify()` (`:350-352`) returns early when `loading` is true, and the shortcuts route through it, so the timeline cannot start twice or orphan a timer.
- **Telemetry / injection:** zero `@vercel/analytics`, zero `dangerouslySetInnerHTML`, all snippet text interpolated as React children.
- **Timer lifetime:** the interval is cleared in `finally` and in the `useEffect` cleanup (`:328-331`) that returns `stopTimer`.

_Reviewed: 2026-11-01T18:55:00Z_
_Reviewer: gsd-code-reviewer role (executed inline — no subagent runtime available)_
_Depth: standard_
_Note: runtime behaviour unverified — `next dev`/`next build` are blocked by the Node ≥ 20.9.0 engine floor on this host_

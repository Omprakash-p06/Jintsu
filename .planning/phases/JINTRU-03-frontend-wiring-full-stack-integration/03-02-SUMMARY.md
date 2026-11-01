# Phase 3 Plan 2: Workbench Component Wiring Summary

**Execution Status:** Completed (type-level verification only — see §4)
**Phase:** 3 - Frontend Wiring & Full-Stack Integration
**Plan:** `03-02-PLAN.md`

## 1. Executive Summary
Replaced every fixture in the prototype with live backend data. `frontend/app/page.tsx` now submits real claims, renders the backend verdict, derives the evidence map and cards from actual `SourceItem`s, and drives the history drawer and provider status from the API. `frontend/app/globals.css` gained the five explicit verdict tokens, a global focus ring, and the small set of new classes the wiring needs.

## 2. Key Accomplishments
- **Tokens & accessibility (`globals.css`, in place — no class or layout rule renamed):** `--emerald`, `--rose`, `--slate`, `--indigo-bg` (plus light/dark `-bg` companions) added; `.verdict-badge` and `.verdict-card` tones repointed at them while keeping existing class names; global `:where(a,button,textarea,[tabindex]):focus-visible { outline:2px solid #7c3aed }` so the prototype's raw `<button>`s get a visible ring; new `.sr-only`, `.alert`, `.quarantine-flag`, `.stance-badge`, `.history-*`, `.provider-status` rules. Both `@media` blocks preserved untouched.
- **Claim submission (`page.tsx`):** real `createVerification()` call replacing the `setTimeout` fake; 5–500 guard mirrored from the API contract; live `mm:ss`-style elapsed timer driven by a 100ms interval with cleanup on unmount; six stages advanced from elapsed thresholds aligned to the real budget (0.2s / 2.3s / 2.0s / 3.0s / validate / persist) and **explicitly labelled as estimated**, because the endpoint is synchronous and streams nothing.
- **Error handling:** `ApiError` codes mapped to human copy (`PROVIDER_TIMEOUT`, `SYNTHESIS_WINDOW_EXCEEDED`, `PROVIDER_UNAVAILABLE`, `VALIDATION_ERROR`, `CLIENT_DISCONNECTED`, `CLIENT_TIMEOUT`, `NETWORK_ERROR`) and rendered in a dismissible `role="alert"` panel with the raw code shown for support.
- **Verdict presentation:** all five verdicts map to icon + text label + distinct tone (supported/emerald `CheckCircle2`, contradicted/rose `XCircle`, mixed/amber `AlertCircle`, insufficient_evidence/slate `Info`, not_verifiable/indigo `ShieldCheck`); summary, timestamp and distinct-family count come from the response.
- **Evidence cards:** stance badge (icon + label), canonical domain, wire attribution humanised from `source_family_id` (`associated_press` → "Associated Press wire", etc.), `exact_quote ?? snippet`, relevance, provenance line (family/type/hash prefix), quarantine flag that suppresses the outbound link, and `rel="noopener noreferrer"` on external anchors. Filter pills compute their counts from real stances.
- **Relationship graph:** claim node from the record, up to three distinct supporting families and up to three challenging families (or an explicit "NO COUNTEREVIDENCE FOUND" label), final node bound to the verdict and its tone.
- **History drawer:** `listVerifications({limit:20})` on mount, `getVerification(id)` to restore a record, `deleteVerification(id)` per item, `purgeVerifications()` behind an explicit confirmation, plus refresh; failures surface inline without crashing the page.
- **Health panel:** `getHealth()` drives the sidebar footer and settings dialog; `configured` maps to an emerald dot, `missing` to amber, and a failed call renders "Backend unreachable" instead of a false green dot.

## 3. Verification & Quality Gates
- `cd frontend && npx tsc --noEmit` → **exit 0**.
- Fixture/prohibition greps: `sampleSources|historySeed|dangerouslySetInnerHTML` → **0 matches**; `rel="noopener noreferrer"` → present.
- Design-token greps: `--emerald`, `--rose`, `--slate`, `--indigo-bg`, `#7c3aed` present; `@media` count unchanged at 2.
- `npm run build` → **BLOCKED**: `You are using Node.js 18.19.1. For Next.js, Node.js version ">=20.9.0" is required.`

## 4. Known Blockers
- **No runtime verification was possible.** `next dev` shares the Node ≥ 20.9.0 floor, so the app was never rendered in a browser in this session: the wiring is verified at the type level and by source inspection only. Submitting a claim, restoring history, deleting, purging, and reading the health panel against a live backend are **unverified** and become Phase 4 Playwright work (TEST-02).
- No screenshot or visual review was performed, per the task's scope.

## 5. Deviations from Plan
1. **`not_verifiable` uses `ShieldCheck` rather than `ShieldHelp`.** `lucide-react` was not inspectable offline at authoring time, so an icon already imported by the prototype was used instead of risking a missing export. The invariant (icon + label + token, never colour alone) holds.
2. **History rows are `div[role="button"]` with a real delete `<button>` inside**, not nested `<button>` elements — the plan's markup sketch would have produced invalid nested interactive content.
3. **The full snippet and provenance details are additional `.source-note` blocks**, reusing the prototype's existing "Jintru interpretation" visual rather than introducing a new panel style.
4. A "GROUNDED REASONING" panel renders `result.reasoning` when the backend supplies validated statements; the plan did not require it, but the data was already in the response and the SSOT positions cited reasoning as part of the result surface.

## 6. Requirements Satisfied
- `UI-02`: claim textarea with 500-character counter, submit action, live elapsed timer and stage display.
- `UI-03`: accessible 5-way verdict badge with explicit colour tokens, summary narrative, and "What remains unknown" limitations section.
- `UI-04`: evidence cards with stance badges, canonical domains, wire attribution, quoted snippets and safe external links.
- `UI-05`: history drawer with listing, restore, individual deletion and full purge.

All four are satisfied at the source/type level; end-to-end browser behaviour awaits the Node upgrade and Phase 4 E2E coverage.

## 7. Artifacts
- `frontend/app/page.tsx`, `frontend/app/globals.css`

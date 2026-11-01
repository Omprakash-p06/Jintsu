# Phase 3 Plan 1: Typed API Boundary & Toolchain Summary

**Execution Status:** Completed (build gate blocked by Node runtime — see §4)
**Phase:** 3 - Frontend Wiring & Full-Stack Integration
**Plan:** `03-01-PLAN.md`

## 1. Executive Summary
Repaired the imported prototype's toolchain, removed telemetry, and established a single typed boundary between the Next.js workbench and the Phase 2 gateway. `frontend/lib/api.ts` mirrors `backend/app/api/schemas.py` field-for-field and is now the only place the UI talks to `/api/v1`; requests go same-origin through a Next.js rewrite to the backend origin.

## 2. Key Accomplishments
- **Toolchain repair:**
  - Created `frontend/lib/utils.ts` exporting `cn()` (clsx + tailwind-merge) — `components/ui/button.tsx` already imported `@/lib/utils`, so the prototype could not typecheck before this.
  - Added `"typecheck": "tsc --noEmit"` to `package.json` scripts.
  - Corrected `"packageManager": "pnpm@12.3.4"` (a version that does not exist) to `pnpm@9.15.0`.
  - Installed 273 packages; only `EBADENGINE` warnings were emitted (Node 18 vs. dependencies requiring 20+).
- **Telemetry removed:** deleted the `@vercel/analytics` dependency and its `<Analytics />` mount in `app/layout.tsx`, per SSOT non-functional requirement 4 (zero telemetry). Also dropped the leftover `generator: 'v0.app'` metadata.
- **Typed client (`frontend/lib/api.ts`):**
  - Types: `PublicVerdict`, `SourceStance`, `Relevance`, `SourceItem`, `ReasoningStatement`, `VerificationResponse`, `VerificationListItem`, `PaginatedVerificationResponse`, `HealthResponse`, `ErrorEnvelope`.
  - `ApiError` (status, code, message, detail) plus `isApiError` for the UI's error branch.
  - One private `request<T>()` helper: 12s `AbortController` backstop (above the backend's 8.0s SLA so it never masks a 504), 204 → `undefined`, non-2xx parsed into `ApiError` from the `ErrorEnvelope`, network/abort failures mapped to `NETWORK_ERROR` / `CLIENT_TIMEOUT`.
  - Endpoints: `createVerification`, `listVerifications`, `getVerification`, `deleteVerification`, `purgeVerifications`, `getHealth`; `toQuery` omits undefined values and encodes both key and value.
- **Proxy (`frontend/next.config.mjs`):** removed `typescript: { ignoreBuildErrors: true }`, added `rewrites()` mapping `/api/v1/:path*` → `${JINTRU_API_URL ?? 'http://127.0.0.1:8000'}/api/v1/:path*` (server-side only). Added `frontend/.env.example` documenting `JINTRU_API_URL` and `NEXT_PUBLIC_API_BASE_URL`.

## 3. Verification & Quality Gates
- `npx tsc --noEmit` → **exit 0** (with the wired `page.tsx` from 03-02 also present).
- Rewrite check: `node --input-type=module -e "import('./next.config.mjs')..."` → `rewrite ok: http://127.0.0.1:8000/api/v1/:path*`.
- `grep ignoreBuildErrors next.config.mjs` → 0 matches; `grep -r @vercel/analytics app/ package.json` → 0 matches.

## 4. Known Blockers
- **`next build` / `next dev` cannot run in this workspace.** `next@16.4.3` requires Node `>=20.9.0`; the host runs `v18.19.1`. The build was attempted and failed with: *"You are using Node.js 18.19.1. For Next.js, Node.js version \">=20.9.0\" is required."* Roadmap success criterion 1 (clean `npm run build`) therefore remains **unmet**, not failed — it needs a Node upgrade, which is a host-level action outside this repository.

## 5. Deviations from Plan
1. **Installed with `npm install --no-package-lock` instead of `npx pnpm@9 install`.** pnpm 9 refuses this repo's `pnpm-workspace.yaml` (`ERROR packages field missing or empty`), and there is no `pnpm` binary on PATH. `--no-package-lock` avoids creating a competing `package-lock.json` alongside the committed `pnpm-lock.yaml`, so the lockfile contract is unchanged.
2. **The build gate is reported as blocked, not passed**, exactly as the plan required. No attempt was made to work around the engine floor.

## 6. Requirements Satisfied
- `UI-01`: Next.js 16 + React 19 + Tailwind v4 integration with a typed API client at `frontend/lib/api.ts` and a `/api/v1` proxy. Runtime invocation of the client is unverified until the Node floor is met (Phase 4 Playwright covers it).

## 7. Artifacts
- `frontend/lib/api.ts`, `frontend/lib/utils.ts`, `frontend/next.config.mjs`, `frontend/.env.example`, `frontend/package.json`, `frontend/app/layout.tsx`

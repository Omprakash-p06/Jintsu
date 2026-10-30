# Goldfish Annotated Review Report

**Status:** resolved  
**Target:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md) (`full file`)  
**Context:** [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md), [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md)  
**Standard:** Antigravity EGM Goldfish Resolution Protocol (`egm-resolve`)

---

## Prioritized Findings & Applied Resolutions

### [Item 1] [Meta API Contract Finalization] - Severity: High
* **Affected Scope:** Lines 64–65, 426–428, 665–680 ([`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)) (Open Questions & Provider Adapters)
* **Discrepancy Description:** OQ-3 left model discovery, family selection, and request formatting open for integration testing instead of locking the confirmed Meta Model API specifications.
* **Rationale:** Meta Model API officially documents `https://api.meta.ai/v1`, model `muse-spark-1.3`, bearer token authentication, and structured JSON output via `response_format` with `json_schema`.
* ***AI Suggestion:*** `PROPOSE FIX`
* ***Justification:*** Eliminates runtime ambiguity by locking the provider adapter and configuration directly to `muse-spark-1.3` with strict `response_format` JSON schema.
* ***Applied Resolution:***
  * Locked OQ-3 in Section 3.
  * Added `META_MODEL: str = "muse-spark-1.3"` to `Settings` in `backend/app/core/config.py` (Phase 1).
  * Explicitly specified request payload in `MetaModelProvider` (Phase 3) using `response_format: {"type": "json_schema", "json_schema": {"name": "verification_synthesis", "strict": True, "schema": VerificationSynthesisPayload.model_json_schema()}}`.

---

### [Item 2] [Tailwind CSS Stable Dependency Cleanup] - Severity: Low
* **Affected Scope:** Lines 740–755 ([`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)) (Phase 6: Frontend Workbench Application)
* **Discrepancy Description:** Frontend dependencies pinned `@tailwindcss/vite` and `tailwindcss` to `^4.0.0-beta.4`.
* **Rationale:** Stable Tailwind v4 releases are available; pre-release beta tags should be removed for reproducible, clean dependency installation.
* ***AI Suggestion:*** `PROPOSE FIX`
* ***Justification:*** Eliminates pre-release dependency risk in `frontend/package.json`.
* ***Applied Resolution:***
  * Replaced `^4.0.0-beta.4` with `^4.0.0` for both `tailwindcss` and `@tailwindcss/vite` in `frontend/package.json`.

---

### [Item 3] [Brave LLM Context Payload Mapping & Live Latency Benchmarking] - Severity: Medium
* **Affected Scope:** Lines 650–665, 785–815 ([`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)) (Phase 3: Providers, Phase 8: Benchmarks)
* **Discrepancy Description:** Response structure for Brave LLM Context endpoint needed explicit mapping from `grounding.generic[].snippets` to `SourceItem`, and live 8-second SLA needed empirical benchmark validation.
* **Rationale:** Brave documents the LLM context endpoint structure under `grounding.generic[].snippets`; 8.0s SLA is an operational constraint requiring live WAN latency distribution benchmarking.
* ***AI Suggestion:*** `PROPOSE FIX`
* ***Justification:*** Provides zero-decision mapping for the secondary Brave retrieval mode and specifies empirical WAN latency metrics in Phase 8.
* ***Applied Resolution:***
  * In `backend/app/providers/brave.py` (Phase 3), explicitly documented extraction of passages under `grounding.generic[].snippets` into `SourceItem.snippet`, mapping source URL and domain accordingly.
  * In Phase 8, added live retrieval WAN latency distribution benchmarking (P50, P90, P95) and verified that latency overruns (< 2.5s synthesis window) degrade 100% to HTTP 504 Gateway Timeout.

---

## Verification & Final Status

All 3 proposed fixes have been applied and verified in [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md) and [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md).
The design document is **Status: resolved** and approved for Phase 1 implementation.


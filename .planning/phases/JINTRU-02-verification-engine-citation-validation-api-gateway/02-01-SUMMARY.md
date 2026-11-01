# Phase 2 Plan 1: Verification Pipeline Engine Summary

**Execution Status:** Completed
**Phase:** 2 - Verification Engine, Citation Validation & API Gateway
**Plan:** `02-01-PLAN.md`

## 1. Executive Summary
Implemented the deterministic verification engine in `backend/app/services/verification.py` exactly per `misc/docs/designs/jintru_claim_verification.md` § 3.1–3.5 and § Phase 4: conservative Gate A classification, snippet sanitization and injection quarantine, source grouping, Tier 1 / Tier 2 citation validation, the application-level verdict policy, and the monotonic 8.0-second orchestrator. No new runtime dependencies were added.

## 2. Key Accomplishments
- **Gate A (`classify_input`):**
  - Flags non-empirical superlatives in predicate position, moral assertions (`morally/ethically wrong`), and prescriptive social mandates — the latter exempted whenever statutory/legal context is present.
  - Flags future predictions only when a prospective modal co-occurs with an explicit future year (`year > current UTC year`); standalone "will" and historical statements never match.
  - Verified false-positive guards: "Best Buy announced quarterly revenue…", "George Best was a footballer", "The film won Best Picture in 2020", "The bridge was completed in 1937".
- **Sanitization (`sanitize_and_quarantine`):** strips C0/C1 control characters and zero-width characters while preserving `\n`/`\t` for whitespace collapsing, and quarantines `system prompt:`, `override verdict`, `ignore instructions`.
- **Source grouping (`group_sources`):** renumbers `src_N` deterministically across the merged Stage 1 + Stage 2 pool (providers restart IDs per call), canonicalizes registered domains, clusters `source_family_id` by word-boundary wire tokens before falling back to the domain, computes SHA-256 content hashes, and de-duplicates identical snippets.
- **Citations (`validate_citations`):** Tier 1 drops unknown/ quarantined citation IDs and statements left with none; Tier 2 clears excerpts that are not normalized verbatim substrings (`html.unescape`, smart-quote mapping, whitespace collapse).
- **Verdict policy (`apply_verdict_policy`):** blocks `supported` on any direct/contextual `refutes` (→ `contradicted` when direct, else `mixed`), caps single-family corroboration at `insufficient_evidence`, and grounds `contradicted` (direct refutation required) and `mixed` (both stances required) — all with the SSOT limitation wording.
- **Orchestrator (`VerificationPipeline.verify`):** monotonic deadline; `min(stage_budget, remaining)` per stage; Stage 2 only when Stage 1 returned results and remaining ≥ 3.5s using the exact dialectical query; `ProviderTimeoutError(code="SYNTHESIS_WINDOW_EXCEEDED")` raised before dispatch when remaining < 2.5s; quarantined snippets retained in the response but excluded from the prompt.

## 3. Verification & Quality Gates
- `backend/.venv/bin/python -m pytest backend/tests/unit/test_classification.py backend/tests/unit/test_citations.py backend/tests/unit/test_policy.py backend/tests/unit/test_pipeline.py -v` → 40 passed.
- `backend/.venv/bin/python -m pytest backend/tests/ -q` → 65 passed at plan close (Phase 1 suites included).
- `backend/.venv/bin/ruff check backend/` → clean; `backend/.venv/bin/pyright -p backend` → 0 errors.

## 4. Deviations from Plan
1. **Empty snippets are excluded, not emitted with `extraction_status="empty"`.** The SSOT defines the enum, but an item with no snippet cannot serve as evidence; `group_sources` drops it so it never enters the active pool or the response. The field remains available for provider-supplied raw items.
2. **Superlative regex widened for the SSOT's own example.** The literal pattern in § Phase 4 only matches "greatest *of all time*"; CUJ-4's "The Mona Lisa is the greatest painting in human history" needs a bounded noun-phrase gap plus `in <word> history`. The predicate-anchored form still leaves "Best Buy" and "won Best Picture" unflagged.
3. **`mixed` and `contradicted` grounding failures downgrade to `insufficient_evidence`.** Rules 3 and 4 in § Phase 4 state the checks but no failure action; the conservative cap is applied with an explicit limitation, consistent with AGENTS.md rule 6.
4. **Control-character class excludes `\t`, `\n`, `\r`** so the subsequent whitespace collapse (rather than deletion) handles them.

## 5. Requirements Satisfied
- `PIPE-01`: Conservative Gate A pre-retrieval classification with 0 search / 0 LLM calls on short-circuit.
- `PIPE-02`: Monotonic 8.0s orchestrator with two-stage bounded retrieval and the 2.5s synthesis-window guard.
- `CITE-01`: Tier 1 ID presence and Tier 2 normalized verbatim excerpt matching.
- `POL-01`: Deterministic counterevidence and two-domain corroboration guardrails.

## 6. Artifacts
- `backend/app/services/__init__.py`
- `backend/app/services/verification.py`
- `backend/tests/unit/test_classification.py`
- `backend/tests/unit/test_citations.py`
- `backend/tests/unit/test_policy.py`
- `backend/tests/unit/test_pipeline.py`

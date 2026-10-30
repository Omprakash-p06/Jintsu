# Reality Check AI (`jintru`) — Concepts Brief

* **Author:** `jintru` Core Team
* **Date:** 2026-10-30
* **Status:** Approved (Converged Implementation Baseline)
* **Predecessors & Context:** [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md)
* **Design Specification:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)

---

## Overview

`jintru` is a verifiable claim-verification workbench that evaluates factual assertions against live web evidence. It determines whether a claim is supported, contradicted, mixed, or unresolved, and explicitly details what evidence is missing when a conclusion cannot be drawn.

Its core proposition is:
> **"Show what supports a claim, what challenges it, how reliable that evidence is, and exactly what remains unknown."**

The system operates as a single-agent, deterministic pipeline exposed through a typed web interface. It eliminates the systemic failure modes of existing automated fact-checkers (confirmation bias, artificial consensus via syndication, hallucinated certainty, and SSRF vulnerabilities) through six converged architectural mechanisms:

1. **Bounded Dialectical Retrieval (ADR-001):** Single atomic claim input (≤ 500 characters) governed by an authoritative 8.0s synchronous request ceiling. Stage 1 executes focused search via Brave Search snippets (2.3s ceiling, 2.0s subordinate timeout). Stage 2 executes dialectical counterevidence search unconditionally whenever Stage 1 finds results and `remaining_time >= 3.5s`, actively searching for disputes or refutations.
2. **Snippet-First Ingestion & SSRF Elimination (ADR-003):** Raw HTML crawling and custom socket IP-pinning are eliminated; all evidence is ingested strictly via trusted search provider snippets (Brave Search API) and structured context summaries (Brave LLM Context endpoint). Suspicious prompt-injection patterns are quarantined prior to LLM synthesis.
3. **Conservative Pre-Retrieval Screening (Gate A):** Deterministic input classification catches blatant subjective value judgments and future predictions using conservative regex patterns (protecting entity names and historical context), short-circuiting to `not_verifiable` with 0 external API calls.
4. **Single Structured Synthesis Call & 2.5s Execution Guard:** In place of multi-call LLM pipelines, verification runs a single structured synthesis call against the Meta Model API (locked to `muse-spark-1.3` with strict `response_format` JSON schema) within a dedicated 3.0s window. If remaining time before synthesis drops below 2.5s, the system aborts cleanly with an HTTP 504 Gateway Timeout rather than risking mid-stream failure or returning ungrounded pseudo-verdicts.
5. **Two-Domain Corroboration & Counterevidence Guardrail:** Awarding `supported` strictly requires corroboration across at least two distinct source families (registered domains or wire services) and the confirmed absence of unresolved, credible counterevidence. If credible refuting evidence is present, `supported` is barred and the verdict is categorized as `mixed` or `contradicted`. If only a single domain supports the claim, the verdict is capped at `insufficient_evidence`.
6. **Three-Tier Citation Validation:** Tier 1 deterministically verifies citation ID existence. Tier 2 deterministically asserts that quoted reasoning excerpts match normalized source snippet text verbatim. Tier 3 evaluates semantic entailment offline in CI benchmarks.
7. **Flat SQLite Persistence in WAL Mode:** Verification records, limitations, sources, and reasoning statements are stored in a single flat SQLite table with connection-scoped pragmas (`PRAGMA busy_timeout=5000;`, `PRAGMA synchronous=NORMAL;`), providing local data sovereignty with zero telemetry.

---

## Milestone 1 Vertical Slice

The initial release targets a lean, battle-tested vertical slice:
1. Submit one atomic factual assertion (≤ 500 characters) via the React workbench.
2. Screen input deterministically for subjective or future claims (Gate A).
3. Retrieve supporting snippets via Brave Search API (Stage 1).
4. Run dialectical counterevidence search if remaining time ≥ 3.5s (Stage 2).
5. Cluster sources by domain and wire attribution tokens; quarantine injection patterns.
6. Synthesize verdict and extract cited quotes in a single structured Meta Model API call (minimum 2.5s window).
7. Apply deterministic application-level validation: Tier 1/2 citation checks, 2-domain corroboration rule, and counterevidence check.
8. Persist verification snapshot in local SQLite WAL database.
9. Render accessible 5-way verdict badge (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`), stance tags, and expandable quoted source excerpts in the workbench UI.

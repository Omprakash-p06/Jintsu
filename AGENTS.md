<!-- graphicle:start (added by graphicle setup; graphicle disconnect removes it) -->
## Graphicle
Use the `graphicle` MCP server for where or how something works, for questions across files or history, and before changing unfamiliar code: `recall_project` or `query_graph` with the question, then `get_node` and `get_neighbors` for one symbol; answers cite file and lines. For an exact identifier you already know, grep is enough.
Without the server, run `graphicle context "<question>"` in a terminal.
<!-- graphicle:end -->

---

# Reality Check AI (`jintru`) — Repository Engineering Rules

These rules are mandatory for all development, planning, and execution within this repository. They derive directly from the approved design and audit artifacts in `misc/`.

## 1. Single Source of Truth (SSOT) Invariant
All implementations, data schemas, API contracts, and verification pipelines **must strictly conform** to the specifications in `misc/`:
- `misc/docs/designs/jintru_claim_verification.md` (Master Executable Design Specification & Contracts)
- `misc/docs/designs/concepts_brief.md` (Architectural Concepts Brief)
- `misc/docs/specification.md` (Research Foundations & ADRs)
- `misc/consolidated_review_report.md` (EGM Master Review Sign-Off)
- `misc/goldfish_review_report.md` (Contract Resolution Audit)

Never improvise alternative architectures, re-open locked architectural decisions, or add out-of-scope features.

## 2. Scope & Input Ceiling
- **Milestone 1 Scope:** Verifying single atomic empirical assertions (minimum 5, maximum 500 characters).
- **Prohibited:** Compound claim decomposition (FActScore) is deferred to Milestone 2; compound inputs exceeding 500 characters or containing multiple disconnected propositions must be rejected with HTTP 422.

## 3. Retrieval & Dialectical Execution Invariant
- **Two-Stage Bounded Retrieval:**
  - **Stage 1 (Search):** Focused search query via Brave Search API (`/res/v1/web/search` or `/res/v1/llm/context`) returning at most 5 snippets (subordinate timeout: 2.0s).
  - **Stage 2 (Dialectical Counter-Search):** Unconditional dialectical query (`f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`) executed whenever Stage 1 returns results and remaining request time is ≥ 3.5s.
- **Rate-Limit Invariant:** Sequential single-query execution per stage guarantees request QPS ≤ 0.5, naturally respecting Brave Search API rate limits without in-memory token buckets.

## 4. Authoritative Monotonic 8.0-Second SLA Ceiling
- The entire synchronous request lifecycle is strictly capped at **8.0 seconds**:
  - `0.2s` Gate A Pre-Classification
  - `2.3s` Stage 1 Search (timeout: 2.0s)
  - `2.0s` Stage 2 Counter-Search
  - `3.0s` Single Structured Synthesis Call
  - `0.5s` SQLite Persistence & Safety Buffer
- **Minimum Synthesis Window Guard:** At least **2.5s** of remaining time is required before initiating model synthesis. If remaining time drops below 2.5s, the system must abort cleanly and return an `HTTP 504 Gateway Timeout` with a structured `ErrorEnvelope`. Never guess or emit pseudo-verdicts without full LLM synthesis.

## 5. External Provider Contracts
- **Meta Model API Provider:**
  - Base URL: `https://api.meta.ai/v1`
  - Model: Locked to `muse-spark-1.3`
  - Auth: `Authorization: Bearer {META_API_KEY}`
  - Temperature: `0.0`
  - Structured output enforced via `response_format: {"type": "json_schema", "json_schema": {"name": "verification_synthesis", "strict": true, "schema": VerificationSynthesisPayload.model_json_schema()}}`.
- **Brave Search Provider:**
  - Supports `mode="snippets"` (`/res/v1/web/search`) and `mode="context"` (`/res/v1/llm/context`).
  - For `mode="context"`, extract passages under `grounding.generic[].snippets` into `SourceItem.snippet`.
  - Normalize all sources into `SourceItem` with deterministic `source_id = f"src_{idx+1}"`, registered domain extraction, wire attribution tokens (`Associated Press`, `Reuters`, `PR Newswire`) mapped to `source_family_id`, and SHA-256 `content_hash`.

## 6. Deterministic Verdict Policy & Counterevidence Rule
- **Absence of Counterevidence:** Even when multiple distinct domains support a claim, `supported` is **strictly prohibited** if any active source has `stance == "refutes"` with direct or contextual relevance. The verdict must be downgraded to `mixed` (or `contradicted` if refutation is conclusive) with an explicit limitation note.
- **Two-Domain Minimum Corroboration:** In the confirmed absence of counterevidence, awarding `supported` requires corroboration across **at least two distinct `source_family_id` clusters**. Single-domain evidence is capped at `insufficient_evidence`.
- **Contradiction Grounding:** Awarding `contradicted` requires at least one primary source with `stance == "refutes"` and `relevance == "direct"`.

## 7. Three-Tier Citation Validation
- **Tier 1 (Structural):** Every cited source ID in reasoning statements must exist in active retrieved sources.
- **Tier 2 (Provenance Match):** Every `quoted_excerpt` in reasoning statements must exist as a verbatim substring in the cited `SourceItem.snippet` after applying `html.unescape()`, whitespace collapsing, and smart quote normalization.
- **Tier 3 (Semantic Entailment):** Evaluated offline in CI against curated benchmark datasets (target: ≥ 90% citation precision). Ordinary deterministic code must not overclaim semantic proof.

## 8. Conservative Pre-Retrieval Screening (Gate A)
- Flags non-empirical subjective value judgments and future predictions before network calls:
  - Subjective superlatives require predicate context (`is the greatest of all time`) or normative moral prescriptions without statutory context. Proper nouns (e.g., "Best Buy", "George Best") and factual claims ("The film won Best Picture") are never flagged.
  - Future predictions require prospective modal verbs paired with an explicit future year (`year > current_utc_year`). Standalone "will" (names, historical statements, nouns) is never flagged.
  - Uncertain or ambiguous statements fall back to the retrieval pipeline.

## 9. Network Security Boundary (Snippet-First)
- **Zero Raw HTML Crawling:** Ingest evidence strictly through search snippets and LLM context endpoints. Never fetch arbitrary third-party web pages; never implement userland socket IP-pinning.
- **Prompt Injection Defense:** Screen snippets for high-risk injection phrases (`system prompt:`, `override verdict`); quarantine flagged snippets (`is_quarantined = True`) and exclude them from LLM prompts.

## 10. Persistence & Concurrency (SQLite WAL Mode)
- Single flat table `verifications` with JSON columns (`limitations`, `sources`, `reasoning`).
- Connection factory `@asynccontextmanager _connect()` must execute `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;` on **every** opened connection.
- `Database.get_verification(id)` must decode JSON columns via `json.loads()` before returning dict rows.
- Handle write contention via bounded exponential backoff (up to 3 retries).

## 11. Frontend UI & Accessibility Invariants
- Accessible 5-way verdict badge pairing semantic icons with explicit color tokens (`supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo). Never communicate verdict by color alone.
- Target WCAG 2.2 AA with visible focus rings (`#7C3AED`).
- External source links must use `rel="noopener noreferrer"`.
- Use stable Tailwind CSS v4 (`^4.0.0`).

## 12. GSD Phased Roadmap Governance
- All development must follow the 4 coarse phases in `.planning/ROADMAP.md`:
  1. `Phase 1: Foundations, Data Contracts & External Providers`
  2. `Phase 2: Verification Engine, Citation Validation & API Gateway`
  3. `Phase 3: Frontend Wiring & Full-Stack Integration`
  4. `Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking`
- Every phase plan (`*-PLAN.md`) must cite the SSOT documents in `misc/` as its foundation.

## 13. Graphicle Cross-File Coherence Invariant
- During both phase planning and execution, always use Graphicle (`graphicle context "<question>"`, or MCP tools `recall_project`, `query_graph`, `get_node`, `get_neighbors`) to connect all architectural dots across files, dependencies, contracts, and history before introducing changes. No phase plan or execution step may introduce disconnected symbols, mismatched interfaces, or orphaned configurations. All code symbols, API routes, and schema structures must be verified for cross-file alignment.



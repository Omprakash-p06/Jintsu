# Architecture Summary: Reality Check AI (jintru)

## System Design Principles

### 1. Single Source of Truth (SSOT) Invariant
All implementations, data schemas, API contracts, and verification pipelines **must strictly conform** to specifications in `misc/`:
- `misc/docs/designs/jintru_claim_verification.md`
- `misc/docs/designs/concepts_brief.md`
- `misc/docs/specification.md`
- `misc/consolidated_review_report.md`
- `misc/goldfish_review_report.md`

### 2. Scope & Input Ceiling
- **Milestone 1 Scope:** Verifying single atomic empirical assertions (minimum 5, maximum 500 characters)
- **Prohibited:** Compound claim decomposition (FActScore) deferred to Milestone 2
- **Input rejection:** Compound inputs exceeding 500 characters or containing multiple disconnected propositions return HTTP 422

### 3. Retrieval & Dialectical Execution Invariant
- **Two-Stage Bounded Retrieval:**
  - **Stage 1 (Search):** Focused search query via Brave Search API, at most 5 snippets, subordinate timeout 2.0s
  - **Stage 2 (Dialectical Counter-Search):** Unconditional query `f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`, executed whenever Stage 1 returns results and remaining request time ≥ 3.5s
- **Rate-Limit Invariant:** Sequential single-query execution per stage guarantees QPS ≤ 0.5

### 4. Authoritative Monotonic 8.0-Second SLA Ceiling
- Entire synchronous request lifecycle strictly capped at 8.0 seconds
- Breakdown: 0.2s Gate A + 2.3s Stage 1 + 2.0s Stage 2 + 3.0s Synthesis + 0.5s SQLite Buffer
- **Minimum Synthesis Window Guard:** At least 2.5s of remaining time required before initiating model synthesis. If remaining time drops below 2.5s, abort cleanly with HTTP 504 Gateway Timeout

### 5. External Provider Contracts
- **Meta Model API Provider:**
  - Base URL: `https://api.meta.ai/v1`
  - Model: Locked to `muse-spark-1.3`
  - Auth: `Authorization: Bearer {META_API_KEY}`
  - Temperature: `0.0`
  - Structured output via `response_format: {"type": "json_schema", ...}`

- **Brave Search Provider:**
  - Supports `mode="snippets"` (`/res/v1/web/search`) and `mode="context"` (`/res/v1/llm/context`)
  - For `mode="context"`, extract passages under `grounding.generic[].snippets` into `SourceItem.snippet`
  - Normalize sources with deterministic `source_id = f"src_{idx+1}"`, wire attribution tokens (`Associated Press`, `Reuters`, `PR Newswire`) mapped to `source_family_id`, and SHA-256 `content_hash`

### 6. Deterministic Verdict Policy & Counterevidence Rule
- **Absence of Counterevidence:** `supported` strictly prohibited if any active source has `stance == "refutes"` with direct or contextual relevance. Verdict downgraded to `mixed` (or `contradicted` if refutation is conclusive)
- **Two-Domain Minimum Corroboration:** Awarding `supported` requires corroboration across at least two distinct `source_family_id` clusters. Single-domain evidence capped at `insufficient_evidence`
- **Contradiction Grounding:** Awarding `contradicted` requires at least one primary source with `stance == "refutes"` and `relevance == "direct"`

### 7. Three-Tier Citation Validation
- **Tier 1 (Structural):** Every cited source ID in reasoning statements must exist in active retrieved sources
- **Tier 2 (Provenance Match):** Every `quoted_excerpt` must exist as verbatim substring in cited `SourceItem.snippet` after `html.unescape()`, whitespace collapsing, and smart quote normalization
- **Tier 3 (Semantic Entailment):** Evaluated offline in CI against curated benchmark datasets (target: ≥ 90% citation precision)

### 8. Conservative Pre-Retrieval Screening (Gate A)
- Flags non-empirical subjective value judgments and future predictions before network calls
- Subjective superlatives require predicate context or normative moral prescriptions with statutory context
- Future predictions require prospective modal verbs paired with explicit future year

### 9. Network Security Boundary (Snippet-First)
- **Zero Raw HTML Crawling:** Evidence strictly through search snippets and LLM context endpoints
- **Prompt Injection Defense:** Screen snippets for high-risk injection phrases (`system prompt:`, `override verdict`); quarantine flagged snippets (`is_quarantined = True`)

### 10. Conservative Pre-Retrieval Screening (Gate A)
- Flags non-empirical subjective value judgments and future predictions before network calls
- Subjective superlatives require predicate context or normative moral prescriptions with statutory context
- Future predictions require prospective modal verbs paired with explicit future year

### 11. Persistence & Concurrency (SQLite WAL Mode)
- Single flat table `verifications` with JSON columns (`limitations`, `sources`, `reasoning`)
- Connection factory `@asynccontextmanager _connect()` must execute `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;` on every opened connection
- `Database.get_verification(id)` must decode JSON columns via `json.loads()` before returning dict rows
- Handle write contention via bounded exponential backoff (up to 3 retries)

### 12. Frontend UI & Accessibility Invariants
- Accessible 5-way verdict badge pairing semantic icons with explicit color tokens
  - `supported`: emerald, `contradicted`: rose, `mixed`: amber, `insufficient_evidence`: slate, `not_verifiable`: indigo
- **Visible focus rings** (`#7C3AED`)
- Target WCAG 2.2 AA
- External source links must use `rel="noopener noreferrer"`

### 13. Graphicle Cross-File Coherence Invariant
- During both phase planning and execution, always use Graphicle to connect all architectural dots across files, dependencies, contracts, and history
- No phase plan or execution step may introduce disconnected symbols, mismatched interfaces, or orphaned configurations

### 14. GSD Phased Roadmap Governance
- All development must follow 4 coarse phases in `.planning/ROADMAP.md`:
  1. Phase 1: Foundations, Data Contracts & External Providers
  2. Phase 2: Verification Engine, Citation Validation & API Gateway
  3. Phase 3: Frontend Wiring & Full-Stack Integration
  4. Phase 4: Verification Suite, Offline Evals & Live SLA Benchmarking
- Every phase plan (`*-PLAN.md`) must cite the SSOT documents in `misc/` as its foundation
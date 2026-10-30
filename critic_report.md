# Goldfish Review Report (Critic Stage)

**Target:** `docs/designs/jintru_claim_verification.md` (`FeatureRange`: Lines 1–437)

## Reviewer Status

| Reviewer | Lens | Status |
| :--- | :--- | :--- |
| `egm-design` | Hostile Design Critic | completed |
| `egm-structural` | Structural Layout Validator | completed |
| `egm-style` | Technical Copy Editor | completed |

---

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. Latency Budget Contradiction & Unaccounted Decomposition LLM Latency - Severity: 🔴 Blocker
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Section 4 (`RequestBudget`, lines 215–270), Section NFR 1 (lines 411–415), and Section 1 (`Pipeline Lifecycle`, lines 127–128).
* **Discrepancy Description**: 
  1. `RequestBudget.stage_budgets["verdict_synthesis"]` is allocated `1.0s` (line 241). However, NFR 1 explicitly mandates: *"At least 1.5s remaining time is required before initiating a model synthesis call; requests falling below this threshold degrade cleanly rather than timing out mid-stream"* (lines 414–415). Under this definition, if previous stages consume their budgeted allocations (2.5s + 2.0s + 1.5s = 6.0s elapsed; 2.0s remaining), any slight jitter leaving $< 1.5s$ will abort synthesis immediately. Allocating 1.0s to a stage that requires a 1.5s minimum window is an internal logical contradiction.
  2. The pipeline allocates 1.5s for Gate B semantic assessment and 1.0s for Verdict Synthesis over an external remote HTTP API (Meta Model API). For compound claims containing up to 5 atomic propositions, executing Gate B assessments plus JSON synthesis over public networks within 2.5s cumulative LLM time is completely ungrounded given standard cloud LLM TTFT (500–1500ms) and generation token latencies (typically 2–4s per call).
  3. G-1 allows input claims up to 2,000 characters decomposing into up to 5 atomic propositions with temporal anchors (`normalization.py`, line 464). If this decomposition requires an LLM call, it requires another 1.5–2.5s network round-trip that is completely absent from `stage_budgets`.
* **Rationale & Recommendation**: 
  Reconcile `stage_budgets`: Allocate at least 2.5s to synthesis and update the minimum remaining time threshold accordingly. Explicitly define whether proposition decomposition is LLM-based or deterministic; if LLM-based, add a dedicated stage budget (`decomposition: 1.5s`) and adjust the target deadline to 10.0–12.0s or convert `POST /verifications` into an asynchronous endpoint with Server-Sent Events (SSE) streaming rather than a brittle 8.0s synchronous hold.

---

### 2. False Security Assertion in Indirect Injection Defense (CUJ 4 Flaw) - Severity: 🔴 Blocker
* **Reviewer Lens:** `egm-design` & `egm-style`
* **Affected Scope:** CUJ 4 (lines 100–109), Section 3 (Table, lines 206–212), and ADR-003 (lines 200–209).
* **Discrepancy Description**: 
  CUJ 4 Step 4 asserts: *"Even if the model emits a manipulated response, Tier 2 citation validation detects whether the claimed excerpt actually entails the fact, and the application-level validator rejects ungrounded statements"* (line 107).
  This assertion is technically false. Section 3 explicitly defines Tier 2 as a pure verbatim substring match (*"Asserts that the quoted excerpt string exists verbatim... within the fetched source document text"*). It does NOT check entailment. If an adversary hosts a webpage stating a false claim alongside an indirect injection payload, and the manipulated Gate B / Synthesis task quotes that exact sentence verbatim, Tier 2 passes 100%. Furthermore, Section 3 states that Tier 3 entailment is not evaluated deterministically in production (*"In production, Gate B tags relations"*). But if Gate B was manipulated by the injection, the defense collapses.
* **Rationale & Recommendation**: 
  Correct CUJ 4 and Section 3 to eliminate the false claim that Tier 2 validates entailment. Mitigate the poisoning vector at the architecture level: require that any source passage triggering heuristic injection patterns is immediately quarantined from verdict synthesis, and mandate that a `supported` verdict requires corroboration across at least two independent, distinct `source_family_id` clusters from recognized primary domains rather than relying on a single untrusted web excerpt.

---

### 3. Missing Mandatory "Risks & Mitigations" Section - Severity: 🟡 Major
* **Reviewer Lens:** `egm-structural` & `egm-design`
* **Affected Scope:** Document Structure (Lines 1–437) vs Feature Specification Standard (`feature-spec-standard.md`, lines 22–24, 35–36).
* **Discrepancy Description**: 
  The Feature Specification Standard explicitly mandates: *"The specification must explicitly call out its own constraints. It must identify potential failure modes, security implications, scalability limits, and how they will be mitigated"* and requires a dedicated **Risks & Mitigations** section. While security defenses (SSRF, injection) and timeouts are discussed within architecture subsections and Non-Functional Requirements, there is no dedicated `## Risks & Mitigations` section consolidating operational failure modes (provider rate limits, SQLite lock contention, client disconnects, and search provider deprecation).
* **Rationale & Recommendation**: 
  Add a dedicated `## Risks & Mitigations` section addressing operational, reliability, and security risks with explicit mitigation strategies.

---

### 4. Fragility of Tier 2 Verbatim Exact Match on Snippets and HTML Extractions - Severity: 🟡 Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Section 3 (Three-Tier Citation Validation, lines 206–212) and Section 4 (`max_page_fetches`, line 226).
* **Discrepancy Description**: 
  Tier 2 requires quoted excerpts to exist *"verbatim (modulo whitespace normalization) within the fetched source document text."* In practice, sources will often be search snippets (which contain ellipses `...` and concatenated sentence fragments) or HTML body text extracted via libraries (which decode entities `&amp;`, alter smart quotes `“` vs `"`, convert em-dashes `—`, or strip bracketed footnote citations like `[1]`). A strict verbatim equality check will fail, aggressively dropping valid citations and causing false `INVALID_MODEL_OUTPUT` rejections or ungrounded verdicts.
* **Rationale & Recommendation**: 
  Replace strict verbatim string match with a normalized character/token shingle match or fuzzy containment threshold (e.g., token-set containment $\ge 90\%$ or character similarity $\ge 95\%$) that tolerates HTML entity decoding, smart quotes, and snippet truncation artifacts while still rejecting hallucinated quotes.

---

### 5. Inconsistent State Machine Transitions and Conflicting Gate A Responsibilities - Severity: 🟡 Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Section 1 (Architecture Diagram, lines 139–156), Section 2 (State Machine, lines 167–201), and CUJ 3 (lines 90–99).
* **Discrepancy Description**: 
  1. CUJ 3 (line 92) claims: *"Gate A flags the missing coverage; Stage 2 follow-up searches confirm absence of credible data."* However, both the High-Level Architecture Diagram (line 139) and the State Machine (lines 173–178) define Gate A as a deterministic structural filter (`eligible` vs `cannot_verify`). Stage 2 retrieval is triggered exclusively by Gate B / AppRouter via `needs_more_evidence`.
  2. In Section 2, `GateB_Assessment` transitions to `needs_more_evidence` or `conflict_detected`. There is NO transition from `GateB_Assessment` directly to `eligible` or `Verdict_Synthesis` when evidence is complete, relevant, and undisputed.
* **Rationale & Recommendation**: 
  Update the State Machine diagram to include the primary happy-path transition: `GateB_Assessment --> eligible: Unanimous / Sufficient Evidence Found`. Update CUJ 3 to clarify that Gate B (not Gate A) diagnoses missing coverage and triggers Stage 2 follow-up searches.

---

### 6. Brave Search Rate Limits (1–5 QPS) and Client Disconnect Leaks - Severity: 🟡 Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Section 4 (`RequestBudget`, lines 220–228), ADR-001 (lines 149–154), and Section NFR 2 (lines 416–420).
* **Discrepancy Description**: 
  `RequestBudget` permits up to 10 distinct queries, 12 provider attempts, and a concurrency of 3 within a single 8.0s window. Brave Search standard API plans enforce strict rate limits (1 QPS on Free/Base, or 5–20 QPS on standard tiers). Dispatching 3 concurrent queries for a decomposed claim will immediately trigger HTTP 429 rate limits. Furthermore, if a user navigates away or closes the browser tab during the 8.0s synchronous hold, FastAPI does not automatically terminate running background coroutines unless explicitly checking `request.is_disconnected()`.
* **Rationale & Recommendation**: 
  Implement a client-side token bucket rate limiter for the Brave adapter; stagger queries to conform to plan QPS; and integrate FastAPI `request.is_disconnected()` cancellation checks into the orchestrator loop to abort in-flight searches when the user disconnects.

---

### 7. SQLite Lock Contention and Unspecified Concurrency Safeguards - Severity: 🟡 Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Section 7 (Schema Design, lines 301–356) and NFR 1 (lines 411–415).
* **Discrepancy Description**: 
  Verification records, atomic claims, sources, and reasoning statements are persisted across 4 relational tables in local SQLite via async SQLAlchemy 2.x (`aiosqlite`). In default SQLite configurations (rollback journal, default busy timeout of 0s), any concurrent write will block the database with `OperationalError: database is locked`. The design allocates only a 0.5s safety buffer for serialization and DB writes.
* **Rationale & Recommendation**: 
  Explicitly mandate that the SQLite connection pool configure Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), `PRAGMA synchronous=NORMAL;`, and an explicit `PRAGMA busy_timeout=5000;`. For benchmark runs (`evals/run_evals.py`), use an isolated temporary database.

---

### 8. Structural Template Gaps & Retained Resolved Questions - Severity: 🟡 Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** Line 55 (`## Open Questions & Resolution Status`) and Line 61 (`OQ-5`)
* **Discrepancy Description**: 
  The blueprint `design_doc.md` specifies the exact section heading `## Open Questions` and instructs: *"Remove answered questions as they are resolved."* Line 61 retains question `OQ-5` marked as `**RESOLVED.**` and embeds the resolution inline.
* **Rationale & Recommendation**: 
  Rename heading to `## Open Questions`. Remove resolved `OQ-5` from the list and move its decision rationale into Section 4 / Section 8.

---

### 9. Ungrounded Absolute Claims & Security Hyperbole - Severity: 🟡 Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Section 6 (Lines 285, 295)
* **Discrepancy Description**: 
  Line 285 claims: *"To eliminate Server-Side Request Forgery vulnerabilities..."* and Line 295 claims: *"This completely prevents Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks."* Absolute guarantees ("eliminate", "completely prevents") constitute ungrounded certainty claims.
* **Rationale & Recommendation**: 
  Replace "eliminate" with "mitigate", and rephrase line 295 to: "This prevents Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding by opening the socket directly to the validated IP address."

---

### 10. Philosophical Buzzword Overuse ("Dialectical") - Severity: 🟡 Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Overview (Line 11), Goal G-1 (Line 31), CUJ 2 (Line 79), Alternative A (Line 371)
* **Discrepancy Description**: 
  The term "dialectical" is repeatedly applied across four sections ("dialectical process", "Bounded Dialectical Verification", "Dialectical Ingestion", "Dialectical Fan-Out"). This is non-technical jargon that obscures concrete engineering operations.
* **Rationale & Recommendation**: 
  Replace with descriptive technical terms: "two-sided verification process", "bidirectional evidence retrieval", and "concurrent support/counter search fan-out".

---

### 11. Minor Formatting, Caching, and Phrasing Nits - Severity: 🟢 Nit
* **Reviewer Lens:** `egm-design`, `egm-structural`, `egm-style`
* **Affected Scope:** Lines 1, 63, 110, 279, 293, 367, 398, 412
* **Discrepancy Description**:
  - Raw LaTeX math delimiters (`$\ge 0.85$`, `$\le$ 3.0s`) are used in Markdown text instead of plain Unicode symbols (`≥ 0.85`, `≤ 3.0s`).
  - Extraneous horizontal rules placed between sub-sections disrupt layout symmetry.
  - Line 293 specifies `http://198.51.100.24:443/article` (mixing HTTP scheme with HTTPS port 443).
  - Phantom cache architecture referenced in NFR 1 without cache key definition or TTL policy.
  - Tautological title: "Verifiable Claim Verification System".
* **Rationale & Recommendation**: 
  Clean up math formatting, fix URL scheme, remove unnecessary horizontal rules, define or prune cache references, and simplify title.


# Comprehension Test Report: Reality Check AI (`jintru`)

**Target File:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)  
**Evaluator:** Naive Reader (Comprehension Goldfish, Stage 6 EGM Protocol)  
**Target Scopes:** `FeatureRange` (Lines 1–377), `DetailedRange` (Lines 378–769)  
**Reference Context:** [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md), [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md)  
**Review Stage:** Stage 6

---

#### What this proposes
The document proposes an automated claim-verification system (`jintru`) for Milestone 1 that evaluates single atomic factual statements (up to 500 characters) against live web search snippets within an authoritative 8.0-second synchronous SLA. The system implements a deterministic, multi-stage pipeline comprising pre-retrieval classification, bounded two-stage retrieval via Brave Search, heuristic source-family clustering, a single structured LLM synthesis call via Meta Model API, and application-level citation and corroboration validation. Persisted locally in a single SQLite table in WAL mode, the results are classified into a 5-way verdict taxonomy (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`) and presented through a React-based single-page web workbench featuring side-by-side stance breakdowns and verifiable excerpt matching.

#### How the existing system works, per this document
The document describes current automated fact-checking and retrieval-augmented language model systems as suffering from five critical failure modes: confirmation bias favoring the query framing, artificial consensus caused by syndicated wire republication across distinct URLs, uncalibrated certainty and fabricated citations when evidence is absent, temporal/scoping conflations between historical and current metrics, and SSRF/indirect prompt injection vulnerabilities from raw HTML web fetching. Within `jintru` itself, there is no prior existing codebase or operational legacy deployment described; rather, the document establishes the initial greenfield system baseline for Milestone 1, explicitly superseding older exploratory design ideas (such as multi-sentence decomposition, raw socket IP-pinned crawling, multi-agent argumentation, and multi-table relational schemas).

---

### Overall Verdict
🔴 **FAIL — ACTION REQUIRED BEFORE IMPLEMENTATION**  
The document possesses substantial architectural depth and high rigor in many areas, but contains **2 Blocker**-level contract/runtime discrepancies, **5 Major** operational/specification gaps, and **5 Minor/Nit** points of ambiguity that must be resolved to achieve zero-decision, deterministic implementation.

---

### Findings & Discrepancies

#### 🔴 Blocker Findings

##### 1. Tier 2 Citation Validation Operates on Nonexistent Excerpt Field in `ReasoningStatement`
* **Severity:** 🔴 Blocker
* **Affected Scope:** Section 3 (Lines 227–232), Phase 2 (Lines 461–471), Phase 4 (Lines 646–648).
* **Discrepancy Description & Rationale:**
  * In the Three-Tier Citation Validation table (lines 227–232), Tier 2 is defined as: *"Asserts that quoted excerpts exist as a substring within source text after applying html.unescape(), collapsing multiple spaces, and normalizing smart quotes. Failure Action: Reject citation link; drop ungrounded excerpt."*
  * In Phase 4 (lines 646–648), the citation validation function signature is specified as:
    ```python
    validate_citations(statements: list[ReasoningStatement], sources: list[SourceItem]) -> list[ReasoningStatement]
    ```
    with Tier 2 explicitly tasked to: *"Normalize excerpt (html.unescape(), whitespace collapse, smart quote normalization) and assert exact substring presence."*
  * However, in Phase 2 `backend/app/api/schemas.py` (lines 461–464), `ReasoningStatement` is defined as:
    ```python
    class ReasoningStatement(BaseModel):
        statement: str
        citation_ids: list[str] = Field(default_factory=list)
    ```
    `ReasoningStatement` contains only `statement` and `citation_ids`—it contains NO quote or excerpt field!
  * Meanwhile, `exact_quote` exists on `SourceEvaluationItem` (line 469), which is nested inside `VerificationSynthesisPayload` (line 476). But `VerificationSynthesisPayload` is not passed into `validate_citations`.
  * Consequently, an implementing engineer cannot execute Tier 2 excerpt substring verification. It is fundamentally impossible to validate quoted excerpts when the data model passed to the validator does not contain excerpts.
* **Remediation:** Add `quoted_excerpt: Optional[str] = None` to `ReasoningStatement`, or pass `source_evaluations` into `validate_citations`, and merge validated evaluations into `SourceItem`.

##### 2. Deserialization Failure on Read from SQLite JSON Columns into `VerificationResponse`
* **Severity:** 🔴 Blocker
* **Affected Scope:** Phase 2 (Lines 551–564, 572–578), Phase 5 (Line 660), Schemas (Lines 481–490).
* **Discrepancy Description & Rationale:**
  * In `Database.save_verification` (lines 559–563), structured lists are dumped to JSON text strings before insertion into SQLite:
    ```python
    json.dumps(record.limitations),
    json.dumps([s.model_dump() for s in record.sources]),
    json.dumps([r.model_dump() for r in record.reasoning]),
    ```
  * In `Database.get_verification` (lines 572–578), the implementation executes `SELECT * FROM verifications WHERE id = ?` and directly returns `dict(row)`. In SQLite, these JSON columns are returned as raw `TEXT` strings.
  * In Phase 5 (line 660), `GET /api/v1/verifications/{id}` returns this record against `response_model=VerificationResponse`.
  * In `VerificationResponse` (lines 481–490), the fields are typed as `limitations: list[str]`, `sources: list[SourceItem]`, and `reasoning: list[ReasoningStatement]`. In Pydantic v2, passing a JSON string (e.g. `'[{"source_id": "..."}]'`) to a `list[SourceItem]` field does not automatically parse the string into objects; it raises a runtime `ValidationError` (`Input should be a valid list`).
  * `Database.get_verification` lacks `json.loads()` deserialization hooks, which guarantees an HTTP 500 error on every single read-by-ID operation.
* **Remediation:** In `get_verification` and `list_verifications`, explicitly decode JSON columns using `json.loads()` before returning dict rows.

---

#### 🟡 Major Findings

##### 3. Undefined Evaluation Logic for Stage 2 Counter-Search Trigger and Query Formulation
* **Severity:** 🟡 Major
* **Affected Scope:** CUJ 2 (Lines 89–91), System Architecture (Lines 161–164), State Machine (Line 203), Latency Budget (Lines 241–242), Phase 4 (Line 651).
* **Discrepancy Description & Rationale:**
  * The architecture states that Stage 2 counterevidence retrieval is triggered *"only when Stage 1 evidence is one-sided or disputed, and remaining time >= 3.5s"*.
  * However, between Stage 1 and Stage 2, zero LLM calls have occurred. The document provides no algorithm or heuristic for how code determines whether raw search snippets are "one-sided" or "disputed".
  * Furthermore, the document never specifies how the counterevidence query string is constructed.
* **Remediation:** Make Stage 2 dialectical search an unconditional two-sided retrieval step whenever `remaining_time >= 3.5s`. In Stage 1, search the direct claim. In Stage 2, search counterevidence with dialectical query formulation (e.g., adding `false OR dispute OR criticism`).

##### 4. Missing Wire Protocol Specification & Model Identifier for Model Provider
* **Severity:** 🟡 Major
* **Affected Scope:** OQ-3 (Line 64), Settings (Lines 420–421), Phase 3 (Lines 631–632).
* **Discrepancy Description & Rationale:**
  * The document specifies `META_API_BASE_URL: str = "https://api.meta.ai/v1"` which is not a standard public developer endpoint.
  * `Settings` does not define a model name field, request path, HTTP method, or payload wrapper schema.
* **Remediation:** Standardize on OpenAI-compatible `/chat/completions` configuration with `LLM_API_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL_NAME`.

##### 5. Structural Loss of `source_evaluations` Between Synthesis Payload, DB, and UI
* **Severity:** 🟡 Major
* **Affected Scope:** Phase 2 Schemas (Lines 465–489), CUJ 2 (Line 96), Phase 6 (Line 715).
* **Discrepancy Description & Rationale:**
  * The model outputs `VerificationSynthesisPayload` containing `source_evaluations` with `stance`, `relevance`, `exact_quote`, and `relationship_explanation`.
  * However, `VerificationResponse` and SQLite only include `sources: list[SourceItem]` and `reasoning`.
  * If `source_evaluations` is not merged into `SourceItem`, the UI cannot fulfill CUJ 2's requirement to show side-by-side stance breakdowns and why sources disagree.
* **Remediation:** Include `relevance`, `relationship_explanation`, and `exact_quote` in `SourceItem`, and have the orchestrator merge the model's evaluations into `SourceItem` before returning and saving.

##### 6. Contradictory Degradation Behavior When Synthesis Window is < 1.5s
* **Severity:** 🟡 Major
* **Affected Scope:** Line 66 (OQ-5), Line 242 (Budget Table), Line 330 (Risks & Mitigations), Line 361 (Non-Functional Requirements).
* **Discrepancy Description & Rationale:**
  * Line 242 states "return partial" when remaining time < 1.5s, while Lines 66, 247, and 330 state that an HTTP 504 Gateway Timeout is returned.
* **Remediation:** Reconcile: If remaining time before synthesis is < 2.5s (or 3.0s), abort cleanly and return an HTTP 504 Gateway Timeout with `ErrorEnvelope`.

##### 7. SQLite Connection Pragmas Not Enforced on CRUD Operations
* **Severity:** 🟡 Major
* **Affected Scope:** Section 7 (Lines 294–300), Phase 2 (Lines 526–530, 548–609).
* **Discrepancy Description & Rationale:**
  * `PRAGMA busy_timeout` and `PRAGMA synchronous` are connection-scoped. Executing them only in `init_db()` leaves all subsequent CRUD connections with `busy_timeout = 0`.
* **Remediation:** Implement a shared connection helper `async def get_connection()` executing `PRAGMA busy_timeout=5000;` on every new connection.

---

#### 🟢 Nit Findings

##### 8. Overloaded Use of "Gate A" for Both Pre-Retrieval and Post-Retrieval Screening
* Differentiate Gate A (Pre-Retrieval Input Filter) from Gate B (Evidence Sufficiency Filter).

##### 9. Pre-Retrieval Classification Implementation Imprecision
* Specify regex word boundaries (`\b(should|ought)\b`) and dynamic 4-digit future year comparison.

##### 10. Undefined Acronyms and Unlinked Reference Benchmarks
* Add explicit definitions for `CoBiT`, `ALCE`, and `FActScore`.

##### 11. Nomenclature Collision of "Phase 2"
* Disambiguate implementation plan phases from roadmap milestones.

##### 12. Frontend Typecheck Missing API Schema Prerequisite
* Specify that `src/api/schema.d.ts` is pre-generated and checked in.

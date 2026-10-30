# Intermediate Zoom Out Architectural Audit Report (Stage 8)

**Target Document:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)  
**Auditor:** Skeptical Architect (Zoom Out Goldfish)  
**Standard Applied:** [Zoom Out Standard](file:///home/omprakash/.gemini/config/plugins/egm/resources/document_standards/zoom-out-standard.md)  
**Inputs Evaluated:**
- [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)
- [`zoom_out_report.md`](file:///home/omprakash/Documents/jintru/zoom_out_report.md) (Stage 5 Baseline)
- [`comprehension_report.md`](file:///home/omprakash/Documents/jintru/comprehension_report.md) (Stage 6 Naive Comprehension)
- [`critic_report.md`](file:///home/omprakash/Documents/jintru/critic_report.md) (Stage 7 Hostile Critic Swarm)

---

## 1. Executive Summary & 30,000-Foot Architectural Re-evaluation

Following the hostile and granular evaluations of Stage 6 (Comprehension) and Stage 7 (Critic Swarm), the system architecture has been re-evaluated from the 30,000-foot altitude. 

The core architectural direction of Milestone 1 remains **unquestionably sound and minimal**:
- **Single atomic factual claim input** ($\le 500$ characters).
- **Sequential bounded search** (Stage 1 direct + Stage 2 counterevidence).
- **Single remote LLM synthesis call** in a structured format.
- **Snippet-first network boundary** (no arbitrary HTML scraping or SSRF hazards).
- **Flat SQLite persistence** in WAL mode.

However, the Comprehension and Critic passes identified **5 critical runtime and contract disconnects** that would have caused immediate runtime crashes or SLA failures during execution. Crucially, none of these blockers represent foundational architectural failures; they are interface and protocol precision gaps. 

Applying **hostile YAGNI scrutiny** to each proposed fix confirms that they can be resolved **surgically with zero architectural bloat**, zero additional external dependencies, and zero speculative abstractions.

---

## 2. Hostile Scrutiny of the 5 Target Blockers & Proposed Fixes

### Blocker 1: Tier 2 Citation Excerpt Missing from Data Contract
* **The Root Cause:** The design mandates Tier 2 excerpt substring verification, but `ReasoningStatement` only contains `statement: str` and `citation_ids: list[str]`. The model emits `exact_quote` within `SourceEvaluationItem`, but that payload was not passed to the validator, nor merged into `SourceItem` or `ReasoningStatement`.
* **Hostile Scrutiny & Anti-Overengineering Review:**
  * *Rejected Over-Engineering:* Introducing a complex bi-directional graph structure or citation reconciliation engine.
  * *Surgical YAGNI Remedy:*
    1. In `schemas.py`: Add `quoted_excerpt: Optional[str] = None` to `ReasoningStatement`, and add `exact_quote: Optional[str] = None` and `relevance: Optional[str] = None` to `SourceItem`.
    2. In `VerificationPipeline`: Have the orchestrator merge the LLM's `source_evaluations` into the active `SourceItem` list.
    3. In `validate_citations(statements, sources)`: Enforce Tier 1 (ID check) and Tier 2: if `statement.quoted_excerpt` or `source.exact_quote` is provided, normalize both strings (`html.unescape()`, collapse whitespace) and assert exact substring containment against `source.snippet`. If containment fails, strip the citation link.
  * **Architectural Verdict:** Approved. Maintains clean Pydantic boundaries with zero overhead.

### Blocker 2: SQLite JSON Deserialization Failure on Read
* **The Root Cause:** `Database.save_verification` serializes lists to JSON strings. `Database.get_verification` executed `SELECT *` and returned raw SQLite `TEXT` strings. Passing this directly to `VerificationResponse` causes Pydantic v2 to throw a fatal `ValidationError` on every read-by-ID endpoint call.
* **Hostile Scrutiny & Anti-Overengineering Review:**
  * *Rejected Over-Engineering:* Introducing SQLAlchemy, SQLModel, Alembic, or an ORM layer.
  * *Surgical YAGNI Remedy:*
    In `Database.get_verification(id)`: explicitly deserialize JSON columns before returning the dictionary:
    ```python
    d = dict(row)
    for col in ("limitations", "sources", "reasoning"):
        if isinstance(d.get(col), str):
            d[col] = json.loads(d[col])
    return d
    ```
    (Note: `list_verifications` does not select these JSON columns, so it remains ultra-fast and unaffected).
  * **Architectural Verdict:** Approved. 4 lines of native standard library code; preserves zero-dependency flat SQLite architecture.

### Blocker 3: Stage 2 Counterevidence Trigger Lacked Deterministic Decision Logic
* **The Root Cause:** The design stated Stage 2 counterevidence retrieval is triggered "only when Stage 1 evidence is one-sided or disputed, and remaining time $\ge 3.5$s". Because zero LLM calls have occurred at this stage, the backend has no semantic understanding of whether raw snippets are "one-sided" or "disputed".
* **Hostile Scrutiny & Anti-Overengineering Review:**
  * *Rejected Over-Engineering:* Adding a local sentiment model, an intermediate small LLM call, or a bespoke heuristic stance classifier on raw search snippets.
  * *Surgical YAGNI Remedy:*
    Make Stage 2 dialectical search **unconditional whenever `remaining_time >= 3.5s` and Stage 1 returned usable results**:
    - Stage 1 queries the direct factual claim: `f"{claim}"`.
    - Stage 2 queries dialectical counterevidence: `f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`.
    - If `remaining_time < 3.5s`, Stage 2 is deterministically skipped.
    This fulfills the core mission of active dialectical verification without confirmation bias, guarantees bounded QPS (at most 2 queries per request), and requires zero extra infrastructure.
  * **Architectural Verdict:** Approved. Completely deterministic, robust, and eliminates speculative heuristic classifiers.

### Blocker 4: 1.5s Minimum Synthesis Window is Statistically Unachievable Over WAN
* **The Root Cause:** `VerificationSynthesisPayload` is a deeply structured 400–600 token JSON schema. Over public WAN endpoints, TTFT (300–800ms) + generation (2.0–4.0s) requires a minimum of 2.5s. Attempting synthesis with only 1.5s remaining guarantees a socket timeout or SLA breach 100% of the time. Additionally, the spec contained a contradiction: Line 242 stated "return partial" while Lines 66 and 330 stated "HTTP 504".
* **Hostile Scrutiny & Anti-Overengineering Review:**
  * *Rejected Over-Engineering:* Implementing complex streaming partial recovery or speculative token speculative decoding.
  * *Surgical YAGNI Remedy:*
    1. Raise the minimum synthesis window threshold from 1.5s to **2.5s**.
    2. Reconcile the failure behavior: If `remaining_time < 2.5s` before synthesis begins, abort cleanly and return an **HTTP 504 Gateway Timeout** with structured `ErrorEnvelope`. Never attempt to return an ungrounded "partial" verdict when synthesis has not executed.
  * **Architectural Verdict:** Approved. Eliminates dead-end WAN calls and aligns with the 8.0s hard SLA budget table.

### Blocker 5: SQLite `PRAGMA busy_timeout` Connection Scope Vulnerability
* **The Root Cause:** In SQLite, `PRAGMA busy_timeout` and `PRAGMA synchronous` are connection-scoped. Executing them once in `init_db()` leaves all subsequent connections opened in CRUD methods with default `busy_timeout = 0ms`, leading to immediate `database is locked` errors during concurrent operations.
* **Hostile Scrutiny & Anti-Overengineering Review:**
  * *Rejected Over-Engineering:* Adding thread-locking primitives, background write worker queues, or external connection pooling packages.
  * *Surgical YAGNI Remedy:*
    In `backend/app/db/database.py`, add a clean context manager helper:
    ```python
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA synchronous = NORMAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            yield db
    ```
    Route all CRUD methods through `self.get_connection()`.
  * **Architectural Verdict:** Approved. Standard library / `aiosqlite` pattern, eliminates duplicated connection logic across 5 methods.

---

## 3. Hostile Scrutiny of Secondary Critic & Comprehension Findings

| Finding | Severity | Proposed Action | Skeptical Architect Assessment |
| :--- | :---: | :--- | :--- |
| **CR-04: Gate A Keyword False Positives** | Major | Use regex word boundaries `\b(should\|ought)\b` and compare 4-digit future years against UTC current year. | **Approve.** Essential bugfix. Unanchored substring `best` rejected "Best Actor" and "Best Buy". Standard regex is zero-cost. |
| **CR-05 / CR-06: Injection Quarantine & Prompt Escaping** | Major | Drop raw keyword substring quarantine; apply `html.escape(snippet, quote=True)` on prompt inputs; rely on 2-domain corroboration rule. | **Approve.** Keyword quarantine censored valid cybersecurity assertions. `html.escape` prevents XML breakout with zero complexity. |
| **CR-07: "Authoritative" Source Rule Ambiguity** | Major | Replace undefined "authoritative" single source for `contradicted` with strict structural rule: require $\ge 2$ independent source families with `stance="refutes"`. | **Approve.** Enforces consistent algorithmic policy without arbitrary authority scoring. |
| **CR-08: Public Suffix Domain Clustering** | Major | Lightweight registered domain parser for common two-part suffixes (`.co.uk`, `.gov.in`). | **Approve with Caution.** Do NOT pull in heavy dynamic suffix-fetching libraries. A simple internal regex/suffix set keeps it self-contained. |
| **CR-10 / Nit 8: Terminology Overload ("Gate A")** | Major | Differentiate Gate A (Pre-Retrieval Input Filter) from Gate B (Evidence Sufficiency Filter). | **Approve.** High-altitude clarity; prevents conflating input validation with search results screening. |
| **CR-11: Absolute File URIs in Header** | Major | Convert `file:///home/omprakash/...` to relative markdown links `./concepts_brief.md`, `../specification.md`. | **Approve.** Essential git repository hygiene. |
| **CR-14 / Finding 4: API Endpoint Specification** | Nit | Standardize on OpenAI-compatible `/chat/completions` configuration (`LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`). | **Approve.** Replaces fictitious `api.meta.ai` with universal standard interface. |

---

## 4. Master Architectural Convergence Checklist

To achieve full compliance and implementation readiness, the master document [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md) must be updated with the following surgical modifications:

1. [ ] **Metadata Links (CR-11):** Convert absolute file URIs (lines 6–8) to relative Markdown paths.
2. [ ] **Gate Nomenclature (CR-10):** Name Phase 1 pre-retrieval classification **Gate A** and Phase 1 post-retrieval snippet screening **Gate B**.
3. [ ] **Gate A Classification Regex (CR-04):** Update `classify_input` to use `\b(should|ought)\b` and dynamic numeric year comparison for future claims.
4. [ ] **Stage 2 Dialectical Retrieval Rule (CR-01):** Formulate Stage 2 query dialectically (`f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"`) and execute unconditionally whenever `remaining_time >= 3.5s` and Stage 1 found results.
5. [ ] **Synthesis Timeout & Degradation (CR-02, CR-09):** Update synthesis threshold to `2.5s`; standardize timeout degradation behavior to return HTTP 504 Gateway Timeout with `ErrorEnvelope`.
6. [ ] **XML Delimiter Escaping (CR-06):** Specify `html.escape(snippet, quote=True)` on search evidence inserted into XML prompt blocks.
7. [ ] **Contradicted Rule Precision (CR-07):** Update `contradicted` policy to require $\ge 2$ independent domain families with `stance="refutes"`.
8. [ ] **Pydantic Schemas (Blocker 1, Stage 6 Finding 5):**
   - Add `quoted_excerpt: Optional[str] = None` to `ReasoningStatement`.
   - Add `relevance: Optional[str] = None` and `exact_quote: Optional[str] = None` to `SourceItem`.
9. [ ] **Database Connection Helper & Deserialization (Blocker 2, Blocker 5):**
   - Add `@asynccontextmanager async def get_connection()` in `Database` setting `PRAGMA busy_timeout = 5000;` and `PRAGMA synchronous = NORMAL;`.
   - Update `get_verification()` to deserialize `limitations`, `sources`, and `reasoning` via `json.loads()`.
10. [ ] **Provider Configuration (CR-14):** Standardize settings to generic OpenAI-compatible environment variables (`LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`).

---

## 5. Architectural Verdict & Sign-Off

🟢 **CONVERGED & APPROVED (SUBJECT TO SURGICAL REVISIONS)**

The architecture is lean, sound, and free of speculative abstractions. The proposed fixes resolve every identified runtime, concurrency, and schema defect without adding architectural complexity. Once the 10 surgical updates listed above are applied to [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md), the document will be fully ready for deterministic Phase 1–8 execution.

# Comprehension Review Report: `docs/designs/jintru_claim_verification.md`

**Auditor:** Naive Reader (Comprehension Goldfish)  
**Target Document:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)  
**Scopes Evaluated:** `FeatureRange` (Lines 1–437) & `DetailedRange` (Lines 438–518)  
**Mode:** REVIEW  

---

### Paraphrase

#### What this proposes
The document proposes `jintru` (Reality Check AI), a claim-verification system consisting of a React workbench frontend and a FastAPI backend that verifies factual claims against live web evidence within an authoritative 8.0-second synchronous deadline. The architecture decomposes user inputs into up to 5 atomic claims, executes bounded two-stage dialectical retrieval via Brave Search, clusters syndicated sources using MinHash text fingerprinting, and evaluates evidence through a two-stage sufficiency pipeline consisting of deterministic screening (Gate A) and semantic model assessment (Gate B). Verified claims are classified into a five-way public verdict taxonomy (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`) backed by three-tier citation validation, hardened SSRF and prompt-injection boundaries, and local SQLite persistence.

#### How the existing system works, per this document
The document characterizes existing automated fact-checking and retrieval-augmented generation (RAG) tools as suffering from systemic confirmation bias because standard retrieval pipelines formulate search queries that mirror the user's premise rather than discovering counterevidence. These systems frequently mistake syndicated press releases across multiple URLs for independent consensus and produce hallucinated or uncalibrated verdicts when evidence is absent, conflicting, or temporally mismatched. Furthermore, conventional pipelines lack robust pre-socket network defenses against SSRF attacks (such as DNS rebinding and redirect hopping) and fail to protect downstream reasoning models from indirect prompt injections embedded within retrieved web text.

---

### Prioritized Audit Findings

#### Finding 1: Contradiction in Citation Tier Responsibilities (Entailment vs. Exact Match)
* **Severity**: 🔴 **Blocker**
* **Affected Scope**: Section "Critical User Journeys", CUJ 4 (Line 107) vs. Section 3 "Three-Tier Citation Validation Architecture" (Lines 207–212)
* **Discrepancy Description & Rationale**:
  In CUJ 4 (line 107), the text asserts: *"Even if the model emits a manipulated response, Tier 2 citation validation detects whether the claimed excerpt actually entails the fact..."*
  However, in Section 3, Table "Three-Tier Citation Validation Architecture" (lines 207–212), Tier 2 is explicitly defined as a deterministic verbatim string check (*"Asserts that the quoted excerpt string exists verbatim (modulo whitespace normalization) within the fetched source document text"*), while semantic entailment verification is assigned exclusively to **Tier 3** (*"Evaluates whether the cited passage logically entails the asserted fact"*).
  This creates a direct internal contradiction. A developer implementing Tier 2 would not know whether Tier 2 requires a lightweight substring match or a natural language entailment model.

#### Finding 2: Missing Pipeline Components in Implementation Plan ("Conflict Resolver" and "Evidence Gap Diagnoser")
* **Severity**: 🔴 **Blocker**
* **Affected Scope**: Section 1 Architecture Diagram (Line 147), CUJ 2 (Line 87), CUJ 3 (Line 96) vs. Section "Detailed Implementation Plan" (Lines 461–470)
* **Discrepancy Description & Rationale**:
  The document details two major functional blocks in the architecture flow and user journeys:
  1. The *"Conflict Resolver"* / *"Conflict & Disagreement Resolver"* (`ConflictMod` in flowchart line 147; invoked in CUJ 2 line 87).
  2. The *"Evidence Gap Diagnoser"* (invoked in CUJ 3 line 96: *"The pipeline halts before calling verdict synthesis and invokes the Evidence Gap Diagnoser"*).
  However, neither module appears in the *Detailed Implementation Plan* under `backend/app/services/` (lines 461–470). It is unclear whether these are intended to be independent service classes, internal routing helper functions within `orchestrator.py` or `sufficiency.py`, or dedicated LLM prompts. A fresh team member cannot determine which file owns these responsibilities.

#### Finding 3: Omission of Stage 1 Retrieval in Pipeline State Machine
* **Severity**: 🟡 **Major**
* **Affected Scope**: Section 2 "State Machine: Internal Pipeline States to Public Verdicts" (Lines 167–201)
* **Discrepancy Description & Rationale**:
  In the state diagram, the request transitions directly from `Ingested` to `GateA_Screening` with the label `"Normalized & Decomposed"`. It then transitions through `eligible` to `GateB_Assessment`, and only introduces retrieval later as `Stage2_Retrieval` (triggered by `needs_more_evidence`).
  This conflicts with the High-Level System Architecture flowchart (lines 128–139) and CUJ 1 (lines 71–73), where initial bounded search (Stage 1 retrieval) happens prior to Gate A screening. As drawn, the state machine implies Gate A screens un-retrieved propositions or that Stage 1 retrieval does not exist as a state transition.

#### Finding 4: Unspecified Full-Page Fetch (`HttpFetch`) Triggering Criteria and Workflow
* **Severity**: 🟡 **Major**
* **Affected Scope**: Section 1 Architecture (Line 132), Section 4 Request Budget (Lines 226, 239), and Section 4 Services (Line 465)
* **Discrepancy Description & Rationale**:
  The architecture includes an SSRF-guarded `HttpFetch` client, defines a hard ceiling of `max_page_fetches = 5`, and allocates 2.0 seconds for `"counter_and_fetch"`. However, nowhere in the document are the operational criteria or triggers for `HttpFetch` defined.
  It is left unspecified whether full-page fetches are dispatched for all top search results, only when search snippets fail Gate A's soft relevance check, or only during Stage 2 counterevidence retrieval. Without explicit triggering rules, an engineer cannot implement the retrieval coordinator.

#### Finding 5: Unexplained Counterquery Generation Mechanism
* **Severity**: 🟡 **Major**
* **Affected Scope**: Section 4 Budget (Line 239), Section 1 Architecture (Line 146), and Section 4 Services (Line 465)
* **Discrepancy Description & Rationale**:
  When Gate B marks an assessment as `needs_more_evidence` and triggers Stage 2 retrieval with intent `counterevidence_seeking`, the document does not explain how the counterquery string is generated.
  It is unspecified whether the query is generated by an additional LLM call, deterministically constructed by applying negation heuristics to the proposition, or returned directly as a field in Gate B's structured assessment output. If an additional LLM call is required, its latency and attempt reservation are unaccounted for in the request budget.

#### Finding 6: Request Budget Stage Durations and Synthesis Threshold Discrepancy
* **Severity**: 🟡 **Major**
* **Affected Scope**: Section 4 "Authoritative Request-Wide Budget & Deadline Accounting" (Lines 237–243) vs. Section "Non-Functional Requirements" (Line 414)
* **Discrepancy Description & Rationale**:
  1. The sum of stage-level budgets in `RequestBudget.stage_budgets` is $2.5\text{s} + 2.0\text{s} + 1.5\text{s} + 1.0\text{s} + 0.5\text{s} = 7.5\text{s}$, leaving 0.5s unaccounted for against the authoritative 8.0-second request deadline.
  2. In Section 4 (line 241), `verdict_synthesis` is budgeted for 1.0 second. However, line 414 states: *"Minimum Synthesis Window: At least 1.5s remaining time is required before initiating a model synthesis call; requests falling below this threshold degrade cleanly rather than timing out mid-stream."*
  Requiring a 1.5s minimum window to initiate synthesis while explicitly assigning it a 1.0s stage budget creates conflicting boundary conditions for deadline enforcement.

#### Finding 7: Undefined and Unlinked External Standards, Research Acronyms, and ADRs
* **Severity**: 🟡 **Major**
* **Affected Scope**: Lines 21, 59, 129, 211, 217, 375, 387, 393, 474, 489
* **Discrepancy Description & Rationale**:
  The document references internal design artifacts, evaluation benchmarks, and external systems without providing inline definitions or links:
  - **ADR References**: `ADR-001`, `ADR-002`, `ADR-003` are cited as authoritative architectural policies (e.g., lines 129, 217, 375, 387), but there is no link or mention indicating that their full definitions reside in `docs/specification.md`.
  - **Benchmark Acronyms**: `CoBiT` (line 21), `ALCE` (line 211), and `AVeriTeC` (line 489) are introduced as abbreviations without defining their full names or referencing their source literature.
  - **Provider & Model Identifiers**: `Meta Model API` and `muse-spark-1.3` (lines 59, 474) are referenced without explaining their endpoint schema, authentication format, or whether they represent OpenAI-compatible endpoints or vendor-specific interfaces.

#### Finding 8: Vague Gate A Screening Rules & "Soft Lexical Relevance"
* **Severity**: 🟢 **Nit**
* **Affected Scope**: Section 1 Flowchart (Line 139), Section 4 Services (Line 467), and CUJ 1 (Line 73)
* **Discrepancy Description & Rationale**:
  The document states that Gate A performs "deterministic structural screening (soft lexical score, provenance, temporal alignment)" and routes structural failures to `cannot_verify`. However, it does not specify what constitutes a structural failure versus what is tolerated under soft lexical relevance. Without concrete rejection thresholds (e.g., missing required fields vs. lexical match score < threshold), the boundary between Gate A failure and Gate B forwarding is ambiguous.

#### Finding 9: Discrepancy in Export API Route Definition
* **Severity**: 🟢 **Nit**
* **Affected Scope**: Section 8 Target API Contract (Line 364) vs. Section 3 API Routes Implementation Plan (Line 457)
* **Discrepancy Description & Rationale**:
  Section 8 defines the export endpoint as `POST /api/v1/verifications/{id}/export` (line 364), whereas the implementation plan route summary under `backend/app/api/routes/verifications.py` lists it as `POST /export` (line 457). The endpoint signature should be standardized to include the resource identifier.

#### Finding 10: Missing Atomic Claim Linking in Database Schema
* **Severity**: 🟢 **Nit**
* **Affected Scope**: Section 7 ER Diagram (Lines 304–355)
* **Discrepancy Description & Rationale**:
  In the relational schema, `SOURCE` and `REASONING_STATEMENT` contain a `verification_id` foreign key but no link to `ATOMIC_CLAIM`. For compound claims with up to 5 atomic claims (G-1), there is no relational association specifying which evidence sources or reasoning statements substantiate which specific atomic proposition.


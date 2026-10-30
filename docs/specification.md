# Reality Check AI (`jintru`) — Research Foundation & Architectural Decisions Specification

* **Project Name:** jintru (Reality Check AI)
* **Date:** 2026-10-30
* **Status:** Approved Research Specification (Converged with Milestone 1 Architecture)
* **Authoritative Implementation Design:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)
* **Sitemap & Registry:** [`docs/designs/SITEMAP.md`](file:///home/omprakash/Documents/jintru/docs/designs/SITEMAP.md)
* **Predecessors & Context:** [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md)

---

## Deliverable Taxonomy & Verification Boundaries

All specifications, architectural choices, and technological selections within this document are categorized into three distinct evidential classes:

1. **`[Research-backed]`**: Directly supported by peer-reviewed published papers, official vendor documentation, or reproducible empirical evaluations.
2. **`[Recommended design]`**: Pragmatic engineering decisions, patterns, and trade-offs derived from empirical evidence and project constraints.
3. **`[Unverified]`**: Claims regarding very recent releases, library versions (e.g., late October 2026 releases), or project-specific runtime assumptions requiring direct validation before locking.

---

## 1. Research Findings & Architectural Implications

`[Research-backed]`

Recent October 2026 and foundational natural language processing and security research directly refutes the naive paradigm of feeding search snippets into an LLM and asking for an ungrounded verdict. The following research findings define mandatory architectural requirements for `jintru`:

| Paper & Citation | Core Finding | Engineering Design Consequence in `jintru` | Classification |
| :--- | :--- | :--- | :--- |
| **How Robust Are Automated Fact-Checking Systems? A Cross-Benchmark Evaluation**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.1915/) | Evaluated 9 systems across 4 benchmarks (scientific, open-web, climate). Model rankings fluctuate wildly across domains. Substituting gold evidence for retrieved evidence boosts veracity accuracy by **14–22 percentage points**. | **Decouple Retrieval from Verification:** The pipeline must evaluate retrieval recall/precision independently of verdict generation. Never conflate retrieval failure with model reasoning failure. | `[Research-backed]` |
| **Retrieving Facts or Reinforcing Beliefs? Confirmation Bias in RAG**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.44/) | Introduces CoBiT (707 minimally perturbed claim–counterclaim pairs). Proves standard RAG retrieval rankings and LLM generation actively amplify confirmation bias toward the query framing. | **Counterevidence-Aware Retrieval & Fairness:** Formulate dialectical queries to retrieve refuting evidence. Ensure the retrieval process gives the claim a fair chance to be disproved. Benchmark against claim/negation pairs to measure verdict symmetry. | `[Research-backed]` |
| **Advancing Fact-Checking via Argumentative Reasoning**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.1207/) | Introduces MAVEN benchmark and ArgCheck framework. Demonstrates that web evidence is heterogeneous and contradictory; simple link counting fails. Models evidence as arguments with attack relations. | **Source Disagreement & Conflict Modeling:** Do not tally source URLs. Maintain contradictory evidence in the response, attribute stances explicitly, and model source disagreements before synthesizing verdicts. (Formal multi-agent argumentation is deferred). | `[Research-backed]` |
| **Retrieve Few, Verify Many: Segment-Level Evidence Reuse**<br>(Findings of EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.1584/) | Introduces SegmentFact. Reusing evidence across related claims within long-form text assessment reduces redundant retrieval calls. | **Evidence Pooling (Phase 2):** Motivates cross-proposition evidence reuse when decomposing compound claims. In Milestone 1, claims are strictly single atomic assertions, eliminating cross-claim leakage. | `[Research-backed]` |
| **Peerify: Benchmarking Peer-Review Claim Verification**<br>(EMNLP 2026 Industry) [ACL Anthology](https://aclanthology.org/2026.emnlp-industry.169/) | Benchmarks claim decomposition and manuscript verification. Identifies that interpretive, subjective, or ambiguous claims break standard binary/ternary veracity classifiers. | **Explicit Abstention Category (`not_verifiable`):** Distinguish non-verifiable opinions and semantic ambiguities from objective factual claims. Do not force subjective input into true/false verdicts. | `[Research-backed]` |
| **TRACER: Trace-Regularized Training Against Indirect Prompt Injection**<br>(Findings of EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.2124/) | Demonstrates that defenses trained on direct user prompts fail significantly when identical attack instructions appear inside retrieved context. | **Retrieved Context as Untrusted Security Boundary:** Treat all retrieved web content as untrusted input. Validate output behavior against adversarial web snippets rather than assuming prompt delimiters eliminate risk. | `[Research-backed]` |
| **Overcoming the Retrieval Barrier: Real-World Indirect Prompt Injection**<br>(USENIX Security 2026) [USENIX](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan) | Analyzes practical injection payloads engineered to enter search engine results and poison downstream RAG synthesis tasks. | **Poisoning Defense & Quarantine:** Screen retrieved snippets for instruction patterns; quarantine flagged snippets from prompt context; strip model capabilities. | `[Research-backed]` |
| **Do LLMs Know When Evidence is Insufficient?**<br>(ScienceDirect 2026) [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1546221826007526) | Proposes a 5-level evidence sufficiency benchmark (supportive, partial, irrelevant, absent, conflicting). Demonstrates high over-answering rates under partial/absent evidence. | **Two-Stage Sufficiency Gate:** Measure over-answering rate and false abstention rate as primary metrics. Enforce deterministic structural checks before semantic evaluation. Short-circuit on empty retrieval. | `[Research-backed]` |
| **Ev2R: Evaluating Evidence Retrieval in Automated Fact-Checking**<br>(TACL 2026) [ACL Anthology](https://aclanthology.org/2026.tacl-1.25/) | Establishes joint evaluation protocols demonstrating that high verdict accuracy does not imply valid evidence retrieval. Penalizes systems whose verdicts rely on noisy or ungrounded evidence. | **Decoupled Evaluation Protocol:** Implement independent benchmark experiments for (1) fixed-evidence reasoning and (2) live-retrieval quality. | `[Research-backed]` |

---

## 2. Comprehensive Research Baseline Catalogue

`[Research-backed]`

The baseline bibliography is classified by publication type, evaluation setting, and direct engineering application:

### A. Peer-Reviewed Conference & Journal Papers
1. **Claim Verification in the Age of Large Language Models: A Survey (ACL 2026)**
   * *Type:* Survey Paper. *Setting:* Comprehensive review of LLM verification architectures.
   * *Application to `jintru`:* Baseline for system stage decomposition and decoupling retrieval from reasoning.
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.acl-srw.2/)
2. **Evaluating Retrieval Augmented Generation: A Comprehensive Review (2026)**
   * *Type:* Peer-Reviewed Journal (Springer SN Computer Science). *Setting:* 4-axis RAG evaluation framework.
   * *Application to `jintru`:* Defines independent evaluation metrics in `evals/` rather than a single quality score.
   * *Link:* [Springer Nature Link](https://link.springer.com/article/10.1007/s42979-026-05134-x)
3. **ElementCheck: Complexity-Aware Fact-Checking (Findings of EMNLP 2026)**
   * *Type:* Findings Paper. *Setting:* Allocates computational budgets based on claim hardness.
   * *Application to `jintru`:* Informs two-stage retrieval budget allocation (Stage 2 counter-queries dispatched only when necessary).
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.868/)
4. **InSight: Multimodal Claim Verification (EMNLP 2026)**
   * *Type:* Conference Paper. *Setting:* Verification against charts and visual data.
   * *Application to `jintru`:* Out of scope for Milestone 1; reserved for Phase 2 multimodal extensions (NG-5).
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.emnlp-main.606/)
5. **FActScore: Fine-grained Atomic Carving for Factual Precision (EMNLP 2023)**
   * *Type:* Conference Paper. *Setting:* Atomic proposition decomposition.
   * *Application to `jintru`:* Theoretical foundation for atomic proposition carving (deferred to Phase 2; Milestone 1 scopes to single factual claims).
   * *Link:* [ACL Anthology](https://aclanthology.org/2023.emnlp-main.741/)
6. **ALCE: Automatic Language Model Citation Evaluation (EMNLP 2023)**
   * *Type:* Conference Paper. *Setting:* Citation precision and recall metrics for language models.
   * *Application to `jintru`:* Defines benchmark measurement for Tier 3 citation entailment in CI.
   * *Link:* [ACL Anthology](https://aclanthology.org/2023.emnlp-main.398/)
7. **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (ICLR 2024)**
   * *Type:* Conference Paper. *Setting:* Adaptive retrieval and reflection tokens.
   * *Application to `jintru`:* Inspiration for separating retrieval necessity from evidence sufficiency.
   * *Link:* [IBM Research / arXiv](https://research.ibm.com/publications/self-rag-learning-to-retrieve-generate-and-critique-through-self-reflection)
8. **RAGTruth: A Hallucination Benchmark for Retrieval-Augmented Generation (ACL 2024)**
   * *Type:* Conference Paper. *Setting:* Human-annotated corpus of hallucinations in RAG outputs.
   * *Application to `jintru`:* Grounding for Tier 2 normalized exact quote validation to prevent hallucinated citations.
   * *Link:* [ACL Anthology](https://aclanthology.org/2024.acl-long.585/)
9. **LLatrieval: LLM-Verified Retrieval for Verifiable Generation (NAACL 2024)**
   * *Type:* Conference Paper. *Setting:* Iterative retrieval verification.
   * *Application to `jintru`:* Selective follow-up queries when initial evidence is structurally incomplete or one-sided.
   * *Link:* [ACL Anthology](https://aclanthology.org/2024.naacl-long.305/)
10. **Ev2R: Evaluating Evidence Retrieval in Automated Fact-Checking (TACL 2026)**
    * *Type:* Peer-Reviewed Journal Article (TACL). *Authors:* Mubashara Akhtar, Michael Schlichtkrull, Andreas Vlachos.
    * *Setting:* Reference-based and proxy-level evaluation of evidence retrieval.
    * *Application to `jintru`:* Decouples evidence retrieval scoring from final verdict generation.
    * *Link:* [ACL Anthology](https://aclanthology.org/2026.tacl-1.25/)
11. **TRACER: Trace-Regularized Training Against Indirect Prompt Injection (Findings of EMNLP 2026)**
    * *Type:* Findings Paper. *Setting:* Evaluates indirect prompt injection in retrieved contexts.
    * *Application to `jintru`:* Proves prompt delimiters alone do not eliminate injection; motivates ADR-003 defense-in-depth and quarantine rules.
    * *Link:* [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.2124/)
12. **Overcoming the Retrieval Barrier: Real-World Indirect Prompt Injection (USENIX Security 2026)**
    * *Type:* Conference Paper. *Setting:* Empirical analysis of retrieval poisoning attacks.
    * *Application to `jintru`:* Threat model for retrieved web snippet sanitization, capability stripping, and snippet quarantine.
    * *Link:* [USENIX](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan)
13. **Do LLMs Know When Evidence is Insufficient? (ScienceDirect 2026)**
    * *Type:* Journal Article. *Setting:* Evaluates abstention under 5 evidence conditions.
    * *Application to `jintru`:* Core motivation for the two-stage sufficiency gate and abstention metrics.
    * *Link:* [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1546221826007526)

### B. Standard Benchmark Datasets
14. **AVeriTeC: Real-World Claim Verification with Evidence (NeurIPS 2023)**
    * *Type:* Benchmark Dataset. *Setting:* Multi-hop real-world claims and evidence QA.
    * *Application to `jintru`:* Fixture dataset for regression evaluation (`evals/cases.jsonl`).
    * *Link:* [NeurIPS Proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/file/cd86a30526cd1aff61d6f89f107634e4-Paper-Datasets_and_Benchmarks.pdf)
15. **AVeriTeC Shared Task (FEVER Workshop 2024)**
    * *Type:* Shared Task Evaluation. *Setting:* Joint evaluation of verdict and evidence quality.
    * *Application to `jintru`:* Metric penalizing correct verdicts supported by incorrect evidence.
    * *Link:* [ACL Anthology](https://aclanthology.org/2024.fever-1.1/)
16. **QueenVer: Question Enrichment for Claim Verification (FEVER Workshop 2024)**
    * *Type:* Workshop Paper. *Setting:* Multi-perspective question generation.
    * *Application to `jintru`:* Query planning for multi-faceted factual assertions.
    * *Link:* [ACL Anthology](https://aclanthology.org/2024.fever-1.6/)
17. **FEVER: Large-Scale Fact Extraction and VERification (NAACL 2018)**
    * *Type:* Foundational Benchmark Dataset. *Setting:* 3-way classification (`Supported`, `Refuted`, `NotEnoughInfo`).
    * *Application to `jintru`:* Grounding for core verdict taxonomy.
    * *Link:* [ACL Anthology](https://aclanthology.org/N18-1074/)
18. **SciFact: Scientific Claim Verification (EMNLP 2020)**
    * *Type:* Domain Benchmark Dataset. *Setting:* Scientific claims with annotated abstract rationales.
    * *Application to `jintru`:* Specialized test suite for scientific and health claims.
    * *Link:* [ACL Anthology](https://aclanthology.org/2020.emnlp-main.609/)

### C. Empirical Theses & Preprints
19. **Evaluating Mitigation Strategies Against Indirect Prompt Injection (2026)**
    * *Type:* Academic Thesis (eScholarship). *Setting:* Comparative evaluation of sanitization, delimiters, and tool restrictions.
    * *Application to `jintru`:* Highlights trade-offs between prompt sanitization and utility loss. Results replicated in offline tests.
    * *Link:* [eScholarship](https://escholarship.org/uc/item/8zq0952f)

### D. Security & Accessibility Standards
20. **OWASP Top 10 (2025 Standard for Web Applications)**
    * *Type:* Security Baseline. *Focus:* Broken access control, security misconfigurations, cryptographic failures.
21. **OWASP API Security Top 10 (2023 Standard)**
    * *Type:* Security Baseline. *Focus:* Broken object-level authorization, rate limiting, SSRF, resource consumption.
22. **OWASP Server-Side Request Forgery Prevention Cheat Sheet**
    * *Type:* Security Guidance. *Focus:* Controlling redirects, DNS rebinding mitigations, IPv4-mapped IPv6, and destination address validation.
23. **W3C Web Content Accessibility Guidelines (WCAG 2.2 AA)**
    * *Type:* Accessibility Standard. *Focus:* Color contrast pairs, visible focus indicators, screen-reader announcements, keyboard navigation.

---

## 3. Architecture Decision Records (ADRs)

`[Recommended design]`

### ADR-001: Bounded Dialectical Retrieval & Latency Budget Policy
* **Context:** Unconstrained retrieval fan-out exhausts quotas, violates latency targets, and risks runaway provider retries. Furthermore, multiple URLs repeating identical wire copy creates an illusion of consensus.
* **Decision (Milestone 1 Baseline):**
  * **Input Bound:** Single factual assertion (min 5, max 500 characters). Inputs exceeding this ceiling or containing multiple propositions are rejected with HTTP 422. (Compound claim decomposition is deferred to Phase 2).
  * **Retrieval Fairness:** Query planning must give the claim a fair opportunity to be refuted. Track query intent (`support_seeking` vs. `counterevidence_seeking`).
  * **Heuristic Source Grouping:** Group snippets sharing the same registered domain or wire service attribution into a shared `source_family_id`. Repeated reporting within the same family is never treated as independent corroboration.
  * **Sequential Two-Stage Execution:**
    1. *Stage 1 (Initial Search):* Exactly 1 focused query against Brave Search API (`/res/v1/web/search`) retrieving top 5 snippets.
    2. *Stage 2 (Targeted Counterevidence):* At most 1 counterevidence query, triggered *only* when Stage 1 evidence is one-sided or disputed, and remaining request time is ≥ 3.5s.
  * **Authoritative Request Deadline (8.0 Seconds Target):**
    * A single deadline is created at request entry: `deadline = now() + 8.0s`.
    * Stage-level time budgeting: Pre-Classification & Gate A (max 0.2s), Stage 1 Search (max 2.5s), Stage 2 Counter-Search (max 2.0s), Single Synthesis Call (max 3.0s), Storage & Safety Buffer (0.3s). Sum = 8.0s.
    * Minimum remaining-time threshold: At least 1.5s remaining is required before initiating a model synthesis call. If remaining time is < 1.5s, return HTTP 504 Gateway Timeout or a structured partial response with limitations.
* **Consequences:** Prevents budget overruns; guarantees strict 8.0-second wall-clock termination; eliminates HTTP 429 rate limit spikes.

### ADR-002: Evidence Sufficiency Gate, Pre-Retrieval Classification & 5-Way Verdict Taxonomy
* **Context:** Purely deterministic rules cannot assess semantic entailment on paraphrased claims, while purely model-driven checks suffer from high over-answering on absent evidence. Claims also frequently mix temporal periods or future forecasts.
* **Decision:**
  * **Internal States:** `eligible`, `needs_more_evidence`, `insufficient_evidence`, `not_verifiable`.
  * **Public API Verdicts (5-Way):** `supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`.
  * **Gate A Pre-Retrieval Deterministic Screening:**
    * *Subjective Value Judgments:* Detects normative markers (`should`, `ought`, `best`, `worst`). Routes immediately to public verdict `not_verifiable` (0 search calls, 0 LLM calls).
    * *Future Predictions:* Detects prospective markers (`will`, `by 2028`, `projected to`). Routes immediately to public verdict `not_verifiable` with explanation that future events cannot be empirically verified prior to occurrence (0 search calls, 0 LLM calls).
    * *Empty Results Short-Circuit:* If Stage 1 search yields zero relevant snippets, short-circuits immediately to `insufficient_evidence` with 0 external LLM calls.
  * **Single Structured Synthesis LLM Round-Trip:**
    * When usable evidence exists, dispatches a single structured prompt to the Meta Model API with schema `VerificationSynthesisPayload`.
  * **Application-Level Deterministic Verdict Acceptance:**
    * `supported` requires: (1) model proposed `supported`, (2) at least two distinct `source_family_id` clusters with `stance="supports"`, (3) 0 unrefuted `refutes` stances, and (4) 100% of cited quotes pass Tier 2 normalized substring matching. If evidence has only 1 domain or fails Tier 2, application code downgrades the verdict to `insufficient_evidence`.
    * `contradicted` requires: at least 1 authoritative or 2 distinct source families with `stance="refutes"`.
    * `mixed` requires: genuine contradiction between credible sources with neither side decisively refuting the other.
* **Consequences:** Eliminates external LLM calls on garbage or speculative inputs; prevents hallucinated consensus; provides deterministic bounds on model-generated verdicts.

### ADR-003: Snippet-First Network Security & Multi-Layer Prompt Injection Defense
* **Context:** Fetching arbitrary web pages risks SSRF attacks via DNS rebinding, IPv6 tunnels, and malicious redirects. Furthermore, retrieved content can contain adversarial instructions designed to manipulate model verdicts.
* **Decision:**
  * **Snippet-First Retrieval:** Evidence ingestion is restricted strictly to search provider snippets (`Brave Search API`) and cleaned text (`Brave LLM Context endpoint`). **Raw third-party web page crawling is completely excluded.**
  * **SSRF Elimination:** Because the backend communicates solely with pre-configured trusted APIs (`api.search.brave.com`, Meta Model API), the SSRF attack surface is eliminated at the architectural level.
  * **Indirect Prompt Injection Mitigations:**
    * System instructions and untrusted web excerpts are separated.
    * Excerpts are stripped of control characters, HTML comments, and zero-width spaces.
    * Heuristic Injection Scanner: Snippets containing instruction patterns (`system prompt:`, `override verdict`, `ignore previous instructions`) are **quarantined and excluded** from the synthesis prompt payload.
    * Principle of Least Privilege: The verification model has zero tools, zero network access, and zero database permissions.
  * **Three-Tier Citation Validation:**
    * Tier 1 (Structural ID Existence): Deterministic check asserting every cited `source_id` exists in the active evidence list.
    * Tier 2 (Excerpt Provenance): Deterministic normalized substring check (`html.unescape()`, whitespace collapse, smart quote normalization) asserting the quoted excerpt exists within source text.
    * Tier 3 (Semantic Entailment): Evaluated in production via model relationship tags and tested in CI via the ALCE benchmark harness; application code does not claim to prove entailment deterministically.
* **Consequences:** Eliminates SSRF risks; neutralizes injection attacks via quarantine; ensures all citations correspond to actual retrieved source text.

### ADR-004: Latency Objectives & Synchronous Deadline Accounting
* **Context:** External web search and multi-step model inference across public networks cannot reliably guarantee a 3.0s P95 latency.
* **Decision:**
  * **Fast-Path Test Profile:** P95 ≤ 3.0s applies strictly to cached verifications, mock provider fixtures, and pre-retrieval short-circuit paths.
  * **Live-Search SLA:** Live external search and model inference are measured independently. Total request budget is capped at an 8.0s hard cutoff with a 0.3s safety buffer.
* **Consequences:** Eliminates dishonest performance guarantees; establishes transparent operational metrics.

### ADR-005: Decoupled Independent Factuality & Retrieval Evaluation Protocol
* **Context:** Single accuracy metrics reward "accidental correctness" where a model guesses the right verdict despite retrieved evidence being absent, irrelevant, or conflicting (Ev2R findings).
* **Decision:** Establish two separate evaluation experiments in `evals/`:
  1. **Fixed-Evidence Evaluation:** Supply known ground-truth evidence to the model to isolate and evaluate reasoning, verdict classification, explanation quality, and citation entailment precision.
  2. **Live-Retrieval Evaluation:** Allow the complete pipeline to search the live web and evaluate whether it discovers necessary supporting evidence and known refuting sources.
  * **Quantitative CI Pass Thresholds:**
    * Citation Entailment Precision: ≥ 90%
    * False-Support Rate under Absent Evidence: ≤ 5%
    * Counterevidence Recall: ≥ 80%
* **Consequences:** Prevents metric gaming; isolates model reasoning failures from retrieval failures.

---

## 4. Audit & Convergence Record

`[Recommended design]` & `[Unverified]`

The architectural specification underwent rigorous evaluation via the EGM Goldfish Review Protocol (`consolidated_review_report.md`), resulting in the following convergence from the initial proposal to the approved Milestone 1 vertical slice:

| Component | Initial Proposal | Audited Defect | Converged Milestone 1 Baseline |
| :--- | :--- | :--- | :--- |
| **Claim Scope** | Up to 5 atomic claims decomposed via NLP | Unbudgeted LLM latency, combinatorial query fan-out | Single atomic factual claim (≤ 500 chars). Proposition carving deferred to Phase 2. |
| **Model Invocations** | 2 sequential LLM calls (Gate B 1.5s + Synthesis 1.0s) | Breaches 8.0s synchronous SLA over public networks | 1 structured synthesis LLM call (~2.5s window). Short-circuit on empty retrieval with 0 calls. |
| **Web Ingestion** | Raw HTML crawling with custom socket IP-pinning transport | Fragile TLS cert validation, high SSRF exposure | Snippet-first ingestion via Brave Search API & LLM Context endpoint. Zero raw crawling. |
| **Source Deduplication** | 64-bit MinHash / SimHash text shingling | Algorithmic overkill for ≤ 10 snippets | Heuristic domain & wire service attribution grouping. |
| **Persistence** | 4-table relational database with async SQLAlchemy & Alembic | MissingGreenlet async issues, cascade delete bugs, migration overhead | Single flat `verifications` SQLite table with JSON columns in WAL mode with 5s busy timeout. |
| **API Endpoints** | Verification, PDF export (`POST /export`), client settings (`/settings`) | YAGNI scope creep for local single-user research workbench | Pruned `/export` and `/settings`. Streamlined to core `/verifications` and `/health`. |

---

## 5. Cross-Reference to Master Implementation Design

This research specification establishes the scientific foundation and architectural policies for `jintru`. 

For the complete, implementation-ready design document containing detailed component specifications, Pydantic schemas, database wrapper code, frontend architecture, and the 8-phase zero-decision build plan, consult:

* **Authoritative Master Design Document:** [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md)
* **Master Sitemap:** [`docs/designs/SITEMAP.md`](file:///home/omprakash/Documents/jintru/docs/designs/SITEMAP.md)

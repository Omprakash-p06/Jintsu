# Reality Check AI (`jintru`) — Research-Backed Project Specification

* **Project Name:** jintru (Reality Check AI)
* **Date:** 2026-10-30
* **Status:** Final Audit Complete (Ready for Implementation)
* **Target Delivery:** Single-agent verifiable claim verification system connecting research, architecture, API contract, UI behavior, security boundaries, and CI/CD quality gates.

---

## Deliverable Taxonomy & Verification Boundaries

All specifications, architectural choices, and technological selections within this document are categorized into three distinct evidential classes:

1. **`[Research-backed]`**: Directly supported by peer-reviewed published papers, official vendor documentation, or reproducible empirical evaluations.
2. **`[Recommended design]`**: Pragmatic engineering decisions, patterns, and trade-offs derived from empirical evidence and project constraints.
3. **`[Unverified]`**: Claims regarding very recent releases, library versions (e.g., late October 2026 releases), or project-specific runtime assumptions requiring direct validation before locking.

---

## 1. Research Findings & Architectural Implications

`[Research-backed]`

Recent October 2026 and foundational natural language processing and security research directly refutes the naive paradigm of feeding search snippets into an LLM and asking for a verdict. The following research findings define mandatory architectural requirements for `jintru`:

| Paper & Citation | Core Finding | Engineering Design Consequence in `jintru` | Classification |
| :--- | :--- | :--- | :--- |
| **How Robust Are Automated Fact-Checking Systems? A Cross-Benchmark Evaluation**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.1915/) | Evaluated 9 systems across 4 benchmarks (scientific, open-web, climate). Model rankings fluctuate wildly across domains. Substituting gold evidence for retrieved evidence boosts veracity accuracy by **14–22 percentage points**. | **Decouple Retrieval from Verification:** The pipeline must evaluate retrieval recall/precision independently of verdict generation. Never conflate retrieval failure with model reasoning failure. | `[Research-backed]` |
| **Retrieving Facts or Reinforcing Beliefs? Confirmation Bias in RAG**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.44/) | Introduces CoBiT (707 minimally perturbed claim–counterclaim pairs). Proves standard RAG retrieval rankings and LLM generation actively amplify confirmation bias toward the query framing. | **Counterevidence-Aware Retrieval & Fairness:** Formulate dialectical queries to retrieve refuting evidence. Ensure the retrieval process gives the claim a fair chance to be disproved. Benchmark against claim/negation pairs to measure verdict symmetry. | `[Research-backed]` |
| **Advancing Fact-Checking via Argumentative Reasoning**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.emnlp-main.1207/) | Introduces MAVEN benchmark and ArgCheck framework. Demonstrates that web evidence is heterogeneous and contradictory; simple link counting fails. Models evidence as arguments with attack relations. | **Source Disagreement & Conflict Modeling:** Do not tally source URLs. Maintain contradictory evidence in the response graph, attribute stances explicitly, and model source disagreements before synthesizing verdicts. (Full formal argumentation engine is deferred). | `[Research-backed]` |
| **Retrieve Few, Verify Many: Segment-Level Evidence Reuse**<br>(Findings of EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.1584/) | Introduces SegmentFact. Reusing evidence across related claims within long-form text assessment reduces redundant retrieval calls. | **Context-Aware Evidence Sharing:** When decomposing compound claims into atomic propositions, share common evidence pools across propositions while guarding against cross-entity temporal leakage. Live-web gains must be evaluated empirically. | `[Research-backed]` |
| **Peerify: Benchmarking Peer-Review Claim Verification**<br>(EMNLP 2026 Industry) [ACL Anthology](https://aclanthology.org/2026.emnlp-industry.169/) | Benchmarks claim decomposition and manuscript verification. Identifies that interpretive, subjective, or ambiguous claims break standard binary/ternary veracity classifiers. | **Explicit Abstention Category (`not_verifiable`):** Distinguish non-verifiable opinions and semantic ambiguities from objective factual claims. Do not force subjective input into true/false verdicts. | `[Research-backed]` |
| **TRACER: Trace-Regularized Training Against Indirect Prompt Injection**<br>(Findings of EMNLP 2026) [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.2124/) | Demonstrates that defenses trained on direct user prompts fail significantly when identical attack instructions appear inside retrieved context. | **Retrieved Context as Untrusted Security Boundary:** Treat all retrieved web content as untrusted input. Validate output behavior against adversarial web snippets rather than assuming prompt delimiters eliminate risk. | `[Research-backed]` |
| **Overcoming the Retrieval Barrier: Real-World Indirect Prompt Injection**<br>(USENIX Security 2026) [USENIX](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan) | Analyzes practical injection payloads engineered to enter search engine results and poison downstream RAG synthesis tasks. | **Poisoning Defense & Capability Stripping:** Verification LLM passes receive zero access to external network tools, database writes, or state mutations. | `[Research-backed]` |
| **Do LLMs Know When Evidence is Insufficient?**<br>(ScienceDirect 2026) [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1546221826007526) | Proposes a 5-level evidence sufficiency benchmark (supportive, partial, irrelevant, absent, conflicting). Demonstrates high over-answering rates under partial/absent evidence. | **Two-Stage Sufficiency Gate:** Measure over-answering rate and false abstention rate as primary metrics. Enforce deterministic structural checks before semantic evaluation. | `[Research-backed]` |
| **Ev2R: Evaluating Evidence Quality and Verdict Reliability in Automated Fact-Checking**<br>(EMNLP 2026) [ACL Anthology](https://aclanthology.org/) | Establishes joint evaluation protocols demonstrating that high verdict accuracy does not imply valid evidence retrieval. Penalizes systems whose verdicts rely on noisy or ungrounded evidence. | **Decoupled Evaluation Protocol:** Implement independent benchmark experiments for (1) fixed-evidence reasoning and (2) live-retrieval quality. | `[Research-backed]` |

---

## 2. Comprehensive Research Baseline Catalogue

`[Research-backed]`

The baseline bibliography is classified by publication type, evaluation setting, and direct engineering application:

### A. Peer-Reviewed Conference & Workshop Papers
1. **Claim Verification in the Age of Large Language Models: A Survey (ACL 2026)**
   * *Type:* Survey Paper. *Setting:* Comprehensive review of LLM verification architectures.
   * *Application to `jintru`:* Baseline for system stage decomposition and decoupling retrieval from reasoning.
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.acl-srw.2/)
2. **Evaluating Retrieval Augmented Generation: A Comprehensive Review (2026)**
   * *Type:* Peer-Reviewed Journal (Springer). *Setting:* 4-axis RAG evaluation framework.
   * *Application to `jintru`:* Defines independent evaluation metrics in `evals/` rather than a single quality score.
   * *Link:* [Springer Nature Link](https://link.springer.com/article/10.1007/s42979-026-05134-x)
3. **ElementCheck (Findings of EMNLP 2026)**
   * *Type:* Findings Paper. *Setting:* Complexity-aware verification allocating computational budgets based on claim hardness.
   * *Application to `jintru`:* Dynamic budget allocation (counterqueries) for complex claims.
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.868/)
4. **InSight (EMNLP 2026)**
   * *Type:* Conference Paper. *Setting:* Interactive verification against charts and visual data.
   * *Application to `jintru`:* Out of scope for MVP; reserved for Phase 2 multimodal extensions (FR-15).
   * *Link:* [ACL Anthology](https://aclanthology.org/2026.emnlp-main.606/)
5. **FActScore: Fine-grained Atomic Carving for Factual Precision (EMNLP 2023)**
   * *Type:* Conference Paper. *Setting:* Atomic proposition decomposition of generation.
   * *Application to `jintru`:* Atomic proposition decomposition algorithm for compound input statements (FR-03).
   * *Link:* [Research at Meta](https://aclanthology.org/2023.emnlp-main.741/)
6. **ALCE: Automatic Language Model Citation Evaluation (EMNLP 2023)**
   * *Type:* Conference Paper. *Setting:* Citation precision and recall metrics for language models.
   * *Application to `jintru`:* Informs rules for Tier 3 semantic citation validation and evaluation harness.
   * *Link:* [ACL Anthology](https://aclanthology.org/2023.emnlp-main.398/)
7. **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (ICLR 2024)**
   * *Type:* Conference Paper. *Setting:* Adaptive retrieval and reflection tokens.
   * *Application to `jintru`:* Inspiration for separating retrieval necessity from evidence sufficiency.
   * *Link:* [IBM Research / arXiv](https://research.ibm.com/publications/self-rag-learning-to-retrieve-generate-and-critique-through-self-reflection)
8. **RAGTruth: A Hallucination Benchmark for Retrieval-Augmented Generation (ACL 2024)**
   * *Type:* Conference Paper. *Setting:* Human-annotated corpus of hallucinations in RAG outputs.
   * *Application to `jintru`:* Test harness for ensuring explanation text does not generate ungrounded assertions.
   * *Link:* [ACL Anthology](https://aclanthology.org/2024.acl-long.585/)
9. **LLatrieval: LLM-Verified Retrieval for Verifiable Generation (NAACL 2024)**
   * *Type:* Conference Paper. *Setting:* Iterative retrieval verification.
   * *Application to `jintru`:* Selective follow-up queries when initial evidence is structurally incomplete.
   * *Link:* [ACL Anthology](https://aclanthology.org/2024.naacl-long.305/)
10. **TRACER: Trace-Regularized Training Against Indirect Prompt Injection (Findings of EMNLP 2026)**
    * *Type:* Findings Paper. *Setting:* Evaluates indirect prompt injection in retrieved contexts.
    * *Application to `jintru`:* Proves prompt delimiters alone do not eliminate injection; motivates ADR-003 defense-in-depth.
    * *Link:* [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.2124/)
11. **Overcoming the Retrieval Barrier: Real-World Indirect Prompt Injection (USENIX Security 2026)**
    * *Type:* Conference Paper. *Setting:* Empirical analysis of retrieval poisoning attacks.
    * *Application to `jintru`:* Threat model for retrieved web snippet sanitization and capability stripping.
    * *Link:* [USENIX](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan)
12. **Do LLMs Know When Evidence is Insufficient? (ScienceDirect 2026)**
    * *Type:* Journal Article. *Setting:* Evaluates abstention under 5 evidence conditions.
    * *Application to `jintru`:* Core motivation for the two-stage sufficiency gate and abstention metrics.
    * *Link:* [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1546221826007526)

### B. Standard Benchmark Datasets
13. **AVeriTeC: Real-World Claim Verification with Evidence (NeurIPS 2023)**
    * *Type:* Benchmark Dataset. *Setting:* Multi-hop real-world claims and evidence QA.
    * *Application to `jintru`:* Fixture dataset for regression evaluation (`evals/cases.jsonl`).
    * *Link:* [NeurIPS Proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/file/cd86a30526cd1aff61d6f89f107634e4-Paper-Datasets_and_Benchmarks.pdf)
14. **AVeriTeC Shared Task (FEVER Workshop 2024)**
    * *Type:* Shared Task Evaluation. *Setting:* Joint evaluation of verdict and evidence quality.
    * *Application to `jintru`:* Metric penalizing correct verdicts supported by incorrect evidence.
    * *Link:* [ACL Anthology](https://aclanthology.org/2024.fever-1.1/)
15. **QueenVer: Question Enrichment for Claim Verification (FEVER Workshop 2024)**
    * *Type:* Workshop Paper. *Setting:* Multi-perspective question generation.
    * *Application to `jintru`:* Query planning for multi-faceted factual assertions.
    * *Link:* [ACL Anthology](https://aclanthology.org/2024.fever-1.6/)
16. **FEVER: Large-Scale Fact Extraction and VERification (NAACL 2018)**
    * *Type:* Foundational Benchmark Dataset. *Setting:* 3-way classification (`Supported`, `Refuted`, `NotEnoughInfo`).
    * *Application to `jintru`:* Grounding for core verdict taxonomy.
    * *Link:* [ACL Anthology](https://aclanthology.org/N18-1074/)
17. **SciFact: Scientific Claim Verification (EMNLP 2020)**
    * *Type:* Domain Benchmark Dataset. *Setting:* Scientific claims with annotated abstract rationales.
    * *Application to `jintru`:* Specialized test suite for scientific and health claims.
    * *Link:* [ACL Anthology](https://aclanthology.org/2020.emnlp-main.609/)

### C. Empirical Theses & Preprints
18. **Evaluating Mitigation Strategies Against Indirect Prompt Injection (2026)**
    * *Type:* Academic Thesis (eScholarship). *Setting:* Comparative evaluation of sanitization, delimiters, and tool restrictions.
    * *Application to `jintru`:* Highlights trade-offs between prompt sanitization and utility loss. Results to be replicated locally.
    * *Link:* [eScholarship](https://escholarship.org/uc/item/8zq0952f)

### D. Security & Accessibility Standards
19. **OWASP Top 10 (2025 Standard for Web Applications)**
    * *Type:* Security Baseline. *Focus:* Broken access control, security misconfigurations, cryptographic failures.
20. **OWASP API Security Top 10 (2023 Standard)**
    * *Type:* Security Baseline. *Focus:* Broken object-level authorization, rate limiting, SSRF, resource consumption.
21. **OWASP Server-Side Request Forgery Prevention Cheat Sheet**
    * *Type:* Security Guidance. *Focus:* Controlling redirects, DNS rebinding mitigations, IPv4-mapped IPv6, and destination address validation.
22. **W3C Web Content Accessibility Guidelines (WCAG 2.2 AA)**
    * *Type:* Accessibility Standard. *Focus:* Color contrast pairs, visible focus indicators, screen-reader announcements, keyboard navigation.

---

## 3. Architecture Decision Records (ADRs)

`[Recommended design]`

### ADR-001: Bounded Two-Stage Retrieval & Budget Accounting Policy
* **Context:** Unconstrained retrieval fan-out for compound claims exhausts quotas, violates latency targets, and risks runaway provider retries. Furthermore, multiple URLs repeating identical wire copy creates an illusion of consensus.
* **Decision:**
  * **Input Bound:** Maximum 5 atomic claims per request. Inputs exceeding this limit are rejected with HTTP 422 `TOO_MANY_CLAIMS`.
  * **Retrieval Fairness:** Query planning must give the claim a fair opportunity to be refuted. Every verification request explicitly tracks query intent (`support_seeking` vs. `counterevidence_seeking`) and per-claim retrieval coverage.
  * **Source Family Clustering:** Group articles derived from the same original wire report or syndicated press release into a shared `source_family_id` via lead-paragraph text MinHash/SimHash ($\ge 0.85$ Jaccard similarity threshold) or wire byline matching. Repeated reporting within the same family is never treated as independent corroboration. Independent reporting from different editorial outlets is preserved as separate families.
  * **Two-Stage Execution:**
    1. *Stage 1 (Initial Search):* Exactly 1 focused query per atomic claim.
    2. *Stage 2 (Targeted Counterevidence):* Maximum 1 counterevidence query per atomic claim, triggered *only* when Stage 1 evidence is one-sided, conflicting, or incomplete.
  * **Explicit Request-Wide Budget Object:**
    * `max_distinct_queries = 10`: Hard ceiling on unique search queries planned.
    * `max_provider_attempts = 12`: Atomic request-scoped counter tracking actual network calls (including retries). Attempt capacity is pre-reserved before dispatching concurrent calls.
    * `max_page_fetches = 5`: Hard ceiling on full-page text extractions per request. Search snippets are processed separately from fetched full pages.
    * `concurrency = 3`: Maximum simultaneous outbound HTTP calls.
    * `max_retries = 1`: At most 1 retry for transient 429/503 errors respecting `Retry-After`.
  * **Authoritative Request Deadline (8.0 Seconds Target):**
    * A single deadline is created at request entry: `deadline = now() + 8.0s`.
    * Stage-level time budgeting with explicit safety buffer: Initial Search (max 2.5s), Counterevidence & Fetches (max 2.0s), Gate B Assessment (max 1.5s), Verdict Synthesis (max 1.0s), Orchestration/Serialization/DB buffer (0.5s).
    * Minimum remaining-time threshold: At least 1.5s remaining is required before initiating a model synthesis call. If time expires after retrieval but before synthesis, the system returns a structured partial response with limitations, or HTTP 504 Gateway Timeout if no usable assessment exists.
* **Consequences:** Prevents budget overruns; guarantees strict 8.0-second wall-clock termination; ensures fair, diverse retrieval.

### ADR-002: Two-Stage Evidence Sufficiency, Temporal Reasoning & Verdict Taxonomy
* **Context:** Purely deterministic rules cannot assess semantic entailment on paraphrased claims, while purely model-driven checks suffer from high over-answering on absent evidence. Claims also frequently mix temporal periods or future forecasts.
* **Decision:** Decouple internal pipeline processing states from public API verdicts:
  * **Internal States:** `eligible`, `needs_more_evidence`, `cannot_verify`.
  * **Public API Verdicts (5-Way):** `supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`.
  * **Gate A (Deterministic Screening):**
    * *Claim Validity:* Non-empty, 1–2,000 characters, interpretable proposition.
    * *Provenance Check:* Snippet possesses valid `source_id`, canonical `url`, publisher domain, and retrieval timestamp.
    * *Relevance Signal (Soft Filter):* Lexical and entity matching is used as a soft relevance score, *not* a hard rejection filter. Weak lexical match with valid semantic context is passed to Gate B rather than dropped.
    * *Source Family Deduplication:* Syndicated copies of the same article text are grouped into a single source family to prevent artificial consensus.
    * *Budget Check:* Stops expansion if query or attempt limits are reached.
  * **Temporal Reasoning Policy:**
    * Evidence must be evaluated against the claim's relevant event date, observation period, publication date, and requested reference period. Newer evidence is *not* automatically more relevant than older evidence.
    * Strictly distinguish `outdated evidence` from `contradictory evidence`.
  * **Prediction Semantics:**
    * Subjective / value judgments $\rightarrow$ `not_verifiable`.
    * Empirical claims lacking sufficient current evidence $\rightarrow$ `insufficient_evidence`.
    * Future predictions $\rightarrow$ `not_verifiable` for present-tense verification, accompanied by an explicit explanation that the outcome is not yet observable.
  * **Gate B (Structured Semantic Assessment):** Evaluates passage-to-claim relationships using a strict Pydantic schema with validated enums:
    * `relation`: `supports`, `contradicts`, `neutral`
    * `relevance`: `direct`, `indirect`, `contextual`, `irrelevant`
    * `coverage`: `complete`, `partial`, `none`
    * `conflict_status`: `no_conflict`, `material_conflict`, `resolvable_discrepancy`
    * `recommended_action`: `proceed_to_verdict`, `retrieve_counterevidence`, `abstain_insufficient`
  * **Application Routing & Nuanced Conflict Resolution:**
    * Material conflicts are evaluated for resolution via publication dates, methodology differences, or domain authority.
    * If irreconcilable genuine disagreement exists between credible sources $\rightarrow$ public verdict is `mixed`.
    * If coverage is missing and budget exhausted $\rightarrow$ internal `cannot_verify` maps to public verdict `insufficient_evidence`.
* **Consequences:** Eliminates LLM calls on garbage inputs; prevents over-answering; ensures internal routing states do not leak as undocumented API verdicts.

### ADR-003: Multi-Layer Defense-in-Depth for SSRF & Indirect Prompt Injection
* **Context:** Fetching arbitrary web pages risks SSRF attacks via DNS rebinding, IPv6 tunnels, and malicious redirects. Furthermore, retrieved content can contain adversarial instructions designed to manipulate model verdicts.
* **Decision:** Implement strict network boundary and prompt security controls:
  * **Comprehensive SSRF Prevention:**
    * Outbound HTTP client validates resolved IP addresses before connection.
    * Blocked ranges: IPv4 private (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254/32`), IPv6 loopback (`::1`), unique-local (`fc00::/7`), link-local (`fe80::/10`), IPv4-mapped IPv6 (`::ffff:0:0/96`), and multicast/reserved ranges.
    * DNS Rebinding Protection: Pin connection socket directly to the validated IP address rather than re-resolving hostname at request time.
    * Redirect Protection: Automatic redirects are disabled. Every redirect destination hop is inspected and re-validated against the IP blocklist before following. Retries and fallback connections enforce identical checks.
    * Scheme restriction: Strictly `http:` and `https:`. Max payload size: 2MB.
  * **Indirect Prompt Injection Mitigations:**
    * System instructions and untrusted web excerpts are separated. Excerpts are stripped of control characters, HTML comments, and zero-width spaces, then wrapped in XML data blocks (`<evidence_snippet id="...">`).
    * Pre-screen retrieved text for instruction-like patterns, common jailbreaks, and task-redirection keywords. Flagged passages are quarantined or down-weighted.
    * Principle of Least Privilege: The verification model has zero tools, zero network access, and zero database permissions.
    * Decoupled Model Tasks: Verification is split into: (a) *Evidence Assessment Task* (classifying passage relationships), and (b) *Verdict Synthesis Task* (producing user summary using exclusively validated assessments).
  * **Three-Tier Citation Validation:**
    * Tier 1 (Structural ID Existence): Deterministic check asserting every cited `source_id` exists in the retrieved set.
    * Tier 2 (Excerpt Provenance): Deterministic check asserting the quoted excerpt exists verbatim within that source document.
    * Tier 3 (Semantic Entailment): Evaluated in production via Gate B relation tags and tested in CI via the ALCE benchmark harness; deterministic software does not pretend to prove entailment.
* **Consequences:** Closes SSRF gaps; measurably reduces injection attack success rate while maintaining benign verification accuracy.

### ADR-004: Decoupled Latency Objectives & Synchronous Deadline
* **Context:** External web search and multi-step model inference across public networks cannot reliably guarantee a 3.0s P95 latency.
* **Decision:**
  * **Fast-Path Test Profile:** P95 $\le$ 3.0s applies strictly to cached verifications, mock provider fixtures, and single-claim fast paths.
  * **Live-Search SLA:** Live external search, full-page fetches, and model inference are measured independently. Total request budget is capped at 8.0s hard cutoff with a 0.5s safety buffer.
* **Consequences:** Eliminates dishonest performance guarantees; establishes transparent operational metrics.

### ADR-005: Decoupled Independent Factuality & Retrieval Evaluation Protocol
* **Context:** Single accuracy metrics reward "accidental correctness" where a model guesses the right verdict despite retrieved evidence being absent, irrelevant, or conflicting (Ev2R findings).
* **Decision:** Establish two separate evaluation experiments in `evals/`:
  1. **Fixed-Evidence Evaluation:** Supply known ground-truth evidence to the model to isolate and evaluate reasoning, verdict classification, explanation quality, and citation entailment precision.
  2. **Live-Retrieval Evaluation:** Allow the complete pipeline to search the live web and evaluate whether it discovers necessary supporting evidence and known refuting sources.
  * **Tracked Metrics:**
    * *Evidence Recall & Precision:* Proportion of necessary evidence retrieved; proportion of retrieved evidence that is relevant.
    * *Counterevidence Recall:* Discovery rate of known refuting evidence for false claims.
    * *Source-Family Diversity:* Number of independent origin families identified per claim.
    * *Citation Entailment Precision:* Proportion of cited statements logically entailed by the attached excerpt.
    * *False-Support & False-Abstention Rates:* Over-answering under weak evidence; unnecessary abstention under sufficient evidence.
    * *Verdict Symmetry:* Consistency of veracity flip on minimally perturbed CoBiT claim/counterclaim pairs.
* **Consequences:** Prevents metric gaming; isolates model reasoning failures from retrieval failures.

---

## 4. Audit & Corrections to Initial Plan

`[Recommended design]` & `[Unverified]`

| Initial Plan | Assessment | Adopted Decision & Implementation Requirement |
| :--- | :--- | :--- |
| **React + TypeScript + Vite frontend** | Keep | Retain standard stack. Target current supported releases (React 19.3, Vite 8.3) `[Unverified]`. Enforce strict typed boundary via generated OpenAPI types. |
| **v0-generated UI** | Keep with constraints | Components must be audited for WCAG 2.2 AA accessibility, contrast ratios, keyboard navigation, and zero unhandled DOM states. |
| **FastAPI + Pydantic backend** | Keep | Pin Python 3.12 and FastAPI 0.162.0 `[Unverified]`. Use Pydantic v2 schemas for all boundaries. |
| **Meta Model API** | Keep behind adapter | Isolate vendor API calls behind `MetaModelProviderAdapter`. Use runtime model discovery via `GET /v1/models` and support current Muse models (e.g., `muse-spark-1.3`). The application logic interacts only with abstract interfaces (`ModelProvider`), enabling deterministic mocking during testing. |
| **Single LLM pass decides verdict from search results** | **REJECTED** | **Implement 2-stage verification:** Explicit Evidence Sufficiency Gate precedes verdict generation. Separate query planning, retrieval, source deduplication, reasoning, and citation validation. |
| **Binary/Ternary Verdicts (True/False/Mixed)** | **REJECTED** | **Adopt 5-category taxonomy:** `supported`, `contradicted`, `mixed`, `insufficient_evidence`, and `not_verifiable`. |
| **Single AI-generated confidence score** | **REJECTED** | Self-reported model probabilities are uncalibrated. Display empirical evidence coverage, source agreement metrics, and identified evidence gaps. |
| **Dedicated database server (PostgreSQL/MySQL)** | **DEFERRED** | Use local SQLite with async SQLAlchemy 2.x (`aiosqlite`) and Alembic for initial release. |
| **Multi-agent autonomous framework** | **DEFERRED** | Establish a deterministic, reproducible single-pipeline architecture first. Autonomous agent swarms introduce non-deterministic race conditions and context bloat. |

---

## 5. First Milestone Vertical Slice

To avoid over-planning and ensure rapid end-to-end verification, the initial implementation milestone delivers a complete vertical slice:

1. **Claim Submission:** Accept a single factual claim via `POST /api/v1/verifications`.
2. **Dialectical Retrieval:** Search for supporting and counterevidence using the Brave Search adapter with attempt pre-reservation.
3. **Provenance & Clustering:** Extract raw snippets, compute canonical URLs, and cluster syndicated source families via MinHash fingerprinting.
4. **Sufficiency Gate:** Execute Gate A deterministic screening and Gate B semantic assessment.
5. **Grounded Synthesis:** Generate an explanation with Tier 1 and Tier 2 validated citations.
6. **Local Persistence:** Persist the result and evidence snapshot in SQLite.
7. **Workbench Display:** Render the verdict badge, summary, stance tags, and expandable source excerpts in the React UI.

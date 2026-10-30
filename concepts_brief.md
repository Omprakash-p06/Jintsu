# Reality Check AI (`jintru`)

* **Author:** EGM Ideation Team
* **Date:** 2026-10-30
* **Status:** Design Review in Progress (Plan Audit Revisions Applied)

## Overview

`jintru` is a claim-verification workbench that evaluates user-provided factual assertions against retrieved web evidence. It determines whether a claim is supported, contradicted, or unresolved, and explicitly details what evidence is missing when a conclusion cannot be drawn.

Existing verification approaches either present unorganized search links or rely on generative language models that hallucinate plausibility without verifying citations. `jintru` resolves these limitations through:
1. A bounded two-stage retrieval policy (ADR-001) with an authoritative 8.0-second request deadline and strict attempt tracking.
2. A two-stage evidence sufficiency gate (ADR-002) that applies deterministic structural screening before calling structured semantic assessment models.
3. A multi-layer defense-in-depth model (ADR-003) with SSRF filtering and capability stripping to reduce indirect prompt injection risk.
4. Independent evaluation of retrieval quality, evidence sufficiency, citation entailment, and verdict accuracy.

The application is structured as a typed React 19.3 frontend paired with an asynchronous FastAPI 0.162.0 backend and an isolated Meta Model API adapter.

## Analysis

### 1. Contrarian & YAGNI Lens (Complexity & Necessity)
* **Risk of Over-Engineering:** Autonomous multi-agent swarms, dynamic microservices, and local vector databases introduce non-deterministic race conditions and operational complexity without improving claim verification precision.
* **Mitigation:** The system operates as a bounded, application-controlled pipeline within a unified FastAPI service. Retrieval executes parallel queries under strict concurrency ceilings. Local SQLite with async SQLAlchemy 2.x (`aiosqlite`) and Alembic provides persistent history. Vector indexes, external database servers, and autonomous agent loops are deferred until empirical requirements justify them.

### 2. Cost, Quota & Token Economics Lens
* **Retrieval Fan-Out & Latency Ceilings (Resolved via ADR-001 & ADR-004):** Unconstrained positive and negative search queries on multi-proposition claims cause rate-limit exhaustion and breach latency targets.
* **Mitigation:** Retrieval is bounded to an initial focused query per atomic claim (maximum 5 claims per request). Counterevidence queries are issued selectively only when initial evidence is one-sided, conflicting, or incomplete. Total distinct queries are capped at 10, with an atomic request-scoped counter tracking actual provider attempts (maximum 12, including retries). All operations are governed by an authoritative 8.0-second request deadline. Fast-path cached verifications maintain a P95 $\le$ 3.0s target.

### 3. UX & Developer Ergonomics Lens
* **Cognitive Load & Trust:** Uncalibrated AI confidence percentages mislead users, while single-verdict labels obscure underlying source disagreements.
* **Mitigation:** The interface adopts a research-workbench model. It displays explicit 5-way public verdict badges (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`), surfaces source stance tags (`supporting`, `refuting`, `neutral`), diagnoses specific evidence gaps, and attributes every sentence in an explanation to verified, inspectable source excerpts.

### 4. Migration & Backward Compatibility Lens
* **Schema Drift:** LLM JSON format shifts across model releases break client components.
* **Mitigation:** Strict Pydantic v2 schemas govern all boundaries at `/api/v1`. The frontend generates TypeScript definitions directly from `/openapi.json`. Database evolution is tracked through versioned Alembic migrations.

### 5. Observability & SRE Debuggability Lens
* **Failure Attribution:** Operational failures must distinguish web retrieval timeouts, model rate limits, schema errors, and genuine lack of evidence.
* **Mitigation:** Every request receives a unique `request_id`. Stage execution latencies, token consumption, and provider errors are recorded in structured JSON logs. All subordinate HTTP timeouts (connect 3s, read 5s) are capped by the remaining request deadline (`min(timeout, remaining_time)`). In-flight calls abort cleanly on deadline expiration, returning structured HTTP 504 `PROVIDER_TIMEOUT` envelopes.

### 6. Long-Term Maintenance & Security Lens
* **Indirect Prompt Injection in Retrieved Evidence (Resolved via ADR-003):** Adversarial web pages containing instructions can manipulate model generation while satisfying JSON schema validation.
* **Mitigation:** Enforce a multi-layer defense-in-depth model:
  1. Segregate system instructions from untrusted web text; strip control characters and wrap excerpts in XML delimiters.
  2. Scan retrieved content for instruction-like patterns and adversarial redirects.
  3. Strip model capabilities (zero database write permissions, zero tool-execution authority). Enforce SSRF protection blocking private IP ranges on all outbound fetches.
  4. Decouple model execution into two separate tasks: *Evidence Assessment* (passage relation tagging) and *Verdict Synthesis* (explanation generation using exclusively validated assessments).
  5. Run an independent `CitationValidator` in application code to ensure every cited passage entails the generated claim.

## Goals vs. Non-Goals

### In-Scope Goals
* **FR-01 to FR-03:** Ingest claims up to 2,000 characters, normalize within the submitted claim text, and decompose compound statements into up to 5 atomic propositions (rejecting larger requests with `TOO_MANY_CLAIMS`).
* **FR-04 & FR-05:** Execute bounded two-stage retrieval (ADR-001) with selective counterevidence search.
* **FR-06 & FR-07:** Run two-stage sufficiency evaluation (Gate A deterministic screening, Gate B structured semantic assessment) to output one of five explicit public verdicts.
* **FR-08 to FR-10:** Generate evidence-grounded explanations with verified citations and explicit source conflict views.
* **FR-11 to FR-13:** Maintain local SQLite history with inspection, individual record deletion, and total history clear under user-controlled data minimization.
* **Defect Prevention Layers A–E:** Enforce static analysis, unit invariants, contract compatibility, Playwright E2E browser tests, and semantic factuality evaluations with prompt injection regression cases.

### Out-of-Scope Non-Goals
* **Multimodal Verification (FR-15):** Parsing charts, video, audio, or images is deferred to Phase 2.
* **Vector Knowledge Bases:** Managing local vector embeddings (FAISS, LanceDB, Qdrant) is excluded; initial verification relies on live web search.
* **Multi-Tenant Enterprise Auth:** Complex RBAC and multi-user authentication are excluded from the initial local/single-user release.
* **Conversational Pronoun Resolution:** Multi-turn session context is excluded from initial claim normalization (FR-02).

## Alternatives Weighed

1. **Unconstrained Upfront Dialectical Fan-Out (2 searches per atomic claim upfront):**
   * *Why Rejected:* Multiplies API latency and query quotas rapidly, violating latency targets and causing provider rate limits. Replaced by ADR-001 bounded two-stage retrieval.
2. **Single-Pass Prompting (Standard RAG):**
   * *Why Rejected:* Research (EMNLP 2026 Cross-Benchmark, CoBiT) shows this amplifies confirmation bias and frequently manufactures false definitive verdicts when evidence is absent.
3. **Purely Deterministic or Purely Model-Driven Sufficiency:**
   * *Why Rejected:* Purely deterministic rules fail on paraphrased or multi-hop claims; purely model-driven checks suffer from high over-answering on absent evidence (Do LLMs Know When Evidence is Insufficient?, 2026). Replaced by ADR-002 two-stage sufficiency.
4. **Prompt Delimiters as Sole Injection Defense:**
   * *Why Rejected:* Research (TRACER 2026, USENIX 2026) demonstrates models obey adversarial commands inside retrieved context even when wrapped in delimiters. Replaced by ADR-003 multi-layer trust boundary.
5. **Single Scalar Confidence Score:**
   * *Why Rejected:* Model self-reported confidence is uncalibrated. Replaced by transparent evidence coverage metrics and explicit gap statements.

## Key Decisions & Staging for Next Steps

* **ADR-001 (Bounded Retrieval):** Max 5 atomic claims, 1 initial query/claim, selective counterevidence query, max 10 distinct queries, max 12 provider attempts, max 3 concurrent calls, 8.0s hard cutoff.
* **ADR-002 (Two-Stage Sufficiency):** Gate A deterministic screening (provenance, coverage, soft relevance signal, source family deduplication) $\rightarrow$ Gate B semantic assessment with validated enums $\rightarrow$ internal states (`eligible`, `needs_more_evidence`, `cannot_verify`) mapped to 5 public verdicts.
* **ADR-003 (Injection Defense in Depth):** Sanitization, content scanning, capability stripping, SSRF blocking, decoupled model tasks, and independent citation validation in application code.
* **ADR-004 (Decoupled Latency SLAs):** Fast-path P95 $\le$ 3.0s for cached/mock paths; live search measured independently under an 8.0s synchronous ceiling.
* **ADR-005 (Multi-Axis Factuality & Security Metrics):** Tracking sufficiency, over-answering, citation precision, counterclaim symmetry, injection resistance, and benign utility.
* **Sample Fixture Verified:** Verified against NOAA Mauna Loa May 2024 monthly peak data (426.90 ppm).
* **Master Specification Anchored:** Fully recorded in [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md).

### Next Step Staging
* **Immediate Action:** Confirm readiness to transition from ideation review to formal design drafting.
* **Drafting Execution:** Run `/egm-draft` to construct the formal technical design document section-by-section using `concepts_brief.md` as the intake source.

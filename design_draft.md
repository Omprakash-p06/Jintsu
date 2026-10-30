# Reality Check AI (`jintru`) — Verifiable Claim Verification System

* **Author:** `jintru` Core Team
* **Status:** Draft
* **Date:** 2026-10-30

--------------------------------------------------------------------------------

## Overview

`jintru` is a claim-verification system designed to evaluate factual assertions against web-retrieved evidence. Unlike generic search tools that return unranked links or generative language models that produce plausibly phrased answers without verifying citations, `jintru` treats evidence verification as a structured, dialectical process. It identifies whether an assertion is supported by credible sources, contradicted by counterevidence, or unresolved due to missing data. 

The system operates as a single-agent, deterministic pipeline exposed through a typed web interface. It actively searches for counterevidence, diagnoses information gaps when evidence is lacking, and attributes every factual statement in its explanation to verifiable source excerpts.

## The Problem

Automated fact-checking tools and retrieval-augmented language models currently suffer from three systemic failure modes:

1. **Confirmation Bias in Search and Generation:** Standard retrieval pipelines formulate search queries that echo the user's initial premise. As demonstrated by recent NLP research (e.g., CoBiT benchmark), searching primarily for confirming evidence leads models to reinforce false claims rather than discover refuting data.
2. **Hallucinated Plausibility and Uncalibrated Certainty:** Large language models frequently output definitive verdicts even when retrieved evidence is irrelevant, outdated, or absent. Models cannot be relied upon to self-report their own uncertainty accurately, leading to false confidence and fabricated citations that look authoritative but fail upon inspection.
3. **Source Scope and Conflict Smoothing:** Complex claims often involve conflicting reports, outdated statistics, or mismatched scopes (such as confusing a local monthly measurement with a global annual average). Existing tools tend to average these discrepancies or silently select one convenient source, hiding genuine disagreements from the user.

Users investigating factual assertions need an evidence workbench that does not guess, does not conceal contradictions, and clearly identifies what specific evidence is missing when a claim cannot be verified.

## Goals

* **G-1 (Bounded Dialectical Verification):** Verify user claims (up to 2,000 characters) by retrieving both supporting evidence and counterevidence, completing execution within an authoritative 8.0-second request deadline.
* **G-2 (Evidence Sufficiency Enforcement):** Enforce an explicit two-stage evidence sufficiency gate (deterministic screening followed by structured semantic assessment) to prevent over-answering on partial, irrelevant, or absent evidence.
* **G-3 (Five-Way Verdict Taxonomy):** Classify claims strictly into one of five unambiguous public verdicts: `supported`, `contradicted`, `mixed`, `insufficient_evidence`, or `not_verifiable`.
* **G-4 (Verifiable Grounding & Citation Traceability):** Ensure 100% of factual statements in generated explanations cite explicit source identifiers that resolve to exact, inspectable excerpts in the retrieved evidence set.
* **G-5 (Defense-in-Depth Security):** Protect against indirect prompt injection in retrieved web content by isolating untrusted data, scanning for instruction patterns, stripping execution privileges, and validating citation entailment in application code.
* **G-6 (Local Privacy & Data Control):** Persist verification records in local SQLite storage without external telemetry or user tracking, providing explicit user controls to view, export, and permanently delete records.

## Non-Goals

* **NG-1 (Multimodal Analysis):** Ingesting, parsing, or verifying images, video, charts, or audio recordings is out of scope for the initial release (reserved for Phase 2).
* **NG-2 (Autonomous Agent Swarms):** Multi-agent negotiation loops, self-directed autonomous tool-use, and dynamic task delegation are excluded in favor of a deterministic, inspectable pipeline.
* **NG-3 (Local Vector Stores):** Embedding and indexing web corpora in local vector databases (such as FAISS or LanceDB) is excluded; the system relies on real-time search engine queries and direct page extractions.
* **NG-4 (Multi-Tenant User Management):** Enterprise authentication, role-based access control, and remote multi-user synchronization are excluded; the initial release operates in single-user local mode.
* **NG-5 (Multi-Turn Conversational Resolution):** Resolving pronouns or conversational references across an extended chat session is excluded; each verification request is evaluated as a standalone text submission.

## Open Questions

* **OQ-1 (Search Engine Endpoint Quotas):** Which Brave Search API tier (Search vs. Answers) best balances response latency and quota consumption for our 3 concurrent query ceiling?
* **OQ-2 (Model Context Optimization for Compound Claims):** For claims with 4–5 atomic propositions, should Gate B evaluate each proposition in isolated sub-prompts or batch them into a single structured assessment call?


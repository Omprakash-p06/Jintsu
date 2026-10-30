# Reality Check AI (`jintru`)

* **Author:** EGM Ideation Team
* **Date:** 2026-10-30
* **Status:** Final Audit Complete (Ready for Implementation)

## Overview

`jintru` is a claim-verification workbench that evaluates user-provided factual assertions against retrieved web evidence. It determines whether a claim is supported, contradicted, or unresolved, and explicitly details what evidence is missing when a conclusion cannot be drawn.

Its core proposition is:
> **"Show what supports a claim, what challenges it, how reliable that evidence is, and exactly what remains unknown."**

The system operates as a single-agent, deterministic pipeline exposed through a typed web interface. It resolves the limitations of existing approaches through:
1. **Bounded Dialectical Retrieval (ADR-001):** Authoritative 8.0s target deadline (with a 0.5s safety buffer for orchestration/DB), pre-reserved provider attempts, query intent tracking (`support_seeking` vs. `counterevidence_seeking`), source family clustering via text MinHash, and per-claim coverage metrics.
2. **Two-Stage Sufficiency & Temporal Reasoning (ADR-002):** Gate A deterministic screening (with soft lexical relevance) followed by Gate B structured semantic assessment. Evaluates evidence against claim event dates and observation periods, strictly distinguishing outdated evidence from contradictory evidence, and handling future predictions with explicit non-observability rationales.
3. **Comprehensive SSRF & Prompt Injection Defenses (ADR-003):** IP-pinned DNS rebinding protection, IPv4/IPv6 private range blocking, redirect chain re-validation, least-privilege capability stripping, and three-tier citation validation (Tier 1 structural existence, Tier 2 excerpt match, Tier 3 semantic entailment testing).
4. **Decoupled Evaluation Protocol (ADR-005):** Independent benchmarks for fixed-evidence reasoning and live-retrieval quality across 8 orthogonal metrics.

## First Milestone Vertical Slice

The initial release targets a lean vertical slice before adding batching or PDF reporting:
1. Submit one factual claim via web workbench.
2. Retrieve supporting and opposing evidence using Brave Search adapter with attempt pre-reservation.
3. Validate source provenance and cluster syndicated source families.
4. Run evidence sufficiency screening (Gate A) and assessment (Gate B).
5. Produce a 5-way verdict with Tier 1 and Tier 2 validated citations.
6. Persist verification and evidence snapshots locally in SQLite.
7. Render the verdict badge, summary, stance tags, and expandable source excerpts in the React UI.

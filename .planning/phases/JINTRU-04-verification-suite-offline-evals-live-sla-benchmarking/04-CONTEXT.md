# Phase 4 Context: Verification Suite, Offline Evals & Live SLA Benchmarking

## Phase Goal
Implement comprehensive automated testing, Playwright E2E user journeys, static security audits, offline factuality evaluation harness, and live WAN latency distribution benchmarking for Reality Check AI (`jintru`).

## Master Specifications & Single Source of Truth (SSOT)
All plans in Phase 4 are derived strictly from:
1. [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md) (Phases 7, 8; Section 5 Verification Plan)
2. [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md) (ADR-005: Decoupled Independent Factuality & Retrieval Evaluation Protocol)
3. [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md) (ADR-005, AVeriTeC Benchmark Foundation)
4. [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md) (Findings IR-09, IR-12, IR-17)
5. [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md) (Item 3: SLA Proof & Grounding Assertions)
6. [`AGENTS.md`](file:///home/omprakash/Documents/jintru/AGENTS.md) (Rules 1, 3, 4, 6, 7, 10, 11, 12, 13)

---

## Phase Requirements Breakdown

| Requirement | Description | Plan |
|:---|:---|:---:|
| **TEST-01** | Unit test suite verifying citation normalization, budget enforcement, mock provider compliance, and 0 database lockups under 10 concurrent tasks | `04-01-PLAN.md` |
| **TEST-02** | Playwright E2E tests validating CUJ 1 (claim submission to citation inspection) and CUJ 3 (abstention on absent evidence) across Chromium and Firefox | `04-01-PLAN.md` |
| **SEC-01** | Security audits passing `semgrep --config auto backend/`, `pip-audit backend/`, and `npm --prefix frontend audit` | `04-01-PLAN.md` |
| **EVAL-01** | Offline evaluation benchmark (`evals/run_evals.py` on `evals/cases.jsonl`) verifying citation entailment precision ≥ 90%, false-support rate ≤ 5%, and counterevidence recall ≥ 80% | `04-02-PLAN.md` |
| **EVAL-02** | Live WAN retrieval latency distribution benchmarking (P50, P90, P95) asserting 100% fail-safe degradation to HTTP 504 when synthesis window drops below 2.5s | `04-02-PLAN.md` |

---

## Key Invariants & Thresholds
1. **Monotonic SLA Ceiling & Clean Abort (Rule 4):**
   - 8.0s total request lifecycle ceiling.
   - At least 2.5s remaining required before model synthesis begins.
   - Injected latency overruns (< 2.5s remaining) must cleanly return HTTP 504 with structured `ErrorEnvelope` in 100% of cases without DB writes or pseudo-verdicts.
2. **Concurrency Integrity (Rule 10):**
   - 10 concurrent asynchronous workers performing simultaneous reads and writes must complete with **0** `OperationalError: database is locked` exceptions.
3. **Decoupled Evaluation Protocol (ADR-005):**
   - Mode 1: Fixed-evidence evaluation isolating reasoning and citation entailment.
   - Mode 2: Live retrieval & SLA latency benchmarking tracking distribution and timeout fail-safe behavior.
   - Target thresholds:
     - Citation Entailment Precision: ≥ 90%
     - False-Support Rate under Absent Evidence: ≤ 5%
     - Counterevidence Recall: ≥ 80%
4. **CI Matrix:**
   - Python 3.12, Node.js 20.x, automated linting, typing, unit tests, security audits, and Playwright E2E.


# Concerns Summary: Reality Check AI (jintru)

## Known Issues and Risks

### 1. Python 3.12 Version Restriction
- **Location:** `backend/pyproject.toml` — `requires-python = ">=3.12"`
- **Concern:** The restriction may be overly conservative. Code may function on Python 3.10/3.11, but the restriction prevents testing on those versions.
- **Risk:** Limits testing coverage and potential user base.
- **Mitigation:** Consider whether the restriction is truly necessary or if it can be relaxed to `>=3.10`.

### 2. SQLite Concurrency Under High Load
- **Location:** `backend/db/database.py` — Connection management with `busy_timeout = 5000`
- **Concern:** While 10 concurrent workers with 200 operations showed 0 `database is locked` errors, higher concurrency may reveal locking issues.
- **Risk:** Potential database lock errors in production under peak load.
- **Mitigation:** Monitor lock contention in production; consider `synchronous = FULL` for critical data, or implement retry logic with longer backoff.

### 3. Brave Search API Rate Limiting
- **Location:** Retrieval pipeline (Stage 1 and Stage 2)
- **Concern:** Sequential single-query execution guarantees QPS ≤ 0.5, but burst scenarios may exceed Brave's rate limits.
- **Risk:** Intermittent 429 responses from Brave Search API, causing request failures.
- **Mitivation:** Implement client-side retry with exponential backoff; consider caching search results for repeated claims.

### 4. 8.0-Second SLA Ceiling Tightness
- **Location:** Verification pipeline timing
- **Concern:** The 8.0-second ceiling is tight, with only 0.5s buffer for SQLite persistence and safety. Network variability could push requests over the limit.
- **Risk:** Frequent HTTP 504 Gateway Timeout errors when remaining time drops below 2.5s before synthesis.
- **Mitigation:** 
  - Ensure Stage 1 timeout clamped to `min(2.0, remaining)` 
  - Stage 2 counter-search skipped when remaining time < 3.5s
  - Minimum 2.5s synthesis window guard strictly enforced

### 5. Model Provider Dependencies
- **Location:** `backend/app/` — Meta Model API (`api.meta.ai/v1`, `muse-spark-1.3`)
- **Concern:** External provider availability and response time variability.
- **Risk:** If Meta API is unavailable or slow, all verification requests time out.
- **Mitigation:** Implement fallback strategies; monitor API uptime; consider circuit breaker pattern.

### 6. Counterevidence Rule Strictness
- **Location:** Verdict determination logic
- **Concern:** The "absence of counterevidence" rule strictly prohibits `supported` if any source has `stance == "refutes"`, even with contextual relevance.
- **Risk:** May downgrade valid claims to `mixed` when some sources support and others refute, potentially underrepresenting consensus.
- **Mitigation:** The two-domain minimum corroboration rule (`at least two distinct source_family_id clusters`) provides some balance, but the interaction between these rules may need fine-tuning.

### 7. Three-Tier Citation Validation Limitations
- **Location:** Citation validation pipeline (Tier 1/2/3)
- **Concern:** Tier 2 (provenance match) requires verbatim substring match after html.unescape(), whitespace collapsing, and smart quote normalization. Minor formatting differences can cause failures.
- **Risk:** Legitimate citations flagged as imprecise, reducing citation precision below the 90% target.
- **Mitigation:** The 100% citation entailment precision achieved in benchmarks suggests current implementation is adequate, but edge cases with non-standard quoting may need handling.

### 7. Gate A Pre-Retrieval Screening Ambiguities
- **Location:** `conservative pre-retrieval screening` logic
- **Concern:** Subjective superlatives require predicate context ("is the greatest of all time") or normative moral prescriptions with statutory context. Ambiguous statements fall back to the retrieval pipeline.
- **Risk:** False negatives (subjective claims not flagged) or false positives (factual claims flagged as subjective).
- **Mitigation:** Continuous review of flagged cases; update predicate context rules based on user feedback.

### 9. Snippet-First Evidence Ingestion Limitations
- **Location:** Network security boundary (snippet-first ingestion)
- **Concern:** Zero raw HTML crawling — evidence only through search snippets and LLM context endpoints.
- **Risk:** Limited context for complex claims that require page-level understanding beyond snippet length.
- **Mitigation:** Stage 2 dialectical counter-search mitigates some risk; consider multi-query expansion for complex claims.

### 10. Phase 4 Scope Creep Risk
- **Location:** Roadmap governance (`misc/ROADMAP.md`)
- **Concern:** Phase 4 (Verification Suite, Offline Evals & Live SLA Benchmarking) includes many deliverables: evaluation benchmark, benchmark runner, SLA tracking, 504 degradation guard, CI integration.
- **Risk:** Scope may become unwieldy, delaying completion or reducing quality.
- **Mitigation:** Follow the 4 coarse phases in `.planning/ROADMAP.md`; each phase plan (`*-PLAN.md`) must cite SSOT documents as foundation; milestone completion gates enforce SSOT compliance.

## Risk Mitigation Priorities

### High Priority
1. **SLA timeout enforcement** — Critical for user experience (0.5s safety buffer is tight)
2. **SQLite concurrency** — Database lock errors affect core functionality
3. **Counterevidence rule** — Determines verdict correctness fundamentally

### Medium Priority
4. **Python version restriction** — Impacts testing and user adoption
5. **Brave API rate limiting** — Affects reliability under load
6. **Gate A screening** — Balances false positives vs. false negatives

### Lower Priority
7. **Citation validation edge cases** — Current 100% precision suggests adequacy
8. **Snippet context limits** — Stage 2 counter-search provides mitigation
9. **Phase scope management** — Follow roadmap governance

## Monitoring and Observability Recommendations

### Metrics to Track
- **SLA compliance rate:** Percentage of requests completing within 8.0s
- **Synthesis window violations:** Count of times < 2.5s remaining before synthesis
- **Database lock count:** `OperationalError: database is_locked` occurrences
- **API response times:** Meta Model and Brave Search latency percentiles
- **Verdict distribution:** Count of each verdict type (`supported`, `contradicted`, `mixed`, `insufficient_evidence`, `not_verifiable`)
- **Counterevidence rate:** Percentage of claims with at least one `refutes` source

### Alert Thresholds
- SLA compliance < 95% → Investigate pipeline timing
- Database lock count > 5/day → Review concurrency strategy
- Counterevidence rate > 30% → Review retrieval scope
- Verdict distribution skew (e.g., > 80% `supported`) → Review counterevidence logic

## Future Considerations

### Potential Improvements
1. **Relax Python version** to `>=3.10` if code compatibility confirmed
2. **Add caching** for frequently searched claims
3. **Implement circuit breaker** for Meta Model API
4. **Add request tracing** for SLA bottleneck analysis
5. **Multi-query expansion** for complex claims beyond snippet context
6. **Alternative search providers** as fallback for Brave Search
7. **Enhanced Gate A** with more subjective value judgment patterns

### Deferred to Milestone 2
- Compound claim decomposition (FActScore)
- Multi-hop reasoning across related claims
- Real-time citation ranking and scoring
- User preference customization of verdict thresholds
# Stage 7 Critic Review Report: `docs/designs/jintru_claim_verification.md`

**Auditors:** Hostile Design Critic (`egm-design`), Structural Layout Validator (`egm-structural`), Technical Copy Editor (`egm-style`)  
**Target Scope:** `FeatureRange` (Lines 1–377 of [`docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/docs/designs/jintru_claim_verification.md))  
**Standards Applied:** [`feature-spec-standard.md`](file:///home/omprakash/.gemini/config/plugins/egm/resources/document_standards/feature-spec-standard.md)  
**Context Documents:** [`docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/docs/designs/concepts_brief.md), [`docs/specification.md`](file:///home/omprakash/Documents/jintru/docs/specification.md)  
**Review Stage:** Stage 7 (Antagonistic Critic Swarm)  
**Overall Verdict:** 🔴 **FAIL — 3 Blockers, 8 Majors, 11 Nits Identified**

---

## 1. Executive Summary

The antagonistic tri-lens critic swarm evaluated the `FeatureRange` (Lines 1–377) of the revised specification. While the document demonstrates commendable engineering maturity—eliminating previous multi-agent orchestration, raw-socket IP pinning, and relational database cascades—the critics identified critical runtime, concurrency, and security vulnerabilities that must be resolved prior to implementation:

1. **Unexecutable Stage 2 Counter-Search Trigger:** The architecture specifies triggering Stage 2 counterevidence retrieval when Stage 1 evidence is "one-sided or disputed", but at this point in the pipeline zero LLM calls have occurred and no heuristic algorithm is provided.
2. **Statistically Unachievable 1.5s Synthesis Window:** Generating a deeply nested 400–600 token JSON schema over public WAN endpoints within 1.5s is statistically impossible under typical cloud LLM latency profiles, guaranteeing an aborted socket or timeout 100% of the time under budget strain.
3. **SQLite `PRAGMA busy_timeout` Connection Scope Vulnerability:** Executing `PRAGMA busy_timeout = 5000;` only during initial DB setup leaves all subsequent runtime connection instances running with SQLite's default 0ms busy timeout, causing immediate `database is locked` crashes on concurrent writes.
4. **False-Positive Gate A and Injection Quarantine Flaws:** Crude keyword substring matching causes false rejections of legitimate empirical assertions (e.g., "Best Buy", "Best Actor", "Prince William") and censors legitimate cybersecurity content.
5. **XML Delimiter Boundary Breakout:** Failure to escape `<` and `>` in retrieved search snippets enables adversarial prompt breakout.

---

## 2. Prioritized Findings Matrix

| ID | Severity | Lens | Affected Lines | Title / Summary |
| :--- | :--- | :--- | :--- | :--- |
| **CR-01** | 🔴 Blocker | Design Critic | Lines 89–92, 161, 203, 241 | Unspecified decision logic for Stage 2 counter-search trigger (no LLM between Stage 1 & 2) |
| **CR-02** | 🔴 Blocker | Design Critic | Lines 36, 159, 237–248, 361 | 1.5s minimum synthesis window statistically unachievable over WAN for 400–600 token JSON |
| **CR-03** | 🔴 Blocker | Design Critic | Lines 294–301, 525–609 | SQLite `PRAGMA busy_timeout` connection-scoped; resets to 0ms on new connections in CRUD methods |
| **CR-04** | 🟡 Major | Design Critic | Lines 38, 105–115, 142–146 | Naive keyword substring matching in Gate A causes false-positive abstentions on objective claims |
| **CR-05** | 🟡 Major | Design Critic | Lines 41, 120–126, 268–272 | Substring injection quarantine censors legitimate cybersecurity and AI empirical claims |
| **CR-06** | 🟡 Major | Design Critic | Lines 123, 268–272 | Missing XML entity escaping (`html.escape`) allows adversarial prompt delimiter breakout |
| **CR-07** | 🟡 Major | Design Critic | Lines 65, 173–177, 230 | Undefined "authoritative" single-source criterion for `contradicted` and unrefuted stance policy |
| **CR-08** | 🟡 Major | Design Critic | Lines 250–257 | Inadequate domain clustering via `urllib.parse` on multi-part public suffixes (`.co.uk`) |
| **CR-09** | 🟡 Major | Style Critic | Lines 66, 242, 247, 330 | Contradictory degradation behavior when synthesis window is < 1.5s ("return partial" vs 504) |
| **CR-10** | 🟡 Major | Style Critic | Lines 36, 38, 76, 78, 142, 158 | Overloaded nomenclature: "Gate A" used for both pre-retrieval and post-retrieval screening |
| **CR-11** | 🟡 Major | Structural Validator | Lines 6–8 | Host-specific absolute file URIs (`file:///home/omprakash/...`) break repository portability |
| **CR-12** | 🟢 Nit | Style Critic | Lines 20, 267 | Promotional hyperbole ("battle-tested", "completely eliminated") |
| **CR-13** | 🟢 Nit | Design Critic | Line 246, Line 327 | Multi-request concurrency rate limit gap on Brave Search |
| **CR-14** | 🟢 Nit | Design Critic | Lines 64, 421 | Fictitious endpoint (`api.meta.ai`) and model identifiers |
| **CR-15** | 🟢 Nit | Structural / Style | Lines 294–299 | Fenced code block language tag mismatch for SQL pragmas (`python` vs `sql`) |
| **CR-16** | 🟢 Nit | Structural / Style | Line 374 vs Lines 307–308 | Inconsistent endpoint namespace prefix (`/api/v1`) in NFR privacy section |
| **CR-17** | 🟢 Nit | Style Critic | Line 54 (NG-6) | Broken grammatical parallelism in Non-Goals |
| **CR-18** | 🟢 Nit | Style Critic | Lines 348–352 | Subjective phrasing in Alternatives Considered ("Over-Normalized", "Extremely fragile") |
| **CR-19** | 🟢 Nit | Structural Validator | Lines 10, 68, 128, 321 | Asymmetrical horizontal rule partitioning across top-level H2 sections |
| **CR-20** | 🟢 Nit | Structural Validator | Line 64 (OQ-3) | Typographic asymmetry in Open Question status tokens (`*Open...*` vs `**RESOLVED.**`) |
| **CR-21** | 🟢 Nit | Structural Validator | Lines 309–319 | 2-space indentation depth for nested fenced code block in Target API Contract |
| **CR-22** | 🟢 Nit | Style Critic | Lines 14, 32, 40, 47 | Conversational wordiness and redundant phrasing |

---

## 3. Detailed Critic Findings

### 🔴 Blockers

#### CR-01: Unspecified Decision Logic for Stage 2 Counter-Search Trigger
* **Reviewer:** Hostile Design Critic
* **Affected Scope:** Lines 89–92, 161, 203, 241.
* **Finding:** The architecture specifies that Stage 2 counterevidence retrieval is triggered *"only when Stage 1 evidence is one-sided or disputed, and remaining request time is ≥ 3.5s"*. However, between Stage 1 and Stage 2, zero LLM calls have occurred. The retrieved snippets are raw strings with default stance. No mechanism, classifier, or heuristic is defined to determine whether snippets are "one-sided" or "disputed".
* **Remediation:** Make Stage 2 dialectical search an **unconditional two-sided retrieval step whenever `remaining_time >= 3.5s`**. Stage 1 queries the direct factual assertion; Stage 2 queries dialectical counterevidence (e.g. formulating a counter-query with terms like `"false" OR "disputed" OR "criticism"` or negation keywords). If `remaining_time < 3.5s`, Stage 2 is skipped. This is completely deterministic and guarantees true two-sided fairness for all empirical claims.

#### CR-02: 1.5s Minimum Synthesis Window is Statistically Unachievable
* **Reviewer:** Hostile Design Critic
* **Affected Scope:** Lines 36, 159, 237–248, 361.
* **Finding:** `VerificationSynthesisPayload` is a deeply nested JSON schema requiring 350–600 output tokens. Over public WAN endpoints, TTFT averages 300–800ms, and generation requires 2.0–6.0s. Initiating an external LLM call with only 1.5s remaining guarantees an HTTP socket timeout or SLA breach 100% of the time under budget strain.
* **Remediation:** Increase the minimum synthesis window threshold from 1.5s to **2.5s** (or 3.0s). If remaining time before synthesis is < 2.5s, abort cleanly and return an HTTP 504 Gateway Timeout before dispatching the model call.

#### CR-03: SQLite `PRAGMA busy_timeout` Connection-Scope Vulnerability
* **Reviewer:** Hostile Design Critic
* **Affected Scope:** Lines 294–301, 525–609.
* **Finding:** `PRAGMA busy_timeout` and `PRAGMA synchronous` are connection-scoped. Executing them once in `init_db()` leaves all subsequent runtime connections opened via `aiosqlite.connect(self.db_path)` with default 0ms busy timeout. Any concurrent write will immediately throw `OperationalError: database is locked`.
* **Remediation:** In `Database`, implement a connection context manager:
  ```python
  @asynccontextmanager
  async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
      async with aiosqlite.connect(self.db_path) as db:
          await db.execute("PRAGMA journal_mode = WAL;")
          await db.execute("PRAGMA synchronous = NORMAL;")
          await db.execute("PRAGMA busy_timeout = 5000;")
          yield db
  ```
  and route all CRUD methods through `self.get_connection()`.

---

### 🟡 Majors

#### CR-04: Naive Keyword Substring Matching in Gate A
* **Reviewer:** Hostile Design Critic
* **Finding:** Unanchored substring searches for `best`, `worst`, and `will` cause false-positive rejections of legitimate factual assertions (e.g. "Cillian Murphy won the Academy Award for Best Actor in 2024", "Best Buy was founded in 1966", "Prince William was born in 1982"). Hardcoding `by 2028` fails for other future years.
* **Remediation:** Use regex word boundaries `\b(should|ought to)\b`, and for future predictions, extract 4-digit years via `\b(20\d{2})\b` and compare numerically against the current year (`year > datetime.now(timezone.utc).year`).

#### CR-05: Substring Injection Quarantine Censoring Legitimate Content
* **Reviewer:** Hostile Design Critic
* **Finding:** Flagging snippets containing `system prompt:` or `override` causes 100% false-positive quarantine on legitimate cybersecurity and AI empirical claims (e.g., USENIX research papers).
* **Remediation:** Do not discard evidence based on raw keyword substring matching. Instead, enforce structural XML containment with character escaping, and rely on post-generation corroboration (2-domain rule and Tier 2 substring matching).

#### CR-06: Missing XML Entity Escaping Allows Prompt Boundary Breakout
* **Reviewer:** Hostile Design Critic
* **Finding:** Snippets are wrapped in `<evidence_snippet>` tags without escaping `<` and `>`. Malicious snippets can close the tag `</evidence_snippet>` and inject arbitrary pseudo-tags.
* **Remediation:** Apply `html.escape(snippet, quote=True)` to all search snippet text before embedding in prompt templates.

#### CR-07: Undefined "Authoritative" Criterion and Unrefuted Stance Policy
* **Reviewer:** Hostile Design Critic
* **Finding:** `contradicted` requires "at least 1 authoritative or 2 distinct source families with stance='refutes'". "Authoritative" is undefined (NG-10 forbids credibility scoring). Additionally, "0 unrefuted 'refutes' stances" has no structured field in the synthesis schema.
* **Remediation:** Make the `contradicted` rule strictly structural: require ≥ 2 distinct `source_family_id` clusters with `stance="refutes"`. If any credible source refutes the claim, cap the verdict at `mixed` or `insufficient_evidence`.

#### CR-08: Inadequate Domain Clustering via `urllib.parse`
* **Reviewer:** Hostile Design Critic
* **Finding:** `urllib.parse.urlsplit().netloc` extracts hostnames, not registered domains. It fails on multi-part public suffixes (`.co.uk`, `.gov.in`), treating `news.bbc.co.uk` and `weather.bbc.co.uk` as separate domains.
* **Remediation:** Specify registered domain extraction with public suffix matching (e.g. `tldextract` or clean suffix parsing).

#### CR-09: Contradictory Degradation Behavior for Synthesis Timeout
* **Reviewer:** Technical Copy Editor
* **Finding:** Line 242 states "return partial", while Lines 66, 247, and 330 state an HTTP 504 Gateway Timeout is returned.
* **Remediation:** Standardize: if remaining time before synthesis is < 2.5s, abort cleanly and return an HTTP 504 Gateway Timeout with `ErrorEnvelope`.

#### CR-10: Terminology Collision: Overloaded "Gate A"
* **Reviewer:** Technical Copy Editor
* **Finding:** "Gate A" is used for both pre-retrieval input validation and post-retrieval snippet screening.
* **Remediation:** Standardize as **Gate A (Pre-Retrieval Input Filter)** and **Gate B (Evidence Sufficiency Filter)**.

#### CR-11: Host-Specific Absolute File URIs in Header Metadata
* **Reviewer:** Structural Layout Validator
* **Finding:** Header metadata links use machine-specific absolute file URIs (`file:///home/omprakash/...`), breaking git portability.
* **Remediation:** Use repository-relative Markdown links: `./concepts_brief.md`, `../specification.md`, and `../../consolidated_review_report.md`.

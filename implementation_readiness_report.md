# Implementation Readiness Audit Report: Phase 1 Planning Artifacts

**Audited Documents:**
- [`01-CONTEXT.md`](file:///home/omprakash/Documents/jintru/.planning/phases/JINTRU-01-foundations-data-contracts-external-providers/01-CONTEXT.md)
- [`01-01-PLAN.md`](file:///home/omprakash/Documents/jintru/.planning/phases/JINTRU-01-foundations-data-contracts-external-providers/01-01-PLAN.md)
- [`01-02-PLAN.md`](file:///home/omprakash/Documents/jintru/.planning/phases/JINTRU-01-foundations-data-contracts-external-providers/01-02-PLAN.md)

**Baseline SSOT & Ground Truth:**
- [`misc/docs/designs/jintru_claim_verification.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/jintru_claim_verification.md)
- [`AGENTS.md`](file:///home/omprakash/Documents/jintru/AGENTS.md)
- [`misc/docs/specification.md`](file:///home/omprakash/Documents/jintru/misc/docs/specification.md)
- [`misc/docs/designs/concepts_brief.md`](file:///home/omprakash/Documents/jintru/misc/docs/designs/concepts_brief.md)
- [`misc/consolidated_review_report.md`](file:///home/omprakash/Documents/jintru/misc/consolidated_review_report.md)
- [`misc/goldfish_review_report.md`](file:///home/omprakash/Documents/jintru/misc/goldfish_review_report.md)
- **Standard:** [`implementation-readiness-standard.md`](file:///home/omprakash/.gemini/config/plugins/egm/resources/document_standards/implementation-readiness-standard.md)

**Evaluators (Stateless Goldfish Review Swarm):**
- **Tech Lead:** `egm-implementation-readiness`
- **Quality Auditor:** `egm-codebase-details`
- **Copy Editor:** `egm-style`

**Stage 9 Verdict:** 🟡 **CONDITIONAL PASS (REMEDIATION REQUIRED BEFORE EXECUTION)**

---

## 1. Executive Summary

The Phase 1 planning artifacts demonstrate rigorous alignment with the converged Milestone 1 architecture in `misc/` and repository rules in `AGENTS.md`. The plans accurately partition the foundations, Pydantic data schemas, concurrency-safe SQLite persistence, and external search/synthesis adapters.

However, all three stateless Goldfish reviewers converged on a concise set of concrete execution hurdles, actionability gaps, and unstated design details that violate the **Zero-Decision Rule** and would cause immediate packaging, test discovery, or runtime failures if executed as written.

Specifically, the audit identified:
1. **2 Blockers**: Unbounded snippet extraction under Brave LLM Context mode, and naive substring matching on wire attribution tokens like `"AP"` (causing false syndicate clustering).
2. **6 Majors**: Missing Python test discovery configuration and Hatchling wheel mapping, omitted field definitions for 5 Pydantic response schemas, unstated provider factory mechanism, undeclared `respx` test dependency, underspecified mock return fixtures, and SQLite connection isolation risks in test suites.
3. **Style & Polish Nits**: Removal of promotional qualifiers, conversational filler, and standardization of dry engineering prose.

---

## 2. Consolidated Prioritized Findings

### 🔴 Blocker Findings

#### [Finding 1] [Unbounded LLM Context Retrieval in `BraveSearchProvider`]
* **Reviewer:** `egm-codebase-details`
* **Affected Scope:** `01-02-PLAN.md` (Task 2 Action, Step 2)
* **Issue:** Brave's `/res/v1/llm/context` endpoint does not accept a `count` parameter and returns all matching passages found by Brave's backend. The plan does not instruct slicing extracted passages to `count` (default 5). If Brave returns 15–20 passages, all of them would be ingested, directly violating Rule 3 in `AGENTS.md` (*"returning at most 5 snippets"*) and bloating synthesis latency.
* **Exact Fix:** Explicitly slice extracted context passages to `[:count]` during normalization in `BraveSearchProvider.search()`.

#### [Finding 2] [Flawed Substring Matching on Wire Attribution Token "AP"]
* **Reviewers:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** `01-02-PLAN.md` (Task 2 Action, Step 2)
* **Issue:** Substring checking for `"AP"` without word boundaries matches common words and acronyms ("Apple", "April", "CAP", "API"), incorrectly collapsing independent domains into a syndicate and violating the Two-Domain Corroboration Guardrail (`AGENTS.md` Rule 6).
* **Exact Fix:** Define explicit regex word-boundary mappings and standardized tokens:
  ```python
  WIRE_MAPPINGS = [
      (re.compile(r"\b(?:Associated Press|AP)\b", re.IGNORECASE), "associated_press"),
      (re.compile(r"\bReuters\b", re.IGNORECASE), "reuters"),
      (re.compile(r"\bPR Newswire\b", re.IGNORECASE), "pr_newswire"),
  ]
  ```

---

### 🟡 Major Findings

#### [Finding 3] [Pytest Import Resolution & Hatchling Package Discovery Failure]
* **Reviewers:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** `01-01-PLAN.md` (Task 1, Task 2), `backend/pyproject.toml`
* **Issue:** Running `pytest backend/tests/unit/...` from root fails with `ModuleNotFoundError: No module named 'app'` unless `pythonpath = ["."]` is configured. Additionally, Hatchling fails editable installs (`pip install -e backend`) because application code is located in `backend/app` rather than `backend/src` or `backend/jintru_backend`.
* **Exact Fix:** In `backend/pyproject.toml`, add:
  ```toml
  [tool.hatch.build.targets.wheel]
  packages = ["app"]

  [tool.pytest.ini_options]
  pythonpath = ["."]
  asyncio_mode = "auto"
  asyncio_default_fixture_loop_scope = "function"
  testpaths = ["tests"]
  ```
  And add `backend/tests/conftest.py` ensuring `backend/` is added to `sys.path`.

#### [Finding 4] [Omitted Field Definitions for 5 Pydantic Response/Envelope Schemas]
* **Reviewers:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** `01-01-PLAN.md` (Task 2 Action, Step 7)
* **Issue:** Task 2 enumerates fields for items 1–6, but simply states *"Implement VerificationResponse, VerificationListItem, PaginatedVerificationResponse, HealthResponse, and ErrorEnvelope"* without field names or types, violating the Zero-Decision Rule.
* **Exact Fix:** Document full class definitions in Task 2 matching `jintru_claim_verification.md` § Phase 2:
  ```python
  class VerificationResponse(BaseModel):
      id: str
      claim: str
      public_verdict: PublicVerdict
      summary: str
      limitations: list[str] = Field(default_factory=list)
      sources: list[SourceItem] = Field(default_factory=list)
      reasoning: list[ReasoningStatement] = Field(default_factory=list)
      created_at: str

  class VerificationListItem(BaseModel):
      id: str
      claim: str
      public_verdict: PublicVerdict
      created_at: str

  class PaginatedVerificationResponse(BaseModel):
      items: list[VerificationListItem]
      total: int

  class HealthResponse(BaseModel):
      status: str
      providers: dict[str, str]

  class ErrorEnvelope(BaseModel):
      error: str
      code: str
      detail: Optional[str] = None
  ```

#### [Finding 5] [Missing Provider Factory Mechanism for `USE_MOCK_PROVIDERS`]
* **Reviewer:** `egm-codebase-details`
* **Affected Scope:** `01-02-PLAN.md` (Task 1 Action)
* **Issue:** `Settings` defines `USE_MOCK_PROVIDERS: bool = False`, but the plan lacks a standardized factory function to resolve real vs mock providers, leaving downstream Phase 2 wiring undefined.
* **Exact Fix:** Add factory functions in `backend/app/providers/__init__.py`:
  - `get_search_provider(settings: Settings) -> SearchProvider`
  - `get_model_provider(settings: Settings) -> ModelProvider`

#### [Finding 6] [Undeclared Test Dependency `respx` vs `httpx.MockTransport`]
* **Reviewers:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** `01-02-PLAN.md` (Task 2, Task 3)
* **Issue:** Plans reference `respx`, but `respx` is not in `pyproject.toml`. Importing it causes `ModuleNotFoundError`.
* **Exact Fix:** Remove reference to `respx` and standardize unit tests on `httpx.MockTransport` and `unittest.mock`.

#### [Finding 7] [Underspecified Mock Return Payloads in `mock.py`]
* **Reviewer:** `egm-implementation-readiness`
* **Affected Scope:** `01-02-PLAN.md` (Task 1 Action)
* **Issue:** Mock return values are described as "canned" without explicit data structures, risking drift in Phase 2 pipeline tests.
* **Exact Fix:** Specify default fixtures: `MockSearchProvider` returns 2 distinct domain snippets (`example.com`, `reuters.com`) with valid SHA-256 hashes and `stance="supports"`; `MockModelProvider` returns a deterministic `VerificationSynthesisPayload`.

#### [Finding 8] [SQLite Connection Isolation Trap in `test_db.py`]
* **Reviewers:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** `01-01-PLAN.md` (Task 3 Behavior & Action)
* **Issue:** Testing `Database(db_path=":memory:")` wipes the DB between method calls because each `@asynccontextmanager _connect()` creates and closes a separate connection.
* **Exact Fix:** Mandate using a temporary SQLite file via pytest's `tmp_path` fixture (`Database(db_path=str(tmp_path / "test.db"))`).

---

### 🟢 Editorial & Style Nits

#### [Finding 9] [Missing File Action Markers (`Create`)]
* **Reviewer:** `egm-codebase-details`
* **Affected Scope:** `01-01-PLAN.md`, `01-02-PLAN.md`
* **Exact Fix:** Explicitly annotate target files with `(Create)` in task headers and frontmatter tables.

#### [Finding 10] [Multi-Passage `mode="context"` Concatenation]
* **Reviewer:** `egm-implementation-readiness`
* **Affected Scope:** `01-02-PLAN.md` (Task 2)
* **Exact Fix:** Specify joining passages with double newlines: `snippet = "\n\n".join(item.get("snippets", []))`.

#### [Finding 11] [Tone, Brevity, and Removing Promotional Qualifiers]
* **Reviewer:** `egm-style`
* **Affected Scope:** `01-CONTEXT.md`, `01-01-PLAN.md`, `01-02-PLAN.md`
* **Exact Fix:** Strip buzzwords ("concurrency-hardened", "flawless", "cleanly", "complete data contracts") in favor of dry, direct technical phrasing ("WAL-mode SQLite", "data contracts", "abstract interfaces").

---

## 3. Traceability Matrix

| Finding ID | Source Evaluator | Severity | Affected Artifact | Recommended Resolution |
| :--- | :--- | :---: | :--- | :--- |
| **F-01** | `egm-codebase-details` | 🔴 Blocker | `01-02-PLAN.md` | Slice `grounding.generic[].snippets` to `[:count]` |
| **F-02** | `egm-codebase-details`<br>`egm-implementation-readiness` | 🔴 Blocker | `01-02-PLAN.md` | Regex word-boundary wire mappings (`r"\b(?:Associated Press\|AP)\b"`) |
| **F-03** | `egm-implementation-readiness`<br>`egm-codebase-details` | 🟡 Major | `01-01-PLAN.md` | Add `packages = ["app"]`, `pythonpath = ["."]`, and `conftest.py` |
| **F-04** | `egm-implementation-readiness`<br>`egm-codebase-details` | 🟡 Major | `01-01-PLAN.md` | Enumerate full class schemas for 5 response/envelope models |
| **F-05** | `egm-codebase-details` | 🟡 Major | `01-02-PLAN.md` | Add `get_search_provider` and `get_model_provider` factory functions |
| **F-06** | `egm-implementation-readiness` | 🟡 Major | `01-02-PLAN.md` | Eliminate `respx`; mandate `httpx.MockTransport` |
| **F-07** | `egm-implementation-readiness` | 🟡 Major | `01-02-PLAN.md` | Define concrete mock return fixtures |
| **F-08** | `egm-implementation-readiness`<br>`egm-codebase-details` | 🟡 Major | `01-01-PLAN.md` | Test database with `tmp_path` fixture instead of `:memory:` |
| **F-09** | `egm-codebase-details` | 🟢 Nit | `01-01-PLAN.md`<br>`01-02-PLAN.md` | Add `(Create)` action markers to all file paths |
| **F-10** | `egm-implementation-readiness` | 🟢 Nit | `01-02-PLAN.md` | Specify `\n\n.join()` for multiple LLM context passages |
| **F-11** | `egm-style` | 🟢 Nit | All 3 docs | Strip qualitative adjectives; enforce plain engineering prose |

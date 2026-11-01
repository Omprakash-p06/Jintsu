"""Deterministic verification engine: Gate A screening, bounded retrieval, citation
validation and the application-level verdict policy.

Implements misc/docs/designs/jintru_claim_verification.md Section 3.1-3.5 and Phase 4.
"""

import hashlib
import html
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.api.schemas import (
    PublicVerdict,
    ReasoningStatement,
    SourceItem,
    VerificationResponse,
    VerificationSynthesisPayload,
)
from app.core.config import Settings, settings
from app.core.errors import ClientDisconnectedError, ProviderTimeoutError
from app.db.database import Database
from app.providers import get_model_provider, get_search_provider
from app.providers.base import ModelProvider, SearchProvider

# Authoritative 8.0s budget stage allocations (AGENTS.md rule 4).
STAGE1_TIMEOUT_SECONDS = 2.0
STAGE2_TIMEOUT_SECONDS = 2.0
SYNTHESIS_TIMEOUT_SECONDS = 3.0
STAGE2_MIN_REMAINING_SECONDS = 3.5
MIN_SYNTHESIS_WINDOW_SECONDS = 2.5
MAX_STAGE_RESULTS = 5

SUBJECTIVE_MESSAGE = (
    "Subjective value judgment or normative statement; lacks an empirical ground truth."
)
FUTURE_MESSAGE = (
    "Future prediction or prospective event; cannot be empirically verified prior to occurrence."
)

COUNTEREVIDENCE_LIMITATION = (
    "Material counterevidence identified in retrieved sources; claim cannot be marked "
    "supported while unresolved refuting evidence exists."
)
SINGLE_FAMILY_LIMITATION = (
    "Corroborated by a single source domain; secondary independent corroboration required "
    "for supported verdict."
)
CONTRADICTION_GROUNDING_LIMITATION = (
    "No directly refuting source supports a contradicted verdict; verdict capped at "
    "insufficient_evidence."
)
CONFLICT_GROUNDING_LIMITATION = (
    "Proposed mixed verdict lacks both supporting and refuting sources; verdict capped at "
    "insufficient_evidence."
)
EMPTY_EVIDENCE_LIMITATION = (
    "No usable external evidence was retrieved for this claim; a definitive verdict cannot "
    "be awarded."
)
QUARANTINE_LIMITATION = (
    "One or more retrieved snippets were quarantined by the prompt-injection screen and "
    "excluded from synthesis."
)

_SUPERLATIVE_PATTERN = re.compile(
    r"\b(?:is|are|was|were)\s+(?:the\s+)?(?:greatest|best|worst|finest)\b"
    r"[^.?!]{0,60}?\b(?:of\s+all\s+time|in\s+(?:\w+\s+)?history|ever)\b",
    re.IGNORECASE,
)
_MORAL_PATTERN = re.compile(
    r"\b(?:morally|ethically)\s+(?:wrong|right|evil|good)\b",
    re.IGNORECASE,
)
_PRESCRIPTIVE_PATTERN = re.compile(
    r"\b(?:we|society|people|governments?)\s+(?:ought\s+to|should)\b",
    re.IGNORECASE,
)
_STATUTORY_CONTEXT_PATTERN = re.compile(
    r"\b(?:statutes?|laws?|legal|legislation|regulations?|acts?|courts?|constitution)\b",
    re.IGNORECASE,
)
_FUTURE_YEAR_PATTERN = re.compile(
    r"\b(?:in|by|until|during|through|for)\s+(20[2-9]\d)\b",
    re.IGNORECASE,
)
_PROSPECTIVE_MODAL_PATTERN = re.compile(
    r"\b(?:will|shall|projected\s+to|expected\s+to|forecast\s+to)\b",
    re.IGNORECASE,
)

_INJECTION_PATTERNS = ("system prompt:", "override verdict", "ignore instructions")
_CONTROL_CHAR_PATTERN = re.compile(
    "[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b\u200c\u200d\ufeff]"
)
_WHITESPACE_PATTERN = re.compile(r"\s+")

_MULTI_PART_SUFFIXES = frozenset(
    {
        "co.uk",
        "org.uk",
        "ac.uk",
        "gov.uk",
        "com.au",
        "net.au",
        "co.nz",
        "co.jp",
        "com.br",
        "co.in",
        "co.za",
    }
)

_WIRE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:Associated Press|AP)\b", re.IGNORECASE), "associated_press"),
    (re.compile(r"\bReuters\b", re.IGNORECASE), "reuters"),
    (re.compile(r"\bPR Newswire\b", re.IGNORECASE), "pr_newswire"),
)


# ---------------------------------------------------------------------------
# Gate A: pre-retrieval classification
# ---------------------------------------------------------------------------


def _is_subjective(claim: str) -> bool:
    if _SUPERLATIVE_PATTERN.search(claim) or _MORAL_PATTERN.search(claim):
        return True
    if _PRESCRIPTIVE_PATTERN.search(claim):
        return not _STATUTORY_CONTEXT_PATTERN.search(claim)
    return False


def _is_future_prediction(claim: str, current_year: int | None = None) -> bool:
    year_match = _FUTURE_YEAR_PATTERN.search(claim)
    if year_match is None:
        return False
    year = int(year_match.group(1))
    reference_year = current_year if current_year is not None else datetime.now(UTC).year
    if year <= reference_year:
        return False
    return _PROSPECTIVE_MODAL_PATTERN.search(claim) is not None


def classify_input(claim: str) -> tuple[PublicVerdict, str] | None:
    """Conservatively classify a claim before any network call.

    Returns a short-circuit verdict for subjective judgments and future predictions, or
    ``None`` to continue into the bounded retrieval pipeline.
    """
    if _is_subjective(claim):
        return ("not_verifiable", SUBJECTIVE_MESSAGE)
    if _is_future_prediction(claim):
        return ("not_verifiable", FUTURE_MESSAGE)
    return None


def sanitize_and_quarantine(snippet: str) -> tuple[str, bool]:
    """Strip control/zero-width characters and flag prompt-injection attempts."""
    cleaned = _CONTROL_CHAR_PATTERN.sub("", snippet or "")
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    lowered = cleaned.lower()
    quarantined = any(token in lowered for token in _INJECTION_PATTERNS)
    return cleaned, quarantined


# ---------------------------------------------------------------------------
# Source grouping and reconciliation
# ---------------------------------------------------------------------------


def normalize_excerpt(text: str) -> str:
    """Normalize excerpt text for verbatim provenance matching (Tier 2)."""
    unescaped = html.unescape(text or "")
    replaced = (
        unescaped.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return _WHITESPACE_PATTERN.sub(" ", replaced).strip()


def _is_safe_http_url(url: str) -> bool:
    """Validate that a URL uses http or https and has a valid netloc."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc)
    except (ValueError, AttributeError):
        return False


def _canonical_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _registrable_domain(host: str) -> str:
    """Reduce a hostname to its registered domain for source-family clustering.

    Subdomains of one publisher (news.bbc.co.uk, sports.bbc.co.uk) must not count as
    independent corroboration, so clustering keys on the registrable domain.
    """
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) <= 2 or all(part.isdigit() for part in parts):
        return host
    if ".".join(parts[-2:]) in _MULTI_PART_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _resolve_family_id(domain: str, title: str, snippet: str) -> str:
    text = f"{title} {snippet}"
    for pattern, wire_id in _WIRE_PATTERNS:
        if pattern.search(text):
            return wire_id
    return _registrable_domain(domain) or "unknown"


def group_sources(raw_results: list[dict]) -> list[SourceItem]:
    """Normalize, sanitize, de-duplicate and renumber a combined evidence pool."""
    sources: list[SourceItem] = []
    seen_hashes: set[str] = set()
    for raw in raw_results:
        snippet, is_quarantined = sanitize_and_quarantine(str(raw.get("snippet") or ""))
        if not snippet:
            continue
        raw_url = str(raw.get("url") or "").strip()
        url = raw_url if _is_safe_http_url(raw_url) else ""
        domain = _canonical_domain(url) if url else str(raw.get("domain") or "") or "unknown"
        title = str(raw.get("title") or "")
        # Hash the text that is actually stored, not the provider's raw payload: the
        # provider hashes pre-sanitization text, which would make content_hash identify
        # bytes the consumer cannot see and let zero-width variants dodge de-duplication.
        content_hash = hashlib.sha256(snippet.encode()).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)
        sources.append(
            SourceItem(
                source_id=f"src_{len(sources) + 1}",
                url=url,
                domain=domain,
                title=title,
                snippet=snippet,
                stance=raw.get("stance") or "neutral",
                source_family_id=_resolve_family_id(domain, title, snippet),
                retrieved_at=str(raw.get("retrieved_at") or datetime.now(UTC).isoformat()),
                published_at=raw.get("published_at"),
                source_type=raw.get("source_type") or "search_snippet",
                content_hash=content_hash,
                extraction_status="ok",
                is_quarantined=is_quarantined,
            )
        )
    return sources


def reconcile_synthesis(
    payload: VerificationSynthesisPayload,
    sources: list[SourceItem],
) -> tuple[list[SourceItem], list[ReasoningStatement]]:
    """Merge model source evaluations onto the active evidence pool."""
    by_id = {source.source_id: source for source in sources}
    for evaluation in payload.source_evaluations:
        target = by_id.get(evaluation.source_id)
        if target is None:
            continue
        target.stance = evaluation.stance
        target.relevance = evaluation.relevance
        target.exact_quote = evaluation.exact_quote
    return sources, list(payload.reasoning_statements)


# ---------------------------------------------------------------------------
# Three-tier citation validation (Tier 3 is evaluated offline in CI)
# ---------------------------------------------------------------------------


def validate_citations(
    statements: list[ReasoningStatement],
    sources: list[SourceItem],
) -> list[ReasoningStatement]:
    """Enforce Tier 1 ID presence and Tier 2 normalized verbatim excerpts."""
    active = {source.source_id: source for source in sources if not source.is_quarantined}
    validated: list[ReasoningStatement] = []
    for statement in statements:
        citation_ids = [cid for cid in statement.citation_ids if cid in active]
        if not citation_ids:
            continue
        excerpt = statement.quoted_excerpt
        if excerpt:
            normalized = normalize_excerpt(excerpt)
            grounded = bool(normalized) and any(
                normalized in normalize_excerpt(active[cid].snippet) for cid in citation_ids
            )
            if not grounded:
                excerpt = None
        validated.append(
            ReasoningStatement(
                statement=statement.statement,
                citation_ids=citation_ids,
                quoted_excerpt=excerpt,
            )
        )
    return validated


# ---------------------------------------------------------------------------
# Deterministic verdict policy
# ---------------------------------------------------------------------------


def apply_verdict_policy(
    payload: VerificationSynthesisPayload,
    sources: list[SourceItem],
) -> tuple[PublicVerdict, list[str]]:
    """Veto unsupported verdicts per AGENTS.md rule 6 and SSOT Section 5."""
    active = [source for source in sources if not source.is_quarantined]
    limitations = list(payload.limitations)
    verdict: PublicVerdict = payload.proposed_verdict

    refutations = [
        source
        for source in active
        if source.stance == "refutes" and source.relevance in ("direct", "contextual")
    ]
    direct_refutations = [source for source in refutations if source.relevance == "direct"]
    support = [
        source
        for source in active
        if source.stance == "supports" and source.relevance in ("direct", "contextual")
    ]
    any_supports = [source for source in active if source.stance == "supports"]
    any_refutation = [source for source in active if source.stance == "refutes"]

    if verdict == "supported":
        if refutations:
            verdict = "contradicted" if direct_refutations else "mixed"
            limitations.append(COUNTEREVIDENCE_LIMITATION)
        else:
            families = {source.source_family_id for source in support}
            if len(families) < 2:
                verdict = "insufficient_evidence"
                limitations.append(SINGLE_FAMILY_LIMITATION)
    elif verdict == "contradicted":
        if not direct_refutations:
            verdict = "insufficient_evidence"
            limitations.append(CONTRADICTION_GROUNDING_LIMITATION)
    elif verdict == "mixed" and not (any_supports and any_refutation):
        verdict = "insufficient_evidence"
        limitations.append(CONFLICT_GROUNDING_LIMITATION)

    return verdict, limitations


# ---------------------------------------------------------------------------
# Clock-bounded orchestrator
# ---------------------------------------------------------------------------


class VerificationPipeline:
    """Monotonic 8.0-second orchestrator for a single atomic claim."""

    def __init__(
        self,
        db: Database | None = None,
        search_provider: SearchProvider | None = None,
        model_provider: ModelProvider | None = None,
        deadline_seconds: float | None = None,
        settings_obj: Settings | None = None,
    ) -> None:
        self.settings = settings_obj or settings
        self.db = db if db is not None else Database(db_path=self.settings.DATABASE_PATH)
        self.search_provider = search_provider or get_search_provider(self.settings)
        self.model_provider = model_provider or get_model_provider(self.settings)
        self.deadline_seconds = (
            deadline_seconds
            if deadline_seconds is not None
            else self.settings.REQUEST_DEADLINE_SECONDS
        )

    async def verify(
        self,
        claim: str,
        is_disconnected: Callable[[], Awaitable[bool]] | None = None,
    ) -> VerificationResponse:
        start = time.monotonic()
        deadline = start + self.deadline_seconds

        def remaining() -> float:
            return deadline - time.monotonic()

        classification = classify_input(claim)
        if classification is not None:
            verdict, rationale = classification
            return await self._persist_and_return(
                claim=claim,
                verdict=verdict,
                summary=rationale,
                limitations=[],
                sources=[],
                reasoning=[],
            )

        raw_results = list(
            await self.search_provider.search(
                claim,
                count=MAX_STAGE_RESULTS,
                mode=self.settings.BRAVE_RETRIEVAL_MODE,
                timeout=min(STAGE1_TIMEOUT_SECONDS, remaining()),
            )
            or []
        )
        sources = group_sources(raw_results)
        active = [source for source in sources if not source.is_quarantined]

        if not active:
            return await self._abstain(claim, sources)

        await self._ensure_connected(is_disconnected)

        if raw_results and remaining() >= STAGE2_MIN_REMAINING_SECONDS:
            counter_results = list(
                await self.search_provider.search(
                    f"{claim} (dispute OR controversy OR false OR criticism OR debunk)",
                    count=MAX_STAGE_RESULTS,
                    mode=self.settings.BRAVE_RETRIEVAL_MODE,
                    timeout=min(STAGE2_TIMEOUT_SECONDS, remaining()),
                )
                or []
            )
            raw_results.extend(counter_results)
            sources = group_sources(raw_results)
            active = [source for source in sources if not source.is_quarantined]
            if not active:
                return await self._abstain(claim, sources)

        await self._ensure_connected(is_disconnected)

        budget = remaining()
        if budget < MIN_SYNTHESIS_WINDOW_SECONDS:
            raise ProviderTimeoutError(
                "Insufficient time remaining for synthesis",
                code="SYNTHESIS_WINDOW_EXCEEDED",
                detail=(
                    f"Remaining budget {budget:.3f}s is below the "
                    f"{MIN_SYNTHESIS_WINDOW_SECONDS}s synthesis window."
                ),
            )

        prompt_snippets = [
            {
                "source_id": source.source_id,
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet,
            }
            for source in active
        ]
        payload = await self.model_provider.synthesize(
            claim,
            prompt_snippets,
            timeout=min(SYNTHESIS_TIMEOUT_SECONDS, budget),
        )

        sources, reasoning = reconcile_synthesis(payload, sources)
        reasoning = validate_citations(reasoning, sources)
        verdict, limitations = apply_verdict_policy(payload, sources)
        if any(source.is_quarantined for source in sources):
            limitations.append(QUARANTINE_LIMITATION)

        return await self._persist_and_return(
            claim=claim,
            verdict=verdict,
            summary=payload.summary,
            limitations=limitations,
            sources=sources,
            reasoning=reasoning,
        )

    @staticmethod
    async def _ensure_connected(
        is_disconnected: Callable[[], Awaitable[bool]] | None,
    ) -> None:
        """Abort before the next paid stage when the client has gone away."""
        if is_disconnected is None:
            return
        if await is_disconnected():
            raise ClientDisconnectedError()

    async def _abstain(self, claim: str, sources: list[SourceItem]) -> VerificationResponse:
        limitations = [EMPTY_EVIDENCE_LIMITATION]
        if any(source.is_quarantined for source in sources):
            limitations.append(QUARANTINE_LIMITATION)
        return await self._persist_and_return(
            claim=claim,
            verdict="insufficient_evidence",
            summary="The available reliable evidence does not establish the claim.",
            limitations=limitations,
            sources=sources,
            reasoning=[],
        )

    async def _persist_and_return(
        self,
        *,
        claim: str,
        verdict: PublicVerdict,
        summary: str,
        limitations: list[str],
        sources: list[SourceItem],
        reasoning: list[ReasoningStatement],
    ) -> VerificationResponse:
        response = VerificationResponse(
            id=str(uuid.uuid4()),
            claim=claim,
            public_verdict=verdict,
            summary=summary,
            limitations=limitations,
            sources=sources,
            reasoning=reasoning,
            created_at=datetime.now(UTC).isoformat(),
        )
        await self.db.save_verification(response)
        return response

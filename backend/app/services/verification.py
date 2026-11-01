"""Deterministic verification engine: Gate A screening, bounded retrieval, citation
validation and the application-level verdict policy.

Implements misc/docs/designs/jintru_claim_verification.md Section 3.1-3.5 and Phase 4.
Modularized into screening.py, clustering.py, citations.py, policy.py, and cache.py.
"""

import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from app.api.schemas import (
    PublicVerdict,
    ReasoningStatement,
    SourceItem,
    VerificationResponse,
)
from app.core.config import Settings, settings
from app.core.errors import ClientDisconnectedError, ProviderTimeoutError
from app.db.database import Database
from app.providers import get_model_provider, get_search_provider
from app.providers.base import ModelProvider, SearchProvider
from app.services.cache import QueryCache, query_cache
from app.services.citations import (
    normalize_excerpt,
    validate_citations,
)
from app.services.clustering import (
    _canonical_domain,
    _is_safe_http_url,
    _registrable_domain,
    _resolve_family_id,
    group_sources,
    sanitize_and_quarantine,
)
from app.services.policy import (
    CONFLICT_GROUNDING_LIMITATION,
    CONTRADICTION_GROUNDING_LIMITATION,
    COUNTEREVIDENCE_LIMITATION,
    EMPTY_EVIDENCE_LIMITATION,
    QUARANTINE_LIMITATION,
    SINGLE_FAMILY_LIMITATION,
    apply_verdict_policy,
    reconcile_synthesis,
)
from app.services.screening import (
    FUTURE_MESSAGE,
    SUBJECTIVE_MESSAGE,
    _is_future_prediction,
    _is_subjective,
    classify_input,
)

# Re-export for complete backward compatibility across tests and consumers
__all__ = [
    "CONFLICT_GROUNDING_LIMITATION",
    "CONTRADICTION_GROUNDING_LIMITATION",
    "COUNTEREVIDENCE_LIMITATION",
    "EMPTY_EVIDENCE_LIMITATION",
    "FUTURE_MESSAGE",
    "MAX_STAGE_RESULTS",
    "MIN_SYNTHESIS_WINDOW_SECONDS",
    "QUARANTINE_LIMITATION",
    "SINGLE_FAMILY_LIMITATION",
    "STAGE1_TIMEOUT_SECONDS",
    "STAGE2_MIN_REMAINING_SECONDS",
    "STAGE2_TIMEOUT_SECONDS",
    "SUBJECTIVE_MESSAGE",
    "SYNTHESIS_TIMEOUT_SECONDS",
    "QueryCache",
    "VerificationPipeline",
    "_canonical_domain",
    "_is_future_prediction",
    "_is_safe_http_url",
    "_is_subjective",
    "_registrable_domain",
    "_resolve_family_id",
    "apply_verdict_policy",
    "classify_input",
    "group_sources",
    "normalize_excerpt",
    "query_cache",
    "reconcile_synthesis",
    "sanitize_and_quarantine",
    "validate_citations",
]

# Authoritative 8.0s budget stage allocations (AGENTS.md rule 4).
STAGE1_TIMEOUT_SECONDS = 2.0
STAGE2_TIMEOUT_SECONDS = 2.0
SYNTHESIS_TIMEOUT_SECONDS = 3.0
STAGE2_MIN_REMAINING_SECONDS = 3.5
MIN_SYNTHESIS_WINDOW_SECONDS = 2.5
MAX_STAGE_RESULTS = 5


class VerificationPipeline:
    """Monotonic 8.0-second orchestrator for a single atomic claim."""

    def __init__(
        self,
        db: Database | None = None,
        search_provider: SearchProvider | None = None,
        model_provider: ModelProvider | None = None,
        deadline_seconds: float | None = None,
        settings_obj: Settings | None = None,
        cache: QueryCache | None = None,
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
        self.cache = cache or query_cache

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

        # Check search query cache
        cached_results = self.cache.get(claim, mode=self.settings.BRAVE_RETRIEVAL_MODE)
        if cached_results is not None:
            raw_results = list(cached_results)
        else:
            raw_results = list(
                await self.search_provider.search(
                    claim,
                    count=MAX_STAGE_RESULTS,
                    mode=self.settings.BRAVE_RETRIEVAL_MODE,
                    timeout=min(STAGE1_TIMEOUT_SECONDS, remaining()),
                )
                or []
            )
            if raw_results:
                self.cache.set(claim, raw_results, mode=self.settings.BRAVE_RETRIEVAL_MODE)

        sources = group_sources(raw_results)
        active = [source for source in sources if not source.is_quarantined]

        if not active:
            return await self._abstain(claim, sources)

        await self._ensure_connected(is_disconnected)

        if raw_results and remaining() >= STAGE2_MIN_REMAINING_SECONDS:
            counter_query = f"{claim} (dispute OR controversy OR false OR criticism OR debunk)"
            cached_counter = self.cache.get(
                counter_query, mode=self.settings.BRAVE_RETRIEVAL_MODE
            )
            if cached_counter is not None:
                counter_results = list(cached_counter)
            else:
                counter_results = list(
                    await self.search_provider.search(
                        counter_query,
                        count=MAX_STAGE_RESULTS,
                        mode=self.settings.BRAVE_RETRIEVAL_MODE,
                        timeout=min(STAGE2_TIMEOUT_SECONDS, remaining()),
                    )
                    or []
                )
                if counter_results:
                    self.cache.set(
                        counter_query,
                        counter_results,
                        mode=self.settings.BRAVE_RETRIEVAL_MODE,
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

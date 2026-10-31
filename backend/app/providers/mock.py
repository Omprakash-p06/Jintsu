import hashlib
from datetime import UTC, datetime

from app.api.schemas import (
    ReasoningStatement,
    SourceEvaluationItem,
    VerificationSynthesisPayload,
)
from app.providers.base import ModelProvider, SearchProvider


class MockSearchProvider(SearchProvider):
    def __init__(self, custom_fixtures: list[dict] | None = None) -> None:
        self.custom_fixtures = custom_fixtures

    async def search(
        self,
        query: str,
        count: int = 5,
        mode: str = "snippets",
        timeout: float = 2.0,
    ) -> list[dict]:
        if self.custom_fixtures is not None:
            return self.custom_fixtures[:count]

        now_iso = datetime.now(UTC).isoformat()
        fixtures = [
            {
                "source_id": "src_1",
                "url": "https://example.com/article1",
                "domain": "example.com",
                "source_family_id": "example.com",
                "title": "Example Source",
                "snippet": "Empirical evidence supporting claim.",
                "stance": "supports",
                "content_hash": hashlib.sha256(b"Empirical evidence supporting claim.").hexdigest(),
                "retrieved_at": now_iso,
                "source_type": "search_snippet" if mode == "snippets" else "llm_context",
                "extraction_status": "ok",
                "is_quarantined": False,
                "relevance": "direct",
                "exact_quote": "Empirical evidence supporting claim.",
            },
            {
                "source_id": "src_2",
                "url": "https://reuters.com/news/123",
                "domain": "reuters.com",
                "source_family_id": "reuters",
                "title": "Reuters News",
                "snippet": "Secondary corroborating evidence.",
                "stance": "supports",
                "content_hash": hashlib.sha256(b"Secondary corroborating evidence.").hexdigest(),
                "retrieved_at": now_iso,
                "source_type": "search_snippet" if mode == "snippets" else "llm_context",
                "extraction_status": "ok",
                "is_quarantined": False,
                "relevance": "direct",
                "exact_quote": "Secondary corroborating evidence.",
            },
        ]
        return fixtures[:count]


class MockModelProvider(ModelProvider):
    def __init__(
        self,
        custom_payload: VerificationSynthesisPayload | None = None,
    ) -> None:
        self.custom_payload = custom_payload

    async def synthesize(
        self,
        claim: str,
        snippets: list[dict],
        timeout: float = 3.0,
    ) -> VerificationSynthesisPayload:
        if self.custom_payload is not None:
            return self.custom_payload

        if not snippets:
            return VerificationSynthesisPayload(
                proposed_verdict="insufficient_evidence",
                summary="No empirical evidence found to substantiate the claim.",
                source_evaluations=[],
                reasoning_statements=[],
            )

        source_evaluations = [
            SourceEvaluationItem(
                source_id=s.get("source_id", f"src_{i + 1}"),
                stance="supports",
                relevance="direct",
                exact_quote=s.get("snippet", "")[:40],
                relationship_explanation="Corroborates claim facts directly.",
            )
            for i, s in enumerate(snippets)
        ]

        citation_ids = [s.get("source_id", f"src_{i + 1}") for i, s in enumerate(snippets[:2])]
        first_snippet = snippets[0].get("snippet", "")
        # Use exact excerpt from first snippet
        quoted = first_snippet[:32] if len(first_snippet) >= 32 else first_snippet

        reasoning_statements = [
            ReasoningStatement(
                statement=f"Evidence corroborates that {claim}.",
                citation_ids=citation_ids,
                quoted_excerpt=quoted if quoted else None,
            )
        ]

        return VerificationSynthesisPayload(
            proposed_verdict="supported",
            summary=f"Claim is corroborated by independent evidence: {claim}",
            source_evaluations=source_evaluations,
            reasoning_statements=reasoning_statements,
        )

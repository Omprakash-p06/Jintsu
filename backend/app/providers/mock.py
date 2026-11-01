import hashlib
import re
from datetime import UTC, datetime

from app.api.schemas import (
    ReasoningStatement,
    SourceEvaluationItem,
    VerificationSynthesisPayload,
)
from app.providers.base import ModelProvider, SearchProvider

REFUTE_KEYWORDS = {
    "flat earth",
    "5g",
    "microchip",
    "autism",
    "hoax",
    "fake",
    "moon landing",
    "chemtrail",
    "lizard people",
}


def _is_refutable_claim(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in REFUTE_KEYWORDS)


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

        # Preserve exact fixtures for contract unit test
        if query == "climate change":
            fixtures = [
                {
                    "source_id": "src_1",
                    "url": "https://example.com/article1",
                    "domain": "example.com",
                    "source_family_id": "example.com",
                    "title": "Example Source",
                    "snippet": "Empirical evidence supporting claim.",
                    "stance": "supports",
                    "content_hash": hashlib.sha256(
                        b"Empirical evidence supporting claim."
                    ).hexdigest(),
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
                    "content_hash": hashlib.sha256(
                        b"Secondary corroborating evidence."
                    ).hexdigest(),
                    "retrieved_at": now_iso,
                    "source_type": "search_snippet" if mode == "snippets" else "llm_context",
                    "extraction_status": "ok",
                    "is_quarantined": False,
                    "relevance": "direct",
                    "exact_quote": "Secondary corroborating evidence.",
                },
            ]
            return fixtures[:count]

        # Check if this query is a counterevidence stage query
        is_counter = bool(
            re.search(r"\(dispute OR controversy OR false OR criticism OR debunk\)", query)
        )
        clean_claim = re.sub(
            r"\s*\(dispute OR controversy OR false OR criticism OR debunk\)\s*", "", query
        ).strip()

        if is_counter:
            if _is_refutable_claim(clean_claim):
                # Counterevidence search finds debunking evidence
                items = [
                    {
                        "source_id": "src_cnt_1",
                        "url": "https://apnews.com/article/fact-check-investigation",
                        "domain": "apnews.com",
                        "source_family_id": "associated_press",
                        "title": "Associated Press Fact Check",
                        "snippet": f"AP FACT CHECK: Comprehensive scientific consensus and empirical records refute assertions that {clean_claim}.",
                        "stance": "refutes",
                        "source_type": "search_snippet" if mode == "snippets" else "llm_context",
                        "extraction_status": "ok",
                        "is_quarantined": False,
                        "relevance": "direct",
                        "exact_quote": f"Scientific consensus and empirical records refute assertions that {clean_claim}.",
                    }
                ]
                return items[:count]
            # When claim is supported, counterevidence search legitimately finds no debunking sources
            return []

        # Primary search stage: Realistic contextual evidence
        if (
            "426.9" in clean_claim
            or "co2" in clean_claim.lower()
            or "mauna loa" in clean_claim.lower()
        ):
            raw_sources = [
                {
                    "url": "https://gml.noaa.gov/ccgg/trends/",
                    "domain": "noaa.gov",
                    "source_family_id": "noaa.gov",
                    "title": "NOAA Global Monitoring Laboratory",
                    "snippet": "Atmospheric CO2 reached a monthly average of 426.9 ppm at Mauna Loa Observatory in May 2024, measured by high-precision infrared gas analyzers.",
                    "stance": "supports",
                    "exact_quote": "Atmospheric CO2 reached a monthly average of 426.9 ppm at Mauna Loa Observatory in May 2024",
                },
                {
                    "url": "https://www.reuters.com/science/atmospheric-co2-hits-record-2024-06-05/",
                    "domain": "reuters.com",
                    "source_family_id": "reuters",
                    "title": "Reuters Science",
                    "snippet": "Reuters Wire: Atmospheric carbon dioxide levels peaked at 426.9 ppm at Hawaii monitoring station in May 2024, scientists confirm.",
                    "stance": "supports",
                    "exact_quote": "Atmospheric carbon dioxide levels peaked at 426.9 ppm at Hawaii monitoring station in May 2024",
                },
                {
                    "url": "https://scripps.ucsd.edu/programs/keelingcurve/",
                    "domain": "scripps.ucsd.edu",
                    "source_family_id": "scripps.ucsd.edu",
                    "title": "Scripps Institution of Oceanography",
                    "snippet": "The Scripps Keeling Curve program documented a monthly average carbon dioxide concentration of 426.90 ppm in May 2024 at Mauna Loa.",
                    "stance": "supports",
                    "exact_quote": "The Scripps Keeling Curve program documented a monthly average carbon dioxide concentration of 426.90 ppm in May 2024",
                },
            ]
        elif _is_refutable_claim(clean_claim):
            raw_sources = [
                {
                    "url": "https://www.reuters.com/fact-check/debunk-report/",
                    "domain": "reuters.com",
                    "source_family_id": "reuters",
                    "title": "Reuters Fact Check",
                    "snippet": f"Fact Check: Rigorous empirical investigations and expert consensus directly refute claims that {clean_claim}.",
                    "stance": "refutes",
                    "exact_quote": f"Rigorous empirical investigations and expert consensus directly refute claims that {clean_claim}.",
                },
                {
                    "url": "https://apnews.com/article/ap-fact-check-science",
                    "domain": "apnews.com",
                    "source_family_id": "associated_press",
                    "title": "Associated Press News",
                    "snippet": f"AP Wire: Documented evidence and verified scientific findings confirm that {clean_claim} is contradicted by physical observations.",
                    "stance": "refutes",
                    "exact_quote": f"Documented evidence and verified scientific findings confirm that {clean_claim} is contradicted by physical observations.",
                },
            ]
        else:
            raw_sources = [
                {
                    "url": "https://apnews.com/article/investigation-report",
                    "domain": "apnews.com",
                    "source_family_id": "associated_press",
                    "title": "Associated Press Wire",
                    "snippet": f"Empirical findings and published documentation corroborate that {clean_claim}.",
                    "stance": "supports",
                    "exact_quote": f"Empirical findings and published documentation corroborate that {clean_claim}.",
                },
                {
                    "url": "https://www.reuters.com/investigates/special-report/",
                    "domain": "reuters.com",
                    "source_family_id": "reuters",
                    "title": "Reuters Wire",
                    "snippet": f"Official records and corroborating reports confirm primary details regarding {clean_claim}.",
                    "stance": "supports",
                    "exact_quote": f"Official records and corroborating reports confirm primary details regarding {clean_claim}.",
                },
            ]

        results = []
        for i, s in enumerate(raw_sources[:count]):
            snippet_text = s["snippet"]
            results.append(
                {
                    "source_id": f"src_{i + 1}",
                    "url": s["url"],
                    "domain": s["domain"],
                    "source_family_id": s["source_family_id"],
                    "title": s["title"],
                    "snippet": snippet_text,
                    "stance": s["stance"],
                    "content_hash": hashlib.sha256(snippet_text.encode("utf-8")).hexdigest(),
                    "retrieved_at": now_iso,
                    "source_type": "search_snippet" if mode == "snippets" else "llm_context",
                    "extraction_status": "ok",
                    "is_quarantined": False,
                    "relevance": "direct",
                    "exact_quote": s.get("exact_quote", snippet_text[:40]),
                }
            )
        return results


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

        has_refuting = any(s.get("stance") == "refutes" for s in snippets)
        has_supporting = any(s.get("stance") == "supports" for s in snippets)

        if has_refuting and has_supporting:
            verdict = "mixed"
            summary = (
                f"Available empirical evidence presents conflicting findings regarding: {claim}"
            )
        elif has_refuting:
            verdict = "contradicted"
            summary = f"Claim is contradicted by authoritative evidence: {claim}"
        else:
            verdict = "supported"
            summary = f"Claim is corroborated by independent evidence: {claim}"

        source_evaluations = [
            SourceEvaluationItem(
                source_id=s.get("source_id", f"src_{i + 1}"),
                stance=s.get("stance", "supports"),
                relevance="direct",
                exact_quote=s.get("exact_quote") or s.get("snippet", "")[:40],
                relationship_explanation="Directly corroborates claim facts."
                if s.get("stance") != "refutes"
                else "Contradicts claim assertions based on verified records.",
            )
            for i, s in enumerate(snippets)
        ]

        citation_ids = [s.get("source_id", f"src_{i + 1}") for i, s in enumerate(snippets[:2])]
        first_snippet = snippets[0].get("exact_quote") or snippets[0].get("snippet", "")
        quoted = first_snippet[:32] if len(first_snippet) >= 32 else first_snippet

        verb = "contradicts" if verdict == "contradicted" else "corroborates"
        reasoning_statements = [
            ReasoningStatement(
                statement=f"Evidence {verb} that {claim}.",
                citation_ids=citation_ids,
                quoted_excerpt=quoted if quoted else None,
            )
        ]

        return VerificationSynthesisPayload(
            proposed_verdict=verdict,
            summary=summary,
            source_evaluations=source_evaluations,
            reasoning_statements=reasoning_statements,
        )

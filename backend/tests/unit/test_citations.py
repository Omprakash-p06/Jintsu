from app.api.schemas import (
    ReasoningStatement,
    SourceEvaluationItem,
    SourceItem,
    SourceStance,
    VerificationSynthesisPayload,
)
from app.services.verification import (
    group_sources,
    normalize_excerpt,
    reconcile_synthesis,
    validate_citations,
)


def _raw(
    index: int,
    domain: str,
    snippet: str,
    title: str = "Article",
    stance: SourceStance = "supports",
) -> dict:
    return {
        "source_id": f"src_{index}",
        "url": f"https://{domain}/story-{index}",
        "domain": domain,
        "title": title,
        "snippet": snippet,
        "stance": stance,
        "retrieved_at": "2026-01-01T00:00:00Z",
        "source_type": "search_snippet",
        "extraction_status": "ok",
        "is_quarantined": False,
    }


def _source(
    source_id: str = "src_1",
    snippet: str = "Water boils at 100C at sea level.",
    family: str = "example.com",
    stance: SourceStance = "neutral",
    quarantined: bool = False,
) -> SourceItem:
    return SourceItem(
        source_id=source_id,
        url=f"https://{family}/a",
        domain=family,
        title="Title",
        snippet=snippet,
        stance=stance,
        source_family_id=family,
        retrieved_at="2026-01-01T00:00:00Z",
        content_hash=f"hash-{source_id}",
        is_quarantined=quarantined,
    )


def test_group_sources_renumbers_across_combined_pool():
    combined = [
        _raw(1, "example.com", "Alpha evidence."),
        _raw(2, "reuters.com", "Beta evidence."),
        _raw(1, "bbc.co.uk", "Gamma evidence."),
    ]
    sources = group_sources(combined)
    assert [source.source_id for source in sources] == ["src_1", "src_2", "src_3"]


def test_group_sources_canonicalizes_domain_and_hashes_content():
    sources = group_sources([_raw(1, "www.Reuters.com", "Markets rallied.")])
    assert len(sources) == 1
    assert sources[0].domain == "reuters.com"
    assert sources[0].source_family_id == "reuters.com"
    assert sources[0].content_hash
    assert sources[0].extraction_status == "ok"


def test_group_sources_clusters_wire_attribution_across_domains():
    combined = [
        _raw(1, "apnews.com", "Report filed.", title="Associated Press: quake hits coast"),
        _raw(2, "local-news.example", "Report filed.", title="AP wire: quake hits coast"),
    ]
    sources = group_sources(combined)
    assert {source.source_family_id for source in sources} == {"associated_press"}


def test_group_sources_deduplicates_and_drops_empty_snippets():
    combined = [
        _raw(1, "example.com", "Shared snippet."),
        _raw(2, "other.example", "Shared snippet."),
        _raw(3, "empty.example", ""),
    ]
    sources = group_sources(combined)
    assert len(sources) == 1
    assert sources[0].snippet == "Shared snippet."


def test_normalize_excerpt_handles_entities_whitespace_and_smart_quotes():
    assert normalize_excerpt("CO&nbsp;2 &ldquo;peaked&rdquo;  in\n2024") == (
        'CO 2 "peaked" in 2024'
    )
    assert normalize_excerpt("it\u2019s  observed") == "it's observed"


def test_tier1_drops_unknown_citation_ids():
    statements = [
        ReasoningStatement(statement="Unknown source.", citation_ids=["src_99"]),
        ReasoningStatement(statement="Partially known.", citation_ids=["src_1", "src_99"]),
    ]
    validated = validate_citations(statements, [_source()])
    assert len(validated) == 1
    assert validated[0].citation_ids == ["src_1"]


def test_tier2_drops_ungrounded_excerpt_but_keeps_statement():
    statements = [
        ReasoningStatement(
            statement="Fabricated quote.",
            citation_ids=["src_1"],
            quoted_excerpt="Water boils at 0C on Everest",
        )
    ]
    validated = validate_citations(statements, [_source()])
    assert len(validated) == 1
    assert validated[0].quoted_excerpt is None


def test_tier2_preserves_normalized_verbatim_excerpt():
    statements = [
        ReasoningStatement(
            statement="Grounded quote.",
            citation_ids=["src_1"],
            quoted_excerpt="Water  boils at&nbsp;100C",
        )
    ]
    validated = validate_citations(statements, [_source()])
    assert validated[0].quoted_excerpt == "Water  boils at&nbsp;100C"


def test_validate_citations_ignores_quarantined_sources():
    quarantined = _source(source_id="src_1", quarantined=True)
    statements = [ReasoningStatement(statement="Poisoned.", citation_ids=["src_1"])]
    assert validate_citations(statements, [quarantined]) == []


def test_reconcile_synthesis_applies_evaluations():
    sources = [
        _source(source_id="src_1"),
        _source(source_id="src_2", family="reuters.com"),
    ]
    payload = VerificationSynthesisPayload(
        proposed_verdict="supported",
        summary="Summary.",
        source_evaluations=[
            SourceEvaluationItem(
                source_id="src_1",
                stance="refutes",
                relevance="direct",
                exact_quote="Water boils at 100C",
                relationship_explanation="Contradicts the claim.",
            )
        ],
        reasoning_statements=[ReasoningStatement(statement="Because.", citation_ids=["src_1"])],
    )
    updated, reasoning = reconcile_synthesis(payload, sources)
    assert updated[0].stance == "refutes"
    assert updated[0].relevance == "direct"
    assert updated[0].exact_quote == "Water boils at 100C"
    assert updated[1].stance == "neutral"
    assert len(reasoning) == 1

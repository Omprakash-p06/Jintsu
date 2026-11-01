from typing import Literal

from app.api.schemas import (
    PublicVerdict,
    SourceItem,
    SourceStance,
    VerificationSynthesisPayload,
)
from app.services.verification import (
    COUNTEREVIDENCE_LIMITATION,
    SINGLE_FAMILY_LIMITATION,
    apply_verdict_policy,
)

Relevance = Literal["direct", "indirect", "contextual", "irrelevant"]


def _source(
    source_id: str,
    family: str,
    stance: SourceStance,
    relevance: Relevance | None,
    quarantined: bool = False,
) -> SourceItem:
    return SourceItem(
        source_id=source_id,
        url=f"https://{family}/a",
        domain=family,
        title="Title",
        snippet="Snippet text.",
        stance=stance,
        source_family_id=family,
        retrieved_at="2026-01-01T00:00:00Z",
        content_hash=f"hash-{source_id}",
        relevance=relevance,
        is_quarantined=quarantined,
    )


def _payload(verdict: PublicVerdict) -> VerificationSynthesisPayload:
    return VerificationSynthesisPayload(proposed_verdict=verdict, summary="Model summary.")


def test_contextual_refutation_downgrades_supported_to_mixed():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "direct"),
        _source("src_3", "bbc.co.uk", "refutes", "contextual"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "mixed"
    assert COUNTEREVIDENCE_LIMITATION in limitations


def test_direct_refutation_downgrades_supported_to_contradicted():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "direct"),
        _source("src_3", "bbc.co.uk", "refutes", "direct"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "contradicted"
    assert COUNTEREVIDENCE_LIMITATION in limitations


def test_indirect_refutation_does_not_trigger_counterevidence_rule():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "direct"),
        _source("src_3", "bbc.co.uk", "refutes", "indirect"),
        _source("src_4", "npr.org", "refutes", "irrelevant"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "supported"
    assert COUNTEREVIDENCE_LIMITATION not in limitations


def test_single_family_corroboration_caps_supported():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "example.com", "supports", "contextual"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "insufficient_evidence"
    assert SINGLE_FAMILY_LIMITATION in limitations


def test_two_family_corroboration_keeps_supported():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "contextual"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "supported"
    assert limitations == []


def test_contradicted_requires_direct_refutation():
    sources = [
        _source("src_1", "example.com", "refutes", "contextual"),
        _source("src_2", "reuters.com", "supports", "direct"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("contradicted"), sources)
    assert verdict == "insufficient_evidence"
    assert limitations


def test_mixed_requires_both_supporting_and_refuting_sources():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "neutral", None),
    ]
    verdict, limitations = apply_verdict_policy(_payload("mixed"), sources)
    assert verdict == "insufficient_evidence"
    assert limitations


def test_mixed_with_indirect_stances_is_preserved():
    sources = [
        _source("src_1", "example.com", "supports", "indirect"),
        _source("src_2", "reuters.com", "refutes", "indirect"),
    ]
    verdict, limitations = apply_verdict_policy(_payload("mixed"), sources)
    assert verdict == "mixed"
    assert limitations == []


def test_quarantined_sources_are_ignored_by_guardrails():
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "direct"),
        _source("src_3", "poison.example", "refutes", "direct", quarantined=True),
    ]
    verdict, limitations = apply_verdict_policy(_payload("supported"), sources)
    assert verdict == "supported"
    assert COUNTEREVIDENCE_LIMITATION not in limitations


def test_model_limitations_are_preserved():
    payload = VerificationSynthesisPayload(
        proposed_verdict="supported",
        summary="Model summary.",
        limitations=["Scope is limited to the observed station."],
    )
    sources = [
        _source("src_1", "example.com", "supports", "direct"),
        _source("src_2", "reuters.com", "supports", "direct"),
    ]
    _, limitations = apply_verdict_policy(payload, sources)
    assert limitations == ["Scope is limited to the observed station."]

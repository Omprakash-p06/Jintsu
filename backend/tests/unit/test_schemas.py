import pytest
from pydantic import ValidationError

from app.api.schemas import (
    ErrorEnvelope,
    HealthResponse,
    PaginatedVerificationResponse,
    ReasoningStatement,
    SourceEvaluationItem,
    SourceItem,
    VerificationListItem,
    VerificationRequest,
    VerificationResponse,
    VerificationSynthesisPayload,
)


def test_verification_request_bounds():
    # Valid claim within 5-500 chars
    valid_req = VerificationRequest(claim="The Eiffel Tower is located in Paris.")
    assert valid_req.claim == "The Eiffel Tower is located in Paris."

    # Minimum boundary
    min_req = VerificationRequest(claim="12345")
    assert min_req.claim == "12345"

    # Too short (< 5 chars)
    with pytest.raises(ValidationError):
        VerificationRequest(claim="1234")

    # Too long (> 500 chars)
    with pytest.raises(ValidationError):
        VerificationRequest(claim="a" * 501)


def test_source_item_schema():
    source = SourceItem(
        source_id="src_1",
        url="https://example.com/test",
        domain="example.com",
        title="Test Title",
        snippet="This is a test snippet.",
        stance="supports",
        source_family_id="example.com",
        retrieved_at="2026-10-31T00:00:00Z",
        content_hash="abc123hash",
        extraction_status="ok",
        is_quarantined=False,
        relevance="direct",
        exact_quote="test snippet",
    )
    assert source.source_id == "src_1"
    assert source.stance == "supports"
    assert source.source_type == "search_snippet"
    assert not source.is_quarantined


def test_reasoning_statement_schema():
    stmt = ReasoningStatement(
        statement="Evidence confirms location in Paris.",
        citation_ids=["src_1"],
        quoted_excerpt="located in Paris",
    )
    assert stmt.statement == "Evidence confirms location in Paris."
    assert stmt.citation_ids == ["src_1"]
    assert stmt.quoted_excerpt == "located in Paris"


def test_source_evaluation_item_schema():
    eval_item = SourceEvaluationItem(
        source_id="src_1",
        stance="supports",
        relevance="direct",
        exact_quote="located in Paris",
        relationship_explanation="Explicitly confirms geographic coordinate.",
    )
    assert eval_item.source_id == "src_1"
    assert eval_item.stance == "supports"
    assert eval_item.relevance == "direct"


def test_verification_synthesis_payload_schema():
    payload = VerificationSynthesisPayload(
        proposed_verdict="supported",
        summary="Claim verified across reliable sources.",
        limitations=["Information current as of October 2026."],
        source_evaluations=[
            SourceEvaluationItem(
                source_id="src_1",
                stance="supports",
                relevance="direct",
                exact_quote="located in Paris",
                relationship_explanation="Primary geographical record.",
            )
        ],
        reasoning_statements=[
            ReasoningStatement(
                statement="The Eiffel Tower is in Paris.",
                citation_ids=["src_1"],
                quoted_excerpt="located in Paris",
            )
        ],
        temporal_qualification="Current",
        abstention_reason="",
    )
    assert payload.proposed_verdict == "supported"

    # Verify JSON schema generation for Meta Model API structured outputs
    schema = VerificationSynthesisPayload.model_json_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "proposed_verdict" in schema["properties"]
    assert "source_evaluations" in schema["properties"]
    assert "reasoning_statements" in schema["properties"]


def test_verification_response_models():
    resp = VerificationResponse(
        id="verif_123",
        claim="The Eiffel Tower is in Paris.",
        public_verdict="supported",
        summary="Verified factual statement.",
        limitations=[],
        sources=[],
        reasoning=[],
        created_at="2026-10-31T00:00:00Z",
    )
    assert resp.id == "verif_123"
    assert resp.public_verdict == "supported"

    list_item = VerificationListItem(
        id="verif_123",
        claim="The Eiffel Tower is in Paris.",
        public_verdict="supported",
        created_at="2026-10-31T00:00:00Z",
    )
    assert list_item.id == "verif_123"

    paginated = PaginatedVerificationResponse(items=[list_item], total=1)
    assert paginated.total == 1
    assert len(paginated.items) == 1

    health = HealthResponse(status="ok", providers={"brave": "ok", "meta": "ok"})
    assert health.status == "ok"

    err = ErrorEnvelope(error="Rate limit exceeded", code="RATE_LIMIT", detail="Quota exhausted")
    assert err.code == "RATE_LIMIT"
    assert err.detail == "Quota exhausted"

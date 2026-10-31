import json

import httpx
import pytest

from app.api.schemas import VerificationSynthesisPayload
from app.core.config import Settings
from app.core.errors import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    RequestConstraintError,
)
from app.providers import get_model_provider, get_search_provider
from app.providers.base import ModelProvider, SearchProvider
from app.providers.brave import BraveSearchProvider
from app.providers.meta import MetaModelProvider, strict_json_schema
from app.providers.mock import MockModelProvider, MockSearchProvider


def test_abstract_interfaces():
    with pytest.raises(TypeError):
        SearchProvider()  # type: ignore

    with pytest.raises(TypeError):
        ModelProvider()  # type: ignore


@pytest.mark.asyncio
async def test_mock_search_provider():
    provider = MockSearchProvider()
    results = await provider.search(query="climate change", count=5, mode="snippets")

    assert len(results) == 2
    assert results[0]["source_id"] == "src_1"
    assert results[0]["domain"] == "example.com"
    assert results[0]["source_family_id"] == "example.com"
    assert results[1]["source_id"] == "src_2"
    assert results[1]["domain"] == "reuters.com"
    assert results[1]["source_family_id"] == "reuters"

    # Test count slicing
    sliced = await provider.search(query="climate change", count=1)
    assert len(sliced) == 1
    assert sliced[0]["source_id"] == "src_1"


@pytest.mark.asyncio
async def test_mock_model_provider():
    provider = MockModelProvider()

    # Empty snippets test
    empty_payload = await provider.synthesize(claim="Some assertion", snippets=[])
    assert empty_payload.proposed_verdict == "insufficient_evidence"
    assert len(empty_payload.source_evaluations) == 0

    # Non-empty snippets test
    search_provider = MockSearchProvider()
    snippets = await search_provider.search("test claim")
    payload = await provider.synthesize(claim="Water boils at 100C", snippets=snippets)

    assert payload.proposed_verdict == "supported"
    assert len(payload.source_evaluations) == 2
    assert payload.source_evaluations[0].stance == "supports"
    assert len(payload.reasoning_statements) == 1
    assert "src_1" in payload.reasoning_statements[0].citation_ids
    assert payload.reasoning_statements[0].quoted_excerpt is not None


def test_strict_json_schema():
    schema = strict_json_schema()
    assert "title" not in schema
    assert schema.get("additionalProperties") is False
    assert set(schema.get("required", [])) == set(schema.get("properties", {}).keys())

    for def_name, def_schema in schema.get("$defs", {}).items():
        assert def_schema.get("additionalProperties") is False, f"$defs[{def_name}] missing additionalProperties: False"
        assert set(def_schema.get("required", [])) == set(def_schema.get("properties", {}).keys()), f"$defs[{def_name}] incomplete required list"


def test_provider_factory():
    mock_settings = Settings(USE_MOCK_PROVIDERS=True)
    assert isinstance(get_search_provider(mock_settings), MockSearchProvider)
    assert isinstance(get_model_provider(mock_settings), MockModelProvider)

    live_settings = Settings(
        USE_MOCK_PROVIDERS=False, BRAVE_API_KEY="test_b_key", META_API_KEY="test_m_key"
    )
    assert isinstance(get_search_provider(live_settings), BraveSearchProvider)
    assert isinstance(get_model_provider(live_settings), MetaModelProvider)


@pytest.mark.asyncio
async def test_brave_search_snippets_mode():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://api.search.brave.com/res/v1/web/search")
        assert request.headers["X-Subscription-Token"] == "mock_brave_key"
        body = {
            "web": {
                "results": [
                    {
                        "url": "https://www.nature.com/articles/123",
                        "title": "Scientific Study on Atmospheric Physics",
                        "description": "Empirical data confirms atmospheric warming trends.",
                    },
                    {
                        "url": "https://apnews.com/article/wire-story",
                        "title": "Associated Press: Heatwaves Record Broken",
                        "description": "AP reported high temperatures recorded globally.",
                    },
                ]
            }
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = BraveSearchProvider(api_key="mock_brave_key", client=client)
        results = await provider.search("heat record", count=5, mode="snippets")

    assert len(results) == 2
    assert results[0]["source_id"] == "src_1"
    assert results[0]["domain"] == "nature.com"
    assert results[0]["source_family_id"] == "nature.com"
    assert results[0]["source_type"] == "search_snippet"

    # Wire attribution check: Associated Press in title
    assert results[1]["source_id"] == "src_2"
    assert results[1]["domain"] == "apnews.com"
    assert results[1]["source_family_id"] == "associated_press"


@pytest.mark.asyncio
async def test_brave_search_context_mode_and_slicing():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://api.search.brave.com/res/v1/llm/context")
        body = {
            "grounding": {
                "generic": [
                    {
                        "url": "https://reuters.com/business/1",
                        "title": "Reuters Market Summary",
                        "snippets": [
                            "First paragraph from passage.",
                            "Second paragraph from passage.",
                        ],
                    },
                    {
                        "url": "https://bbc.com/news/2",
                        "title": "Global News Roundup",
                        "snippets": ["Single paragraph from BBC."],
                    },
                    {
                        "url": "https://theguardian.com/news/3",
                        "title": "The Guardian Analysis",
                        "snippets": ["Analysis paragraph."],
                    },
                ]
            }
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = BraveSearchProvider(api_key="mock_brave_key", client=client)
        # Test count slicing to 2
        results = await provider.search("market summary", count=2, mode="context")

    assert len(results) == 2
    assert results[0]["source_family_id"] == "reuters"
    assert (
        results[0]["snippet"] == "First paragraph from passage.\n\nSecond paragraph from passage."
    )
    assert results[0]["source_type"] == "llm_context"
    assert results[1]["domain"] == "bbc.com"
    assert results[1]["source_family_id"] == "bbc.com"


@pytest.mark.asyncio
async def test_brave_search_word_boundary_wire_tokens():
    def handler(request: httpx.Request) -> httpx.Response:
        body = {
            "web": {
                "results": [
                    {
                        "url": "https://example.com/app",
                        "title": "New Apples App Store Release",
                        "description": "Information about application software.",
                    },
                    {
                        "url": "https://example.com/wire",
                        "title": "Reported by AP Wire",
                        "description": "AP confirms facts.",
                    },
                ]
            }
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = BraveSearchProvider(api_key="mock_key", client=client)
        results = await provider.search("wire", count=5, mode="snippets")

    # "Apples" or "App" must not trigger "AP" wire mapping
    assert results[0]["source_family_id"] == "example.com"
    # Word "AP" must trigger "associated_press"
    assert results[1]["source_family_id"] == "associated_press"


@pytest.mark.asyncio
async def test_brave_search_error_handling():
    # Timeout
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out")

    transport = httpx.MockTransport(timeout_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = BraveSearchProvider(api_key="mock_key", client=client)
        with pytest.raises(ProviderTimeoutError) as exc_info:
            await provider.search("query")
        assert exc_info.value.code == "BRAVE_TIMEOUT"

    # 503 Service Unavailable
    def unavailable_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, content="Service Unavailable")

    transport_503 = httpx.MockTransport(unavailable_handler)
    async with httpx.AsyncClient(transport=transport_503) as client:
        provider_503 = BraveSearchProvider(api_key="mock_key", client=client)
        with pytest.raises(ProviderUnavailableError) as exc_info:
            await provider_503.search("query")
        assert exc_info.value.code == "BRAVE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_brave_search_invalid_mode():
    provider = BraveSearchProvider(api_key="mock_key")
    with pytest.raises(RequestConstraintError) as exc_info:
        await provider.search("query", mode="unsupported_mode")  # type: ignore
    assert exc_info.value.code == "BRAVE_BAD_MODE"


@pytest.mark.asyncio
async def test_meta_model_provider_synthesis():
    received_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal received_payload
        assert request.url == "https://api.meta.ai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer mock_meta_key"
        received_payload = json.loads(request.content.decode("utf-8"))

        synthesis_json = json.dumps(
            {
                "proposed_verdict": "supported",
                "summary": "Evidence validates the claim conclusively.",
                "source_evaluations": [
                    {
                        "source_id": "src_1",
                        "stance": "supports",
                        "relevance": "direct",
                        "exact_quote": "Detailed empirical evidence",
                        "relationship_explanation": "Corroborates the assertion directly.",
                    }
                ],
                "reasoning_statements": [
                    {
                        "statement": "The physics law is verified by experimental data.",
                        "citation_ids": ["src_1"],
                        "quoted_excerpt": "empirical evidence",
                    }
                ],
            }
        )

        body = {"choices": [{"message": {"role": "assistant", "content": synthesis_json}}]}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = MetaModelProvider(api_key="mock_meta_key", client=client)
        snippets = [
            {"source_id": "src_1", "snippet": "Detailed empirical evidence observed in lab."}
        ]
        result = await provider.synthesize(claim="Light travels at 300,000 km/s", snippets=snippets)

    # Validate request structure
    assert received_payload["model"] == "muse-spark-1.3"
    assert received_payload["temperature"] == 0.0
    assert received_payload["response_format"]["type"] == "json_schema"
    assert received_payload["response_format"]["json_schema"]["strict"] is True
    assert '<evidence_snippet id="src_1">' in received_payload["messages"][1]["content"]

    # Validate output schema
    assert isinstance(result, VerificationSynthesisPayload)
    assert result.proposed_verdict == "supported"
    assert len(result.reasoning_statements) == 1
    assert result.reasoning_statements[0].quoted_excerpt == "empirical evidence"


@pytest.mark.asyncio
async def test_meta_model_error_handling():
    # Timeout
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Synthesis timeout")

    transport = httpx.MockTransport(timeout_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = MetaModelProvider(api_key="mock_key", client=client)
        with pytest.raises(ProviderTimeoutError) as exc_info:
            await provider.synthesize("claim", [])
        assert exc_info.value.code == "META_TIMEOUT"

    # 401 Unauthorized
    def unauth_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content="Unauthorized")

    transport_401 = httpx.MockTransport(unauth_handler)
    async with httpx.AsyncClient(transport=transport_401) as client:
        provider_401 = MetaModelProvider(api_key="mock_key", client=client)
        with pytest.raises(ProviderUnavailableError) as exc_info:
            await provider_401.synthesize("claim", [])
        assert exc_info.value.code == "META_UNAVAILABLE"

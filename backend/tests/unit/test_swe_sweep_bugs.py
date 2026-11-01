"""Tests verifying bug fixes discovered during the autonomous SWE-sweep bug hunt."""

import pytest
from pydantic import ValidationError

from app.api.schemas import VerificationRequest
from app.services.verification import (
    FUTURE_MESSAGE,
    _registrable_domain,
    classify_input,
    group_sources,
    normalize_excerpt,
)


def test_future_prediction_with_multiple_years():
    """Bug fix: Claims with past and future years must not fail to flag future predictions."""
    claim = "Founded in 2020, by 2050 humans will live on Mars"
    result = classify_input(claim)
    assert result is not None
    verdict, rationale = result
    assert verdict == "not_verifiable"
    assert rationale == FUTURE_MESSAGE

    claim2 = "Between 2021 and 2040 global temperatures will increase"
    result2 = classify_input(claim2)
    assert result2 is not None
    assert result2[0] == "not_verifiable"


def test_registrable_domain_uppercase_and_ports():
    """Bug fix: Uppercase domains and hostnames with ports must normalize cleanly."""
    assert _registrable_domain("NEWS.BBC.CO.UK") == "bbc.co.uk"
    assert _registrable_domain("Sports.BBC.co.uk") == "bbc.co.uk"
    assert _registrable_domain("example.com:8080") == "example.com"
    assert _registrable_domain("WWW.REUTERS.COM") == "reuters.com"


def test_group_sources_missing_url_domain_normalization():
    """Bug fix: Missing URL with raw domain string must normalize and cluster properly."""
    raw = [
        {
            "snippet": "First source snippet about economy.",
            "domain": "WWW.NYTIMES.COM",
            "url": "",
        },
        {
            "snippet": "Second source snippet from same publisher.",
            "domain": "nytimes.com",
            "url": "",
        },
    ]
    sources = group_sources(raw)
    assert len(sources) == 2
    assert sources[0].domain == "nytimes.com"
    assert sources[1].domain == "nytimes.com"
    assert sources[0].source_family_id == "nytimes.com"
    assert sources[1].source_family_id == "nytimes.com"


def test_normalize_excerpt_zero_width_chars():
    """Bug fix: Zero-width control characters must be stripped consistently in excerpts."""
    excerpt_with_zw = "atmospheric CO2 reached\u200b 426.9 ppm"
    normalized = normalize_excerpt(excerpt_with_zw)
    assert "\u200b" not in normalized
    assert normalized == "atmospheric CO2 reached 426.9 ppm"


def test_verification_request_whitespace_rejection():
    """Bug fix: Whitespace-only claims must be rejected with ValidationError."""
    with pytest.raises(ValidationError):
        VerificationRequest(claim="     ")

    with pytest.raises(ValidationError):
        VerificationRequest(claim="   \t\n  ")

    # Valid claim with padding spaces is stripped
    req = VerificationRequest(claim="   The Earth orbits the Sun.   ")
    assert req.claim == "The Earth orbits the Sun."

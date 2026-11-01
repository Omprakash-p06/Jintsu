"""Source grouping, URL sanitization, domain extraction, and wire family normalization."""

import hashlib
import re
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.api.schemas import SourceItem

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


def sanitize_and_quarantine(snippet: str) -> tuple[str, bool]:
    """Strip control/zero-width characters and flag prompt-injection attempts."""
    cleaned = _CONTROL_CHAR_PATTERN.sub("", snippet or "")
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    lowered = cleaned.lower()
    quarantined = any(token in lowered for token in _INJECTION_PATTERNS)
    return cleaned, quarantined


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
    host = host.split(":")[0].strip().lower().removeprefix("www.")
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
        if url:
            domain = _canonical_domain(url)
        else:
            domain = str(raw.get("domain") or "").strip().lower().removeprefix("www.") or "unknown"
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

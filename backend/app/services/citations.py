"""Citation validation and verbatim provenance matching."""

import html
import re

from app.api.schemas import ReasoningStatement, SourceItem

_CONTROL_CHAR_PATTERN = re.compile(
    "[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b\u200c\u200d\ufeff]"
)
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_excerpt(text: str) -> str:
    """Normalize excerpt text for verbatim provenance matching (Tier 2)."""
    cleaned = _CONTROL_CHAR_PATTERN.sub("", text or "")
    unescaped = html.unescape(cleaned)
    replaced = (
        unescaped.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return _WHITESPACE_PATTERN.sub(" ", replaced).strip()


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

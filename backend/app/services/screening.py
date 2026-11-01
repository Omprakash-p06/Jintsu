"""Gate A: Conservative pre-retrieval classification.

Screens claims for subjective value judgments and future predictions before any
outbound network calls are made.
"""

import re
from datetime import UTC, datetime

from app.api.schemas import PublicVerdict

SUBJECTIVE_MESSAGE = (
    "Subjective value judgment or normative statement; lacks an empirical ground truth."
)
FUTURE_MESSAGE = (
    "Future prediction or prospective event; cannot be empirically verified prior to occurrence."
)

_SUPERLATIVE_PATTERN = re.compile(
    r"\b(?:is|are|was|were)\s+(?:the\s+)?(?:greatest|best|worst|finest)\b"
    r"[^.?!]{0,60}?\b(?:of\s+all\s+time|in\s+(?:\w+\s+)?history|ever)\b",
    re.IGNORECASE,
)
_MORAL_PATTERN = re.compile(
    r"\b(?:morally|ethically)\s+(?:wrong|right|evil|good)\b",
    re.IGNORECASE,
)
_PRESCRIPTIVE_PATTERN = re.compile(
    r"\b(?:we|society|people|governments?)\s+(?:ought\s+to|should)\b",
    re.IGNORECASE,
)
_STATUTORY_CONTEXT_PATTERN = re.compile(
    r"\b(?:statutes?|laws?|legal|legislation|regulations?|acts?|courts?|constitution)\b",
    re.IGNORECASE,
)
_FUTURE_YEAR_PATTERN = re.compile(
    r"\b(?:in|by|until|during|through|for|before|after|between|and|to|from)\s+(20[2-9]\d)\b",
    re.IGNORECASE,
)
_PROSPECTIVE_MODAL_PATTERN = re.compile(
    r"\b(?:will|shall|projected\s+to|expected\s+to|forecast\s+to)\b",
    re.IGNORECASE,
)


def _is_subjective(claim: str) -> bool:
    if _SUPERLATIVE_PATTERN.search(claim) or _MORAL_PATTERN.search(claim):
        return True
    if _PRESCRIPTIVE_PATTERN.search(claim):
        return not _STATUTORY_CONTEXT_PATTERN.search(claim)
    return False


def _is_future_prediction(claim: str, current_year: int | None = None) -> bool:
    reference_year = current_year if current_year is not None else datetime.now(UTC).year
    has_future_year = False
    for match in _FUTURE_YEAR_PATTERN.finditer(claim):
        year = int(match.group(1))
        if year > reference_year:
            has_future_year = True
            break
    if not has_future_year:
        return False
    return _PROSPECTIVE_MODAL_PATTERN.search(claim) is not None


def classify_input(claim: str) -> tuple[PublicVerdict, str] | None:
    """Conservatively classify a claim before any network call.

    Returns a short-circuit verdict for subjective judgments and future predictions, or
    ``None`` to continue into the bounded retrieval pipeline.
    """
    if _is_subjective(claim):
        return ("not_verifiable", SUBJECTIVE_MESSAGE)
    if _is_future_prediction(claim):
        return ("not_verifiable", FUTURE_MESSAGE)
    return None

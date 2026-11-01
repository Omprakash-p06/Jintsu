"""Deterministic application-level verdict policy matrix and synthesis reconciliation."""

from app.api.schemas import (
    PublicVerdict,
    ReasoningStatement,
    SourceItem,
    VerificationSynthesisPayload,
)

COUNTEREVIDENCE_LIMITATION = (
    "Material counterevidence identified in retrieved sources; claim cannot be marked "
    "supported while unresolved refuting evidence exists."
)
SINGLE_FAMILY_LIMITATION = (
    "Corroborated by a single source domain; secondary independent corroboration required "
    "for supported verdict."
)
CONTRADICTION_GROUNDING_LIMITATION = (
    "No directly refuting source supports a contradicted verdict; verdict capped at "
    "insufficient_evidence."
)
CONFLICT_GROUNDING_LIMITATION = (
    "Proposed mixed verdict lacks both supporting and refuting sources; verdict capped at "
    "insufficient_evidence."
)
EMPTY_EVIDENCE_LIMITATION = (
    "No usable external evidence was retrieved for this claim; a definitive verdict cannot "
    "be awarded."
)
QUARANTINE_LIMITATION = (
    "One or more retrieved snippets were quarantined by the prompt-injection screen and "
    "excluded from synthesis."
)


def reconcile_synthesis(
    payload: VerificationSynthesisPayload,
    sources: list[SourceItem],
) -> tuple[list[SourceItem], list[ReasoningStatement]]:
    """Merge model source evaluations onto the active evidence pool."""
    by_id = {source.source_id: source for source in sources}
    for evaluation in payload.source_evaluations:
        target = by_id.get(evaluation.source_id)
        if target is None:
            continue
        target.stance = evaluation.stance
        target.relevance = evaluation.relevance
        target.exact_quote = evaluation.exact_quote
    return sources, list(payload.reasoning_statements)


def apply_verdict_policy(
    payload: VerificationSynthesisPayload,
    sources: list[SourceItem],
) -> tuple[PublicVerdict, list[str]]:
    """Veto unsupported verdicts per AGENTS.md rule 6 and SSOT Section 5."""
    active = [source for source in sources if not source.is_quarantined]
    limitations = list(payload.limitations)
    verdict: PublicVerdict = payload.proposed_verdict

    refutations = [
        source
        for source in active
        if source.stance == "refutes" and source.relevance in ("direct", "contextual")
    ]
    direct_refutations = [source for source in refutations if source.relevance == "direct"]
    support = [
        source
        for source in active
        if source.stance == "supports" and source.relevance in ("direct", "contextual")
    ]
    any_supports = [source for source in active if source.stance == "supports"]
    any_refutation = [source for source in active if source.stance == "refutes"]

    if verdict == "supported":
        if refutations:
            verdict = "contradicted" if direct_refutations else "mixed"
            limitations.append(COUNTEREVIDENCE_LIMITATION)
        else:
            families = {source.source_family_id for source in support}
            if len(families) < 2:
                verdict = "insufficient_evidence"
                limitations.append(SINGLE_FAMILY_LIMITATION)
    elif verdict == "contradicted":
        if not direct_refutations:
            verdict = "insufficient_evidence"
            limitations.append(CONTRADICTION_GROUNDING_LIMITATION)
    elif verdict == "mixed" and not (any_supports and any_refutation):
        verdict = "insufficient_evidence"
        limitations.append(CONFLICT_GROUNDING_LIMITATION)

    return verdict, limitations

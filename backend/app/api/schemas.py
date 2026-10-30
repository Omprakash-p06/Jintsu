from typing import Literal

from pydantic import BaseModel, Field

PublicVerdict = Literal[
    "supported",
    "contradicted",
    "mixed",
    "insufficient_evidence",
    "not_verifiable",
]

SourceStance = Literal["supports", "refutes", "neutral"]


class VerificationRequest(BaseModel):
    claim: str = Field(..., min_length=5, max_length=500)


class SourceItem(BaseModel):
    source_id: str
    url: str
    domain: str
    title: str
    snippet: str
    stance: SourceStance = "neutral"
    source_family_id: str
    retrieved_at: str
    published_at: str | None = None
    source_type: Literal["search_snippet", "llm_context"] = "search_snippet"
    content_hash: str
    extraction_status: Literal["ok", "truncated", "empty"] = "ok"
    is_quarantined: bool = False
    relevance: Literal["direct", "indirect", "contextual", "irrelevant"] | None = None
    exact_quote: str | None = None


class ReasoningStatement(BaseModel):
    statement: str
    citation_ids: list[str] = Field(default_factory=list)
    quoted_excerpt: str | None = None


class SourceEvaluationItem(BaseModel):
    source_id: str
    stance: SourceStance
    relevance: Literal["direct", "indirect", "contextual", "irrelevant"]
    exact_quote: str
    relationship_explanation: str


class VerificationSynthesisPayload(BaseModel):
    proposed_verdict: PublicVerdict
    summary: str
    limitations: list[str] = Field(default_factory=list)
    source_evaluations: list[SourceEvaluationItem] = Field(default_factory=list)
    reasoning_statements: list[ReasoningStatement] = Field(default_factory=list)
    temporal_qualification: str = ""
    abstention_reason: str = ""


class VerificationResponse(BaseModel):
    id: str
    claim: str
    public_verdict: PublicVerdict
    summary: str
    limitations: list[str] = Field(default_factory=list)
    sources: list[SourceItem] = Field(default_factory=list)
    reasoning: list[ReasoningStatement] = Field(default_factory=list)
    created_at: str


class VerificationListItem(BaseModel):
    id: str
    claim: str
    public_verdict: PublicVerdict
    created_at: str


class PaginatedVerificationResponse(BaseModel):
    items: list[VerificationListItem]
    total: int


class HealthResponse(BaseModel):
    status: str
    providers: dict[str, str]


class ErrorEnvelope(BaseModel):
    error: str
    code: str
    detail: str | None = None

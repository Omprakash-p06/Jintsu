from abc import ABC, abstractmethod

from app.api.schemas import VerificationSynthesisPayload


class SearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        count: int = 5,
        mode: str = "snippets",
        timeout: float = 2.0,
    ) -> list[dict]:
        """Search external index and return normalized source snippet dicts.

        NOTE: Callers must pass min(stage_budget, remaining_time); default 2.0s
        matches the Stage-1 subordinate ceiling, never the 8.0s overall request budget.
        """


class ModelProvider(ABC):
    @abstractmethod
    async def synthesize(
        self,
        claim: str,
        snippets: list[dict],
        timeout: float = 3.0,
    ) -> VerificationSynthesisPayload:
        """Synthesize claim verification payload strictly grounded in snippets.

        NOTE: Callers must pass min(stage_budget, remaining_time); default 3.0s matches
        the synthesis budget window.
        """

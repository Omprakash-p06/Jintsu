from abc import ABC, abstractmethod

from app.api.schemas import VerificationSynthesisPayload


class SearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        count: int = 5,
        mode: str = "snippets",
        timeout: float = 3.0,
    ) -> list[dict]:
        """Search external index and return normalized source snippet dicts."""


class ModelProvider(ABC):
    @abstractmethod
    async def synthesize(
        self,
        claim: str,
        snippets: list[dict],
        timeout: float = 4.0,
    ) -> VerificationSynthesisPayload:
        """Synthesize claim verification payload strictly grounded in snippets."""

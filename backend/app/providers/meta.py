import httpx

from app.api.schemas import VerificationSynthesisPayload
from app.core.config import settings
from app.core.errors import ProviderTimeoutError, ProviderUnavailableError
from app.providers.base import ModelProvider


class MetaModelProvider(ModelProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or settings.META_API_KEY
        self.base_url = (base_url or settings.META_API_BASE_URL).rstrip("/")
        self.model = model or settings.META_MODEL
        self._client = client

    async def synthesize(
        self,
        claim: str,
        snippets: list[dict],
        timeout: float = 3.0,
    ) -> VerificationSynthesisPayload:
        evidence_blocks = "\n".join(
            f'<evidence_snippet id="{s.get("source_id", "")}">\n{s.get("snippet", "")}\n</evidence_snippet>'
            for s in snippets
        )
        user_content = f"Claim: {claim}\n\nEvidence Snippets:\n{evidence_blocks}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an objective claim verification assistant. Evaluate the provided claim "
                    "strictly against the supplied evidence snippets. Output structured verification "
                    "synthesis adhering to the schema."
                ),
            },
            {"role": "user", "content": user_content},
        ]

        payload = {
            "model": self.model,
            "temperature": 0.0,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "verification_synthesis",
                    "strict": True,
                    "schema": VerificationSynthesisPayload.model_json_schema(),
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        try:
            if self._client is not None:
                response = await self._client.post(
                    url, json=payload, headers=headers, timeout=timeout
                )
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Meta model synthesis timed out",
                code="META_TIMEOUT",
                detail=str(exc),
            ) from exc
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise ProviderUnavailableError(
                "Meta model service unavailable",
                code="META_UNAVAILABLE",
                detail=str(exc),
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
            return VerificationSynthesisPayload.model_validate_json(content)
        except Exception as exc:
            raise ProviderUnavailableError(
                "Failed to parse synthesis payload from Meta model response",
                code="META_PARSE_ERROR",
                detail=str(exc),
            ) from exc


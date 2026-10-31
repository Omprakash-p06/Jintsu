import httpx

from app.api.schemas import VerificationSynthesisPayload
from app.core.config import settings
from app.core.errors import ProviderTimeoutError, ProviderUnavailableError
from app.providers.base import ModelProvider


def strict_json_schema() -> dict:
    """Transform Pydantic JSON schema to strictly conformant OpenAI/Meta schema.

    Strict mode requires:
    1. additionalProperties: False on every object node
    2. All properties listed in required on every object node
    3. Root title removed
    """
    schema = VerificationSynthesisPayload.model_json_schema()

    def harden(node: dict) -> dict:
        if not isinstance(node, dict):
            return node
        if node.get("type") == "object":
            props = node.get("properties", {})
            node["additionalProperties"] = False
            node["required"] = list(props.keys())
            for val in props.values():
                if isinstance(val, dict):
                    harden(val)
        items = node.get("items")
        if isinstance(items, dict):
            harden(items)
        defs = node.get("$defs", {})
        for val in defs.values():
            if isinstance(val, dict):
                harden(val)
        return node

    schema.pop("title", None)
    return harden(schema)


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
                    "schema": strict_json_schema(),
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
            try:
                data = response.json()
            except ValueError as exc:
                raise ProviderUnavailableError(
                    "Meta model returned a malformed JSON body",
                    code="META_UNAVAILABLE",
                    detail=str(exc),
                ) from exc

            if not isinstance(data, dict):
                raise ProviderUnavailableError(
                    "Meta model response payload is not an object",
                    code="META_UNAVAILABLE",
                    detail=f"got {type(data).__name__}",
                )
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
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise ValueError("Response missing non-empty 'choices' list")
            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                raise TypeError("Response 'choices[0]' is not an object")
            message = first_choice.get("message")
            if not isinstance(message, dict):
                raise TypeError("Response 'choices[0].message' is not an object")
            content = message.get("content")
            if not isinstance(content, str):
                raise TypeError(
                    f"Response message content is not a string (got {type(content).__name__})"
                )

            cleaned = content.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            return VerificationSynthesisPayload.model_validate_json(cleaned)
        except Exception as exc:
            raise ProviderUnavailableError(
                "Failed to parse synthesis payload from Meta model response",
                code="META_PARSE_ERROR",
                detail=str(exc),
            ) from exc

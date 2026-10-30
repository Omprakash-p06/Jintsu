import hashlib
import re
import urllib.parse
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.core.errors import ProviderTimeoutError, ProviderUnavailableError
from app.providers.base import SearchProvider

WIRE_MAPPINGS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:Associated Press|AP)\b", re.IGNORECASE), "associated_press"),
    (re.compile(r"\bReuters\b", re.IGNORECASE), "reuters"),
    (re.compile(r"\bPR Newswire\b", re.IGNORECASE), "pr_newswire"),
]


class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.BRAVE_API_KEY
        self._client = client

    async def search(
        self,
        query: str,
        count: int = 5,
        mode: str = "snippets",
        timeout: float = 3.0,
    ) -> list[dict]:
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
        }

        if mode == "snippets":
            url = "https://api.search.brave.com/res/v1/web/search"
            params = {"q": query, "count": str(count)}
        elif mode == "context":
            url = "https://api.search.brave.com/res/v1/llm/context"
            params = {"q": query}
        else:
            url = "https://api.search.brave.com/res/v1/web/search"
            params = {"q": query, "count": str(count)}

        try:
            if self._client is not None:
                response = await self._client.get(
                    url, params=params, headers=headers, timeout=timeout
                )
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Brave search request timed out",
                code="BRAVE_TIMEOUT",
                detail=str(exc),
            ) from exc
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            raise ProviderUnavailableError(
                "Brave search service unavailable",
                code="BRAVE_UNAVAILABLE",
                detail=str(exc),
            ) from exc

        raw_items: list[dict] = []
        if mode == "context":
            generic = data.get("grounding", {}).get("generic", [])
            for item in generic:
                raw_items.append(
                    {
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "snippet": "\n\n".join(item.get("snippets", [])),
                        "source_type": "llm_context",
                    }
                )
        else:
            results = data.get("web", {}).get("results", [])
            for item in results:
                raw_items.append(
                    {
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("description", ""),
                        "source_type": "search_snippet",
                    }
                )

        now_iso = datetime.now(UTC).isoformat()
        normalized: list[dict] = []
        for idx, item in enumerate(raw_items):
            url_str = item.get("url", "")
            domain = urllib.parse.urlparse(url_str).netloc.lower().removeprefix("www.")
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Check wire attribution tokens
            source_family_id = domain
            text_to_check = f"{title} {snippet}"
            for pattern, wire_id in WIRE_MAPPINGS:
                if pattern.search(text_to_check):
                    source_family_id = wire_id
                    break

            content_hash = hashlib.sha256(snippet.encode("utf-8")).hexdigest()
            status = "ok" if snippet.strip() else "empty"

            normalized.append(
                {
                    "source_id": f"src_{idx + 1}",
                    "url": url_str,
                    "domain": domain,
                    "source_family_id": source_family_id,
                    "title": title,
                    "snippet": snippet,
                    "content_hash": content_hash,
                    "retrieved_at": now_iso,
                    "source_type": item.get("source_type", "search_snippet"),
                    "extraction_status": status,
                    "is_quarantined": False,
                }
            )

        return normalized[:count]

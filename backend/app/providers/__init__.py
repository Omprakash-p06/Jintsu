from app.core.config import Settings, settings
from app.providers.base import ModelProvider, SearchProvider
from app.providers.brave import BraveSearchProvider
from app.providers.meta import MetaModelProvider
from app.providers.mock import MockModelProvider, MockSearchProvider


def get_search_provider(settings_obj: Settings = settings) -> SearchProvider:
    if settings_obj.USE_MOCK_PROVIDERS:
        return MockSearchProvider()
    return BraveSearchProvider(api_key=settings_obj.BRAVE_API_KEY)


def get_model_provider(settings_obj: Settings = settings) -> ModelProvider:
    if settings_obj.USE_MOCK_PROVIDERS:
        return MockModelProvider()
    return MetaModelProvider(
        api_key=settings_obj.META_API_KEY,
        base_url=settings_obj.META_API_BASE_URL,
        model=settings_obj.META_MODEL,
    )


__all__ = [
    "BraveSearchProvider",
    "MetaModelProvider",
    "MockModelProvider",
    "MockSearchProvider",
    "ModelProvider",
    "SearchProvider",
    "get_model_provider",
    "get_search_provider",
]

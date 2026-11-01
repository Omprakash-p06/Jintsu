from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings
from app.core.errors import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    RequestConstraintError,
)
from app.db.database import Database
from app.main import create_app
from app.services.verification import VerificationPipeline

SECRET_BRAVE = "brave-secret-value"
SECRET_META = "meta-secret-value"


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "USE_MOCK_PROVIDERS": True,
        "DATABASE_PATH": str(tmp_path / "api.db"),
        "BRAVE_API_KEY": "",
        "META_API_KEY": "",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
async def app(tmp_path: Path) -> AsyncIterator[FastAPI]:
    application = create_app(_settings(tmp_path))
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


class _RaisingPipeline:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def verify(self, claim: str) -> None:
        raise self._exc


async def test_lifespan_initializes_state_and_routes(app: FastAPI) -> None:
    assert isinstance(app.state.db, Database)
    assert isinstance(app.state.pipeline, VerificationPipeline)
    paths = set(app.openapi()["paths"])
    assert {
        "/api/v1/verifications",
        "/api/v1/verifications/{verification_id}",
        "/api/v1/health",
    } <= paths
    _, total = await app.state.db.list_verifications()
    assert total == 0


async def test_create_and_get_verification(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/verifications",
        json={"claim": "Water boils at 100 degrees Celsius at sea level."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim"] == "Water boils at 100 degrees Celsius at sea level."
    assert body["public_verdict"] in {
        "supported",
        "contradicted",
        "mixed",
        "insufficient_evidence",
        "not_verifiable",
    }
    assert body["id"]

    fetched = await client.get(f"/api/v1/verifications/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]
    assert isinstance(fetched.json()["sources"], list)


@pytest.mark.parametrize("claim", ["abc", "x" * 501])
async def test_post_rejects_out_of_bounds_claim(
    client: httpx.AsyncClient,
    claim: str,
) -> None:
    response = await client.post("/api/v1/verifications", json={"claim": claim})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["error"]


async def test_pagination_and_verdict_filter(client: httpx.AsyncClient) -> None:
    claims = [
        "Alpha claim text one.",
        "Beta claim text two.",
        "Gamma claim text three.",
    ]
    for claim in claims:
        created = await client.post("/api/v1/verifications", json={"claim": claim})
        assert created.status_code == 200

    page = await client.get("/api/v1/verifications", params={"limit": 1, "offset": 0})
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1

    filtered = await client.get("/api/v1/verifications", params={"verdict": "contradicted"})
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0


async def test_missing_verification_returns_envelope(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/verifications/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert body["error"]


async def test_delete_and_purge(client: httpx.AsyncClient) -> None:
    created = await client.post(
        "/api/v1/verifications",
        json={"claim": "A temporary empirical assertion."},
    )
    verification_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/verifications/{verification_id}")
    assert deleted.status_code == 204
    again = await client.delete(f"/api/v1/verifications/{verification_id}")
    assert again.status_code == 404

    await client.post(
        "/api/v1/verifications",
        json={"claim": "Another temporary empirical assertion."},
    )
    purged = await client.delete("/api/v1/verifications")
    assert purged.status_code == 204

    listing = await client.get("/api/v1/verifications")
    assert listing.json()["total"] == 0


async def test_health_reports_configuration_without_secrets(tmp_path: Path) -> None:
    application = create_app(
        _settings(tmp_path, BRAVE_API_KEY=SECRET_BRAVE, META_API_KEY=SECRET_META)
    )
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
            response = await http_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["providers"] == {"brave": "configured", "meta": "configured"}
    assert SECRET_BRAVE not in response.text
    assert SECRET_META not in response.text


@pytest.mark.parametrize(
    ("exc", "status_code", "code"),
    [
        (ProviderTimeoutError("Provider timed out", code="PROVIDER_TIMEOUT"), 504, "PROVIDER_TIMEOUT"),
        (ProviderUnavailableError("Provider down"), 503, "PROVIDER_UNAVAILABLE"),
        (RequestConstraintError("Compound claim rejected"), 422, "REQUEST_CONSTRAINT_ERROR"),
    ],
)
async def test_domain_errors_map_to_envelopes(
    app: FastAPI,
    client: httpx.AsyncClient,
    exc: Exception,
    status_code: int,
    code: str,
) -> None:
    app.state.pipeline = _RaisingPipeline(exc)
    response = await client.post(
        "/api/v1/verifications",
        json={"claim": "A valid empirical claim about the world."},
    )
    assert response.status_code == status_code
    body = response.json()
    assert body["code"] == code
    assert body["error"]


async def test_cors_allows_local_frontend_origins(client: httpx.AsyncClient) -> None:
    for origin in ("http://localhost:3000", "http://localhost:5173"):
        response = await client.get("/api/v1/health", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

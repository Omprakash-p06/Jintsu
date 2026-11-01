"""FastAPI application factory, lifespan wiring, CORS and error envelopes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.api.schemas import ErrorEnvelope
from app.core.config import Settings, settings
from app.core.errors import (
    ClientDisconnectedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RequestConstraintError,
)
from app.db.database import Database
from app.services.verification import VerificationPipeline

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _envelope(
    status_code: int,
    error: str,
    code: str,
    detail: str | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(error=error, code=code, detail=detail)
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


async def _provider_timeout_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProviderTimeoutError)
    return _envelope(504, exc.message, exc.code, exc.detail)


async def _provider_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProviderUnavailableError)
    return _envelope(503, exc.message, exc.code, exc.detail)


async def _client_disconnected_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ClientDisconnectedError)
    return _envelope(499, exc.message, exc.code, exc.detail)


async def _constraint_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestConstraintError)
    return _envelope(422, exc.message, exc.code, exc.detail)


async def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        messages.append(f"{location}: {error.get('msg', 'invalid value')}")
    return _envelope(
        422,
        "Request validation failed",
        "VALIDATION_ERROR",
        "; ".join(messages) or None,
    )


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    code = "NOT_FOUND" if exc.status_code == 404 else f"HTTP_{exc.status_code}"
    return _envelope(exc.status_code, detail, code, detail)


def create_app(settings_obj: Settings | None = None) -> FastAPI:
    app_settings = settings_obj or settings

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = Database(db_path=app_settings.DATABASE_PATH)
        await database.init_db()
        application.state.settings = app_settings
        application.state.db = database
        application.state.pipeline = VerificationPipeline(
            db=database,
            settings_obj=app_settings,
        )
        yield

    application = FastAPI(title="jintru", version="0.1.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router, prefix="/api/v1")
    application.add_exception_handler(ProviderTimeoutError, _provider_timeout_handler)
    application.add_exception_handler(ProviderUnavailableError, _provider_unavailable_handler)
    application.add_exception_handler(ClientDisconnectedError, _client_disconnected_handler)
    application.add_exception_handler(RequestConstraintError, _constraint_handler)
    application.add_exception_handler(RequestValidationError, _validation_handler)
    application.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    return application


app = create_app()

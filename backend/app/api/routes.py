"""REST endpoints implementing the /api/v1 contract (SSOT Section 3.8)."""

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.schemas import (
    HealthResponse,
    PaginatedVerificationResponse,
    PublicVerdict,
    VerificationListItem,
    VerificationRequest,
    VerificationResponse,
)

router = APIRouter()


@router.post(
    "/verifications",
    response_model=VerificationResponse,
    status_code=200,
    summary="Submit a claim for verification",
)
async def create_verification(
    payload: VerificationRequest,
    request: Request,
) -> VerificationResponse:
    pipeline = request.app.state.pipeline
    result: VerificationResponse = await pipeline.verify(payload.claim)
    return result


@router.get(
    "/verifications",
    response_model=PaginatedVerificationResponse,
    summary="List verification history",
)
async def list_verifications(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    verdict: PublicVerdict | None = None,
) -> PaginatedVerificationResponse:
    rows, total = await request.app.state.db.list_verifications(
        limit=limit,
        offset=offset,
        verdict=verdict,
    )
    return PaginatedVerificationResponse(
        items=[VerificationListItem(**row) for row in rows],
        total=total,
    )


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationResponse,
    summary="Retrieve a single verification record",
)
async def get_verification(
    verification_id: str,
    request: Request,
) -> VerificationResponse:
    row = await request.app.state.db.get_verification(verification_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return VerificationResponse(**row)


@router.delete(
    "/verifications/{verification_id}",
    status_code=204,
    summary="Delete a single verification record",
)
async def delete_verification(verification_id: str, request: Request) -> None:
    deleted = await request.app.state.db.delete_verification(verification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Verification not found")


@router.delete(
    "/verifications",
    status_code=204,
    summary="Purge all verification records",
)
async def purge_verifications(request: Request) -> None:
    await request.app.state.db.purge_verifications()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Report liveness and provider configuration state",
)
async def health(request: Request) -> HealthResponse:
    app_settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        providers={
            "brave": "configured" if app_settings.BRAVE_API_KEY else "missing",
            "meta": "configured" if app_settings.META_API_KEY else "missing",
        },
    )

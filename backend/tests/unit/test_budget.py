import asyncio
from unittest.mock import AsyncMock

import pytest

from app.api.schemas import SourceEvaluationItem, VerificationSynthesisPayload
from app.core.errors import ProviderTimeoutError
from app.db.database import Database
from app.providers.mock import MockModelProvider, MockSearchProvider
from app.services.verification import (
    STAGE1_TIMEOUT_SECONDS,
    STAGE2_TIMEOUT_SECONDS,
    SYNTHESIS_TIMEOUT_SECONDS,
    VerificationPipeline,
)


@pytest.fixture
async def test_db(tmp_path):
    db_file = tmp_path / "test_budget.db"
    db = Database(db_path=str(db_file))
    await db.init_db()
    return db


@pytest.mark.asyncio
async def test_stage1_timeout_clamped_to_remaining_budget(test_db):
    search_provider = MockSearchProvider()
    search_provider.search = AsyncMock(return_value=[])  # type: ignore[method-assign]
    pipeline = VerificationPipeline(
        db=test_db,
        search_provider=search_provider,
        model_provider=MockModelProvider(),
        deadline_seconds=1.5,
    )
    await pipeline.verify("Valid empirical assertion here")
    assert search_provider.search.await_count >= 1
    assert search_provider.search.await_args is not None
    passed_timeout = search_provider.search.await_args.kwargs["timeout"]
    assert passed_timeout <= 1.5
    assert passed_timeout <= STAGE1_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_stage2_counter_search_skipped_when_time_below_threshold(test_db):
    search_provider = MockSearchProvider()
    search_provider.search = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            {
                "title": "Alpha",
                "snippet": "Alpha evidence.",
                "url": "https://alpha.example/doc",
                "domain": "alpha.example",
            }
        ]
    )
    # Total deadline is 3.0s, which is below STAGE2_MIN_REMAINING_SECONDS (3.5s)
    pipeline = VerificationPipeline(
        db=test_db,
        search_provider=search_provider,
        model_provider=MockModelProvider(),
        deadline_seconds=3.0,
    )
    await pipeline.verify("Valid empirical assertion here")
    # Only stage 1 was executed, stage 2 was skipped because remaining < 3.5s
    assert search_provider.search.await_count == 1


@pytest.mark.asyncio
async def test_stage2_counter_search_runs_when_time_sufficient(test_db):
    search_provider = MockSearchProvider()
    search_provider.search = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            {
                "title": "Alpha",
                "snippet": "Alpha evidence.",
                "url": "https://alpha.example/doc",
                "domain": "alpha.example",
            }
        ]
    )
    # Normal 8.0s deadline leaves plenty of time for Stage 2
    pipeline = VerificationPipeline(
        db=test_db,
        search_provider=search_provider,
        model_provider=MockModelProvider(),
        deadline_seconds=8.0,
    )
    await pipeline.verify("Valid empirical assertion here")
    # Stage 1 and Stage 2 executed
    assert search_provider.search.await_count == 2
    counter_call_args = search_provider.search.await_args_list[1]
    assert "dispute OR controversy" in counter_call_args.args[0]
    assert counter_call_args.kwargs["timeout"] <= STAGE2_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_synthesis_guard_aborts_cleanly_below_minimum_window(test_db):
    search_provider = MockSearchProvider()

    async def slow_search(*args, **kwargs):
        # Simulate search consuming 1.0s of a 3.0s total budget -> remaining 2.0s < 2.5s
        await asyncio.sleep(1.0)
        return [
            {
                "title": "Alpha",
                "snippet": "Alpha evidence.",
                "url": "https://alpha.example/doc",
                "domain": "alpha.example",
            }
        ]

    search_provider.search = AsyncMock(side_effect=slow_search)  # type: ignore[method-assign]
    model_provider = MockModelProvider()
    model_provider.synthesize = AsyncMock()  # type: ignore[method-assign]

    pipeline = VerificationPipeline(
        db=test_db,
        search_provider=search_provider,
        model_provider=model_provider,
        deadline_seconds=3.0,  # 3.0s total - 1.0s search = 2.0s remaining < 2.5s min window
    )

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await pipeline.verify("Valid empirical assertion here")

    assert exc_info.value.code == "SYNTHESIS_WINDOW_EXCEEDED"
    assert "below the 2.5" in str(exc_info.value.detail)

    # Assert ZERO model calls were made
    assert model_provider.synthesize.await_count == 0

    # Assert ZERO records were persisted to SQLite
    stored, total = await test_db.list_verifications()
    assert total == 0
    assert len(stored) == 0


@pytest.mark.asyncio
async def test_synthesis_timeout_clamped_to_remaining_budget(test_db):
    search_provider = MockSearchProvider()
    search_provider.search = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            {
                "title": "Alpha",
                "snippet": "Alpha evidence.",
                "url": "https://alpha.example/doc",
                "domain": "alpha.example",
            }
        ]
    )
    model_provider = MockModelProvider()
    model_provider.synthesize = AsyncMock(  # type: ignore[method-assign]
        return_value=VerificationSynthesisPayload(
            proposed_verdict="insufficient_evidence",
            summary="Evidence evaluated.",
            limitations=[],
            source_evaluations=[
                SourceEvaluationItem(
                    source_id="src_1",
                    stance="neutral",
                    relevance="contextual",
                    exact_quote="Alpha evidence.",
                    relationship_explanation="Context.",
                )
            ],
            reasoning_statements=[],
        )
    )

    # 3.2s deadline: Stage 1 takes ~0s, Stage 2 skipped (< 3.5s), remaining ~3.2s
    # synthesis timeout is min(3.0, remaining)
    pipeline = VerificationPipeline(
        db=test_db,
        search_provider=search_provider,
        model_provider=model_provider,
        deadline_seconds=3.2,
    )
    await pipeline.verify("Valid empirical assertion here")
    assert model_provider.synthesize.await_count == 1
    assert model_provider.synthesize.await_args is not None
    passed_timeout = model_provider.synthesize.await_args.kwargs["timeout"]
    assert passed_timeout <= SYNTHESIS_TIMEOUT_SECONDS
    assert passed_timeout <= 3.2

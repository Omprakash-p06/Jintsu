from pathlib import Path

import pytest

from app.api.schemas import (
    PublicVerdict,
    ReasoningStatement,
    SourceItem,
    VerificationResponse,
)
from app.db.database import Database


@pytest.fixture
async def db(tmp_path: Path):
    test_db_path = str(tmp_path / "test.db")
    database = Database(db_path=test_db_path)
    await database.init_db()
    return database


async def test_database_init_and_pragmas(db: Database):
    async with db._connect() as conn:
        cursor = await conn.execute("PRAGMA busy_timeout;")
        row = await cursor.fetchone()
        assert row is not None and row[0] == 5000

        cursor = await conn.execute("PRAGMA synchronous;")
        row = await conn.execute("PRAGMA synchronous;")
        row = await cursor.fetchone()
        # NORMAL synchronous corresponds to 1 in SQLite
        assert row is not None and row[0] == 1


async def test_save_and_get_verification(db: Database):
    record = VerificationResponse(
        id="v_001",
        claim="Water boils at 100 degrees Celsius at sea level.",
        public_verdict="supported",
        summary="Empirical evidence establishes boiling point.",
        limitations=["Applies strictly at standard atmospheric pressure."],
        sources=[
            SourceItem(
                source_id="src_1",
                url="https://physics.example.org/water",
                domain="physics.example.org",
                title="Thermodynamics of Water",
                snippet="Water boils at 100C at 1 atm.",
                stance="supports",
                source_family_id="physics.example.org",
                retrieved_at="2026-10-31T00:00:00Z",
                content_hash="hash_water_100",
                relevance="direct",
                exact_quote="Water boils at 100C",
            )
        ],
        reasoning=[
            ReasoningStatement(
                statement="Verified boiling point at standard pressure.",
                citation_ids=["src_1"],
                quoted_excerpt="Water boils at 100C",
            )
        ],
        created_at="2026-10-31T00:00:00Z",
    )

    await db.save_verification(record)

    fetched = await db.get_verification("v_001")
    assert fetched is not None
    assert fetched["id"] == "v_001"
    assert fetched["claim"] == record.claim
    assert fetched["public_verdict"] == "supported"
    assert isinstance(fetched["limitations"], list)
    assert fetched["limitations"] == ["Applies strictly at standard atmospheric pressure."]
    assert isinstance(fetched["sources"], list)
    assert len(fetched["sources"]) == 1
    assert fetched["sources"][0]["source_id"] == "src_1"
    assert fetched["sources"][0]["relevance"] == "direct"
    assert isinstance(fetched["reasoning"], list)
    assert len(fetched["reasoning"]) == 1
    assert fetched["reasoning"][0]["quoted_excerpt"] == "Water boils at 100C"


async def test_list_and_filter_verifications(db: Database):
    verdicts: list[PublicVerdict] = ["supported", "contradicted", "supported"]
    for idx, verdict in enumerate(verdicts):
        record = VerificationResponse(
            id=f"v_00{idx + 1}",
            claim=f"Test claim {idx + 1}",
            public_verdict=verdict,
            summary=f"Summary {idx + 1}",
            limitations=[],
            sources=[],
            reasoning=[],
            created_at=f"2026-10-31T0{idx}:00:00Z",
        )
        await db.save_verification(record)

    all_items, total = await db.list_verifications(limit=10, offset=0)
    assert total == 3
    assert len(all_items) == 3

    supported_items, total_supported = await db.list_verifications(
        limit=10, offset=0, verdict="supported"
    )
    assert total_supported == 2
    assert len(supported_items) == 2


async def test_delete_and_purge_verifications(db: Database):
    record = VerificationResponse(
        id="v_to_delete",
        claim="Temporary claim.",
        public_verdict="insufficient_evidence",
        summary="Temporary summary.",
        limitations=[],
        sources=[],
        reasoning=[],
        created_at="2026-10-31T00:00:00Z",
    )
    await db.save_verification(record)

    deleted = await db.delete_verification("v_to_delete")
    assert deleted is True

    record_after = await db.get_verification("v_to_delete")
    assert record_after is None

    # Save another and purge
    await db.save_verification(record)
    await db.purge_verifications()
    all_items, total = await db.list_verifications()
    assert total == 0
    assert len(all_items) == 0

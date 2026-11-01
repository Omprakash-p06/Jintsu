import asyncio
import random
import uuid

import pytest

from app.api.schemas import (
    PublicVerdict,
    ReasoningStatement,
    SourceItem,
    VerificationResponse,
)
from app.db.database import Database


def _make_record(idx: int, verdict: PublicVerdict = "supported") -> VerificationResponse:
    rec_id = str(uuid.uuid4())
    return VerificationResponse(
        id=rec_id,
        claim=f"Concurrent empirical test claim {idx} {rec_id[:8]}",
        public_verdict=verdict,
        summary=f"Summary for concurrent record {idx}.",
        limitations=["Limitation 1", "Limitation 2"],
        sources=[
            SourceItem(
                source_id="src_1",
                url="https://source1.example.com/data",
                domain="source1.example.com",
                title=f"Source 1 for record {idx}",
                snippet=f"Snippet content for source 1 record {idx}",
                stance="supports",
                source_family_id="source1.example.com",
                retrieved_at="2026-11-01T20:00:00Z",
                source_type="search_snippet",
                content_hash=f"hash1_{idx}",
                extraction_status="ok",
                is_quarantined=False,
            ),
            SourceItem(
                source_id="src_2",
                url="https://source2.example.com/data",
                domain="source2.example.com",
                title=f"Source 2 for record {idx}",
                snippet=f"Snippet content for source 2 record {idx}",
                stance="supports",
                source_family_id="source2.example.com",
                retrieved_at="2026-11-01T20:00:00Z",
                source_type="search_snippet",
                content_hash=f"hash2_{idx}",
                extraction_status="ok",
                is_quarantined=False,
            ),
        ],
        reasoning=[
            ReasoningStatement(
                statement=f"Reasoning statement for record {idx}",
                citation_ids=["src_1", "src_2"],
                quoted_excerpt=f"Snippet content for source 1 record {idx}",
            )
        ],
        created_at="2026-11-01T20:00:00Z",
    )


@pytest.mark.asyncio
async def test_sqlite_wal_multi_worker_concurrency_no_locks(tmp_path):
    """Assert exactly 0 database lock exceptions under 10 concurrent async workers."""
    db_file = tmp_path / "concurrent_wal.db"
    db = Database(db_path=str(db_file))
    await db.init_db()

    num_workers = 10
    ops_per_worker = 20
    saved_ids: list[str] = []
    saved_lock = asyncio.Lock()
    verdicts: list[PublicVerdict] = [
        "supported",
        "contradicted",
        "mixed",
        "insufficient_evidence",
        "not_verifiable",
    ]

    async def worker(worker_id: int):
        for op_idx in range(ops_per_worker):
            action = random.choice(["save", "get", "list", "save", "delete"])
            verdict = verdicts[(worker_id + op_idx) % len(verdicts)]
            record = _make_record(worker_id * 100 + op_idx, verdict=verdict)

            if action == "save":
                await db.save_verification(record)
                async with saved_lock:
                    saved_ids.append(record.id)
            elif action == "get":
                target_id = None
                async with saved_lock:
                    if saved_ids:
                        target_id = random.choice(saved_ids)
                if target_id:
                    retrieved = await db.get_verification(target_id)
                    if retrieved:
                        assert retrieved["id"] == target_id
                        assert isinstance(retrieved["sources"], list)
                        assert isinstance(retrieved["reasoning"], list)
            elif action == "list":
                chosen_verdict = random.choice(verdicts + [None])
                items, total = await db.list_verifications(
                    limit=10,
                    offset=0,
                    verdict=chosen_verdict,
                )
                assert isinstance(items, list)
                assert total >= 0
            elif action == "delete":
                target_id = None
                async with saved_lock:
                    if saved_ids:
                        target_id = saved_ids.pop()
                if target_id:
                    deleted = await db.delete_verification(target_id)
                    assert deleted is True

            # Short random jitter to interleave async yields
            await asyncio.sleep(random.uniform(0.001, 0.01))

    # Execute all 10 workers simultaneously
    tasks = [worker(i) for i in range(num_workers)]
    await asyncio.gather(*tasks)

    # Verify database consistency after concurrent execution
    remaining_items, remaining_total = await db.list_verifications(limit=100)
    assert remaining_total >= 0
    assert len(remaining_items) == remaining_total

    for item in remaining_items:
        fetched = await db.get_verification(item["id"])
        assert fetched is not None
        assert fetched["id"] == item["id"]
        assert isinstance(fetched["limitations"], list)
        assert isinstance(fetched["sources"], list)
        assert isinstance(fetched["reasoning"], list)

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from app.api.schemas import VerificationResponse
from app.core.config import settings


class Database:
    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def _connect(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row
            yield db

    async def init_db(self) -> None:
        async with self._connect() as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS verifications (
                    id TEXT PRIMARY KEY,
                    claim TEXT NOT NULL,
                    status TEXT NOT NULL,
                    public_verdict TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    limitations JSON NOT NULL,
                    sources JSON NOT NULL,
                    reasoning JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at DESC);"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_verdict ON verifications(public_verdict);"
            )
            await db.commit()

    async def save_verification(self, record: VerificationResponse) -> None:
        for attempt in range(3):
            try:
                async with self._connect() as db:
                    await db.execute(
                        """
                        INSERT INTO verifications (
                            id, claim, status, public_verdict, summary,
                            limitations, sources, reasoning, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            record.id,
                            record.claim,
                            "completed",
                            record.public_verdict,
                            record.summary,
                            json.dumps(record.limitations),
                            json.dumps([s.model_dump() for s in record.sources]),
                            json.dumps([r.model_dump() for r in record.reasoning]),
                            record.created_at,
                        ),
                    )
                    await db.commit()
                    return
            except sqlite3.OperationalError:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.05 * (2**attempt))

    async def get_verification(self, id: str) -> dict | None:
        async with (
            self._connect() as db,
            db.execute("SELECT * FROM verifications WHERE id = ?", (id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["limitations"] = json.loads(data["limitations"])
            data["sources"] = json.loads(data["sources"])
            data["reasoning"] = json.loads(data["reasoning"])
            return data

    async def list_verifications(
        self,
        limit: int = 20,
        offset: int = 0,
        verdict: str | None = None,
    ) -> tuple[list[dict], int]:
        async with self._connect() as db:
            query = "SELECT id, claim, public_verdict, created_at FROM verifications"
            count_query = "SELECT COUNT(*) FROM verifications"
            params: list = []
            if verdict:
                query += " WHERE public_verdict = ?"
                count_query += " WHERE public_verdict = ?"
                params.append(verdict)
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            async with db.execute(count_query, params[:1] if verdict else ()) as cursor:
                total_row = await cursor.fetchone()
                total = total_row[0] if total_row else 0

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows], total

    async def delete_verification(self, id: str) -> bool:
        async with self._connect() as db:
            cursor = await db.execute("DELETE FROM verifications WHERE id = ?", (id,))
            await db.commit()
            return cursor.rowcount > 0

    async def purge_verifications(self) -> None:
        async with self._connect() as db:
            await db.execute("DELETE FROM verifications")
            await db.commit()

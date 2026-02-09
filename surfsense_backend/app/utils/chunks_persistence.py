"""
Chunk persistence helpers.

Why:
- Several processors build `Chunk(...)` objects then call a "safe_set_chunks" helper
  that uses `set_committed_value(document, "chunks", chunks)` to avoid async lazy-loads.
- `set_committed_value` bypasses relationship instrumentation, so the new chunks are not
  attached to the session and never get INSERTed. Result: `chunks` table stays empty.

This module provides an async-safe, DB-correct way to replace a document's chunks
without triggering lazy loading of the relationship.
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.db import Chunk, Document


async def replace_document_chunks(
    session: AsyncSession,
    document: Document,
    chunks: list[Chunk],
) -> None:
    """
    Replace all chunks for a document in a way that works with SQLAlchemy AsyncSession.

    This:
    - Deletes existing DB rows for the document (no lazy-load required)
    - Inserts the new chunks with `document_id` set
    - Updates the in-memory relationship to match (without triggering a load)
    """
    if document.id is None:
        raise ValueError("document.id is required to persist chunks")

    # Remove old chunks in DB (don't rely on relationship loading/orphan detection).
    await session.execute(delete(Chunk).where(Chunk.document_id == document.id))

    for c in chunks:
        c.document_id = document.id

    session.add_all(chunks)

    # Keep in-memory state coherent for the rest of the request/task.
    set_committed_value(document, "chunks", chunks)


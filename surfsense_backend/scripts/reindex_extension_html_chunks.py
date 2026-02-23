#!/usr/bin/env python3
"""
Normalize and re-chunk existing EXTENSION documents.

Use this when older extension captures were indexed with raw HTML content.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from app.config import config
from app.db import Chunk, Document, DocumentType
from app.tasks.document_processors.base import get_current_timestamp
from app.tasks.document_processors.extension_processor import (
    normalize_extension_page_content,
)
from app.utils.blocknote_converter import convert_markdown_to_blocknote
from app.utils.document_converters import create_document_chunks, generate_content_hash


def _build_combined_document_string(
    metadata: dict, normalized_page_content: str
) -> str:
    return "\n".join(
        [
            "<DOCUMENT>",
            "<METADATA>",
            f"SESSION_ID: {metadata.get('BrowsingSessionId', '')}",
            f"URL: {metadata.get('VisitedWebPageURL', '')}",
            f"TITLE: {metadata.get('VisitedWebPageTitle', '')}",
            f"REFERRER: {metadata.get('VisitedWebPageReffererURL', '')}",
            f"TIMESTAMP: {metadata.get('VisitedWebPageDateWithTimeInISOString', '')}",
            (
                "DURATION_MS: "
                f"{metadata.get('VisitedWebPageVisitDurationInMilliseconds', '')}"
            ),
            "</METADATA>",
            "<CONTENT>",
            "FORMAT: markdown",
            "TEXT_START",
            normalized_page_content,
            "TEXT_END",
            "</CONTENT>",
            "</DOCUMENT>",
        ]
    )


async def run(
    search_space_id: int,
    dry_run: bool,
    limit: int | None,
    update_in_place: bool,
) -> None:
    engine = create_async_engine(
        config.DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    updated = 0
    skipped = 0

    async with session_maker() as session:
        query = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(
                Document.document_type == DocumentType.EXTENSION,
                Document.search_space_id == search_space_id,
            )
            .order_by(Document.id.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        docs = (await session.execute(query)).scalars().all()
        print(f"Found {len(docs)} EXTENSION docs in search space {search_space_id}")

        for doc in docs:
            ordered_chunks = sorted(
                doc.chunks,
                key=lambda c: ((c.created_at.isoformat() if c.created_at else ""), c.id),
            )
            raw_text = "\n\n".join(
                (chunk.content or "").strip()
                for chunk in ordered_chunks
                if (chunk.content or "").strip()
            ).strip()

            if not raw_text:
                skipped += 1
                print(f"[skip] doc={doc.id} title={doc.title!r} reason=no_chunk_text")
                continue

            normalized_text = normalize_extension_page_content(raw_text)
            if not normalized_text:
                skipped += 1
                print(f"[skip] doc={doc.id} title={doc.title!r} reason=empty_after_norm")
                continue

            if normalized_text == raw_text:
                skipped += 1
                print(f"[skip] doc={doc.id} title={doc.title!r} reason=unchanged")
                continue

            if dry_run:
                print(
                    f"[dry-run] doc={doc.id} title={doc.title!r} "
                    f"len_old={len(raw_text)} len_new={len(normalized_text)}"
                )
                updated += 1
                continue

            try:
                if update_in_place:
                    chunks_changed = 0
                    for chunk in ordered_chunks:
                        old_chunk_text = (chunk.content or "").strip()
                        if not old_chunk_text:
                            continue
                        new_chunk_text = normalize_extension_page_content(old_chunk_text)
                        if new_chunk_text and new_chunk_text != old_chunk_text:
                            chunk.content = new_chunk_text
                            chunks_changed += 1

                    if chunks_changed == 0:
                        skipped += 1
                        print(
                            f"[skip] doc={doc.id} title={doc.title!r} "
                            "reason=no_chunk_changes"
                        )
                        continue

                    chunks_new_count = len(ordered_chunks)
                else:
                    await session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
                    await session.flush()

                    new_chunks = await create_document_chunks(normalized_text)
                    for chunk in new_chunks:
                        chunk.document_id = doc.id
                        session.add(chunk)
                    chunks_new_count = len(new_chunks)

                metadata = doc.document_metadata or {}
                combined_document_string = _build_combined_document_string(
                    metadata, normalized_text
                )
                doc.content_hash = generate_content_hash(
                    combined_document_string, doc.search_space_id
                )
                doc.updated_at = get_current_timestamp()

                # Keep editor view coherent with the updated content format.
                blocknote = await convert_markdown_to_blocknote(combined_document_string)
                if blocknote:
                    doc.blocknote_document = blocknote

                await session.commit()
                updated += 1
                print(
                    f"[ok] doc={doc.id} title={doc.title!r} "
                    f"chunks_old={len(ordered_chunks)} chunks_new={chunks_new_count}"
                )
            except Exception as exc:
                await session.rollback()
                skipped += 1
                print(
                    f"[error] doc={doc.id} title={doc.title!r} "
                    f"reason={type(exc).__name__}: {exc}"
                )

    await engine.dispose()
    print(f"Done. updated={updated} skipped={skipped} dry_run={dry_run}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize and re-chunk existing EXTENSION documents."
    )
    parser.add_argument("--search-space-id", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--update-in-place",
        action="store_true",
        help=(
            "Normalize existing chunk content in place without re-embedding. "
            "Recommended for quick cleanup of malformed HTML output."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        run(
            search_space_id=args.search_space_id,
            dry_run=args.dry_run,
            limit=args.limit,
            update_in_place=args.update_in_place,
        )
    )


if __name__ == "__main__":
    main()

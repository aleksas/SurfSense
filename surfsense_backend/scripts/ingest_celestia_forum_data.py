#!/usr/bin/env python3
"""
Ingest Celestia forum markdown threads into SurfSense as FILE documents.

Why this exists:
- The repo has forum markdown files on the host at /mnt/data/surfsense/docs/celestia_forum_data.
- The SurfSense advanced stack doesn't auto-index that folder.
- This script creates pending Document rows, then runs the same markdown processing
  path used by the normal file upload pipeline (embedding + chunking + status updates).

Run (inside the backend container):
  python /app/scripts/ingest_celestia_forum_data.py --email test@example.com

Notes:
- Requires the backend container to have /ingest/docs mounted (see docker-compose.yml).
- For markdown files, the processor unlinks the temp file path it reads, so we copy each
  source file to /tmp first.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import shutil
from pathlib import Path

from sqlalchemy import select

from app.db import Document, DocumentStatus, DocumentType, SearchSpace, User, async_session_maker
from app.services.task_logging_service import TaskLoggingService
from app.tasks.document_processors.base import (
    check_document_by_unique_identifier,
    get_current_timestamp,
)
from app.tasks.document_processors.file_processors import (
    process_file_in_background_with_document,
)
from app.utils.document_converters import generate_unique_identifier_hash


DEFAULT_FOLDER = Path("/ingest/docs/celestia_forum_data")


async def _resolve_search_space_id(session, user_id: str, explicit_id: int | None) -> int:
    if explicit_id is not None:
        return explicit_id

    result = await session.execute(
        select(SearchSpace.id).where(SearchSpace.user_id == user_id).order_by(SearchSpace.created_at.asc())
    )
    search_space_id = result.scalars().first()
    if search_space_id is None:
        raise RuntimeError(f"No search space found for user_id={user_id}")
    return int(search_space_id)


async def ingest(
    *,
    email: str,
    folder: Path,
    search_space_id: int | None,
    limit: int | None,
    glob: str,
    dry_run: bool,
    reindex_existing: bool,
) -> int:
    if not folder.exists():
        raise RuntimeError(f"Folder not found inside container: {folder}")

    # Sort numerically by thread id when possible (thread_123.md), otherwise by name.
    # Lexicographic sorting can put thread_10000.md near the start, making progress appear
    # "stuck" on very large threads early in the run.
    def _sort_key(p: Path) -> tuple[int, int | str]:
        stem = p.stem
        if stem.startswith("thread_"):
            suffix = stem.removeprefix("thread_")
            if suffix.isdigit():
                return (0, int(suffix))
        return (1, p.name)

    files = sorted(folder.glob(glob), key=_sort_key)
    if not files:
        raise RuntimeError(f"No files matched {glob} under {folder}")

    if limit is not None:
        files = files[:limit]

    tmp_dir = Path("/tmp/surfsense_ingest")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    reindexed = 0
    skipped_existing = 0
    processed_ok = 0
    processed_failed = 0

    async with async_session_maker() as session:
        # The upstream chonkie SentenceTransformerEmbeddings calls SentenceTransformer.encode()
        # without show_progress_bar=False, which spams progress bars ("Batches: ...") for each embed.
        # For bulk ingestion, silence that output.
        from app.config import config as app_config

        try:
            st_model = app_config.embedding_model_instance.model

            def _quiet_embed(text: str):
                return st_model.encode(  # type: ignore[attr-defined]
                    text, convert_to_numpy=True, show_progress_bar=False
                )

            app_config.embedding_model_instance.embed = _quiet_embed  # type: ignore[assignment]
        except Exception:
            # If embedding backend differs, don't fail ingestion; it will just be noisy.
            pass

        user = (await session.execute(select(User).where(User.email == email))).scalars().first()
        if not user:
            raise RuntimeError(f"User not found: {email}")

        ss_id = await _resolve_search_space_id(session, str(user.id), search_space_id)
        task_logger = TaskLoggingService(session, ss_id)

        print(f"User: {email} (id={user.id})")
        print(f"Search space: {ss_id}")
        print(f"Folder: {folder}")
        print(f"Files: {len(files)}")

        for idx, src in enumerate(files, start=1):
            filename = src.name
            unique_identifier_hash = generate_unique_identifier_hash(
                DocumentType.FILE, filename, ss_id
            )

            existing = await check_document_by_unique_identifier(session, unique_identifier_hash)
            if existing and not reindex_existing:
                skipped_existing += 1
                if skipped_existing <= 5 or skipped_existing % 250 == 0:
                    print(f"[{idx}/{len(files)}] skip existing: {filename} (doc_id={existing.id})")
                continue

            if existing:
                reindexed += 1
            else:
                created += 1

            if dry_run:
                # Keep output stable regardless of created vs reindexed.
                if (created + reindexed) <= 5 or (created + reindexed) % 250 == 0:
                    action = "would reindex" if existing else "would ingest"
                    print(f"[{idx}/{len(files)}] {action}: {filename}")
                continue

            if existing:
                # Reindex in-place: flip to pending and update source_path metadata.
                document = existing
                document.status = DocumentStatus.pending()
                document.updated_at = get_current_timestamp()
                document.document_metadata = {
                    **(document.document_metadata or {}),
                    "FILE_NAME": filename,
                    "source_path": str(src),
                    "reindexed_at": get_current_timestamp().isoformat(),
                }
                await session.commit()
                await session.refresh(document)
            else:
                # Phase 1: create a pending doc (mirrors /documents/fileupload behavior)
                document = Document(
                    search_space_id=ss_id,
                    title=filename,
                    document_type=DocumentType.FILE,
                    document_metadata={
                        "FILE_NAME": filename,
                        "source_path": str(src),
                    },
                    content="Processing...",
                    content_hash=unique_identifier_hash,  # placeholder until ready
                    unique_identifier_hash=unique_identifier_hash,
                    embedding=None,
                    status=DocumentStatus.pending(),
                    updated_at=get_current_timestamp(),
                    created_by_id=str(user.id),
                )
                session.add(document)
                await session.commit()
                await session.refresh(document)

            log_entry = await task_logger.log_task_start(
                task_name="celestia_forum_ingest",
                source="local_ingest",
                message=f"Ingesting {filename}",
                metadata={"document_id": document.id, "source_path": str(src)},
            )

            # Copy to temp path. The markdown processor unlinks the file it reads.
            tmp_path = tmp_dir / f"{document.id}_{filename}"
            try:
                shutil.copyfile(src, tmp_path)
                await process_file_in_background_with_document(
                    document=document,
                    file_path=str(tmp_path),
                    filename=filename,
                    search_space_id=ss_id,
                    user_id=str(user.id),
                    session=session,
                    task_logger=task_logger,
                    log_entry=log_entry,
                    connector=None,
                    notification=None,
                )
                processed_ok += 1
            except Exception as e:
                processed_failed += 1
                # Best-effort: mark failed if the processor didn't.
                try:
                    document.status = DocumentStatus.failed(str(e))
                    document.updated_at = get_current_timestamp()
                    await session.commit()
                except Exception:
                    await session.rollback()
                print(f"[{idx}/{len(files)}] FAILED: {filename}: {e!s}")
            finally:
                # If the processor didn't unlink for some reason, don't leak tmp files.
                with contextlib.suppress(Exception):
                    os.unlink(tmp_path)

            if idx <= 5 or idx % 100 == 0:
                print(
                    f"[{idx}/{len(files)}] ok={processed_ok} failed={processed_failed} "
                    f"created={created} reindexed={reindexed} skipped_existing={skipped_existing}"
                )

    print(
        f"Done. created={created} reindexed={reindexed} skipped_existing={skipped_existing} "
        f"processed_ok={processed_ok} processed_failed={processed_failed}"
    )
    return 0 if processed_failed == 0 else 2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="test@example.com")
    ap.add_argument("--folder", default=str(DEFAULT_FOLDER))
    ap.add_argument("--search-space-id", type=int, default=None)
    ap.add_argument("--glob", default="thread_*.md")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--reindex-existing",
        action="store_true",
        help="Reprocess already-ingested docs (updates content + embeddings + chunks in-place).",
    )
    args = ap.parse_args()

    # Avoid hard crash if someone mounts a different path.
    folder = Path(args.folder)

    raise SystemExit(
        asyncio.run(
            ingest(
                email=args.email,
                folder=folder,
                search_space_id=args.search_space_id,
                limit=args.limit,
                glob=args.glob,
                dry_run=args.dry_run,
                reindex_existing=args.reindex_existing,
            )
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Ingest a tree of local docs into SurfSense as FILE documents.

Use case:
- You want SurfSense to answer questions like "improve this Celestia script" or
  "generate a flyby script" grounded in:
  - Celestia forum markdown threads
  - Local scripting notes/guides (mirrored to /mnt/data/surfsense/docs)

Why a separate script:
- The forum ingester uses filename-only IDs (thread_123.md) which is fine for a flat folder.
- `scripting_knowledge_base_docs/` is a directory tree and contains many repeated basenames
  like README.md. To avoid collisions, this script uses the *relative path* as the title and
  unique identifier seed.

Run (inside the backend container):
  python /app/scripts/ingest_docs_tree.py --email test@example.com

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


DEFAULT_FOLDER = Path("/ingest/docs/scripting_knowledge_base_docs")
DEFAULT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".adoc",
    ".html",
    ".htm",
    ".rtf",
    ".pdf",
    ".doc",
    ".docx",
}


async def _resolve_search_space_id(session, user_id: str, explicit_id: int | None) -> int:
    if explicit_id is not None:
        return explicit_id

    result = await session.execute(
        select(SearchSpace.id)
        .where(SearchSpace.user_id == user_id)
        .order_by(SearchSpace.created_at.asc())
    )
    search_space_id = result.scalars().first()
    if search_space_id is None:
        raise RuntimeError(f"No search space found for user_id={user_id}")
    return int(search_space_id)


def _iter_files(folder: Path, glob: str, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in folder.glob(glob):
        if not p.is_file():
            continue
        if p.suffix.lower() not in extensions:
            continue
        files.append(p)
    files.sort(key=lambda p: p.as_posix())
    return files


async def ingest(
    *,
    email: str,
    folder: Path,
    search_space_id: int | None,
    limit: int | None,
    glob: str,
    extensions: set[str],
    dry_run: bool,
    reindex_existing: bool,
) -> int:
    if not folder.exists():
        raise RuntimeError(f"Folder not found inside container: {folder}")

    files = _iter_files(folder, glob, extensions)
    if not files:
        raise RuntimeError(f"No files matched {glob} under {folder}")

    if limit is not None:
        files = files[:limit]

    tmp_dir = Path("/tmp/surfsense_ingest_tree")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    reindexed = 0
    skipped_existing = 0
    skipped_unsupported = 0
    processed_ok = 0
    processed_failed = 0

    async with async_session_maker() as session:
        # Silence SentenceTransformer encode() progress bars for bulk runs.
        from app.config import config as app_config
        try:
            st_model = getattr(app_config.embedding_model_instance, "model", None)
            if st_model and hasattr(st_model, "encode"):
                def _quiet_embed(text: str):
                    return st_model.encode(
                        text, convert_to_numpy=True, show_progress_bar=False
                    )
                app_config.embedding_model_instance.embed = _quiet_embed
        except Exception:
            pass

        user = (await session.execute(select(User).where(User.email == email))).scalars().first()
        if not user:
            raise RuntimeError(f"User not found: {email}")
        user_id = str(user.id)

        ss_id = await _resolve_search_space_id(session, user_id, search_space_id)
        task_logger = TaskLoggingService(session, ss_id)

        print(f"User: {email} (id={user_id})")
        print(f"Search space: {ss_id}")
        print(f"Folder: {folder}")
        print(f"Files: {len(files)}")

        for idx, src in enumerate(files, start=1):
            if src.suffix.lower() == ".doc":
                # Current ETL pipeline (docling) supports DOCX but not legacy DOC.
                skipped_unsupported += 1
                if skipped_unsupported <= 5 or skipped_unsupported % 100 == 0:
                    print(f"[{idx}/{len(files)}] skip unsupported .doc: {src.name}")
                continue

            rel = src.relative_to(folder).as_posix()
            unique_identifier_hash = generate_unique_identifier_hash(
                DocumentType.FILE, rel, ss_id
            )

            existing = await check_document_by_unique_identifier(session, unique_identifier_hash)
            if existing and not reindex_existing:
                skipped_existing += 1
                if skipped_existing <= 5 or skipped_existing % 250 == 0:
                    print(f"[{idx}/{len(files)}] skip existing: {rel} (doc_id={existing.id})")
                continue

            if existing:
                reindexed += 1
            else:
                created += 1

            if dry_run:
                if (created + reindexed) <= 5 or (created + reindexed) % 250 == 0:
                    action = "would reindex" if existing else "would ingest"
                    print(f"[{idx}/{len(files)}] {action}: {rel}")
                continue

            if existing:
                document = existing
                document.title = rel
                document.status = DocumentStatus.pending()
                document.updated_at = get_current_timestamp()
                document.document_metadata = {
                    **(document.document_metadata or {}),
                    "FILE_NAME": rel,
                    "source_path": str(src),
                    "reindexed_at": get_current_timestamp().isoformat(),
                }
                await session.commit()
                await session.refresh(document)
            else:
                document = Document(
                    search_space_id=ss_id,
                    title=rel,
                    document_type=DocumentType.FILE,
                    document_metadata={
                        "FILE_NAME": rel,
                        "source_path": str(src),
                    },
                    content="Processing...",
                    content_hash=unique_identifier_hash,  # placeholder until ready
                    unique_identifier_hash=unique_identifier_hash,
                    embedding=None,
                    status=DocumentStatus.pending(),
                    updated_at=get_current_timestamp(),
                    created_by_id=user_id,
                )
                session.add(document)
                await session.commit()
                await session.refresh(document)

            log_entry = await task_logger.log_task_start(
                task_name="docs_tree_ingest",
                source="local_ingest",
                message=f"Ingesting {rel}",
                metadata={"document_id": document.id, "source_path": str(src)},
            )

            tmp_path = tmp_dir / f"{document.id}_{src.name}"
            try:
                shutil.copyfile(src, tmp_path)
                
                await process_file_in_background_with_document(
                    document=document,
                    file_path=str(tmp_path),
                    filename=src.name,
                    search_space_id=ss_id,
                    user_id=user_id,
                    session=session,
                    task_logger=task_logger,
                    log_entry=log_entry,
                    connector=None,
                    notification=None,
                )
                processed_ok += 1
            except Exception as e:
                processed_failed += 1
                try:
                    document.status = DocumentStatus.failed(str(e))
                    document.updated_at = get_current_timestamp()
                    await session.commit()
                except Exception:
                    await session.rollback()
                print(f"[{idx}/{len(files)}] FAILED: {rel}: {e!s}")
            finally:
                with contextlib.suppress(Exception):
                    os.unlink(tmp_path)

            if idx <= 5 or idx % 100 == 0:
                print(
                    f"[{idx}/{len(files)}] ok={processed_ok} failed={processed_failed} "
                    f"created={created} reindexed={reindexed} skipped_existing={skipped_existing} "
                    f"skipped_unsupported={skipped_unsupported}"
                )

    print(
        f"Done. created={created} reindexed={reindexed} skipped_existing={skipped_existing} "
        f"skipped_unsupported={skipped_unsupported} processed_ok={processed_ok} "
        f"processed_failed={processed_failed}"
    )
    return 0 if processed_failed == 0 else 2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="test@example.com")
    ap.add_argument("--folder", default=str(DEFAULT_FOLDER))
    ap.add_argument("--search-space-id", type=int, default=None)
    ap.add_argument("--glob", default="**/*")
    ap.add_argument(
        "--extensions",
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help="Comma-separated file extensions to ingest (default includes md/txt/rst/adoc/pdf/doc/docx).",
    )
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--reindex-existing",
        action="store_true",
        help="Reprocess already-ingested docs (updates content + embeddings + chunks in-place).",
    )
    args = ap.parse_args()

    folder = Path(args.folder)
    extensions = {e.strip().lower() for e in args.extensions.split(",") if e.strip()}
    if not extensions:
        raise SystemExit("No extensions configured. Example: --extensions .md,.pdf")

    try:
        exit_code = asyncio.run(
            ingest(
                email=args.email,
                folder=folder,
                search_space_id=args.search_space_id,
                limit=args.limit,
                glob=args.glob,
                extensions=extensions,
                dry_run=args.dry_run,
                reindex_existing=args.reindex_existing,
            )
        )
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()

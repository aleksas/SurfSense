#!/usr/bin/env python3
"""
Ingest Celestia forum markdown as one SurfSense document per post.

Why this exists:
- Thread-level docs are too large and produce weak retrieval for exact-post questions.
- Post-level docs ensure chunks never cross post boundaries and preserve post metadata.

Run (inside backend container):
  python /app/scripts/ingest_celestia_forum_posts.py --email test@example.com --delete-thread-level-docs

Notes:
- Requires /ingest/docs mount (see docker-compose.yml).
- Only files matching thread_<numeric>.md are ingested.
- Duplicate post blocks in the same thread are deduped by (post_id, normalized_body).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select, text

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
THREAD_FILE_RE = re.compile(r"^thread_(?P<thread_id>\d+)\.md$")
POST_HEADER_RE = re.compile(
    r"^## Post\s+(?P<post_num>\d+)\s+\(ID:\s*(?P<post_id>[^,\)]+),\s*Author:\s*(?P<author>[^\)]+)\)\s*$",
    re.MULTILINE,
)


@dataclass
class ForumPost:
    thread_id: str
    thread_file: str
    post_num: str
    post_id: str
    author: str
    body: str
    source_path: str


def _normalize_ws(text_value: str) -> str:
    return re.sub(r"\s+", " ", text_value).strip()


def _sort_key(path: Path) -> tuple[int, int | str]:
    m = THREAD_FILE_RE.match(path.name)
    if m:
        return (0, int(m.group("thread_id")))
    return (1, path.name)


def _clean_post_body(raw: str) -> str:
    body = raw.strip()
    if body.startswith("---"):
        body = body[3:].lstrip()
    if body.endswith("---"):
        body = body[:-3].rstrip()
    return body.strip()


def extract_posts_from_thread(path: Path) -> tuple[list[ForumPost], int]:
    text_value = path.read_text(encoding="utf-8", errors="ignore")
    m_thread = THREAD_FILE_RE.match(path.name)
    if not m_thread:
        return [], 0
    thread_id = m_thread.group("thread_id")

    headers = list(POST_HEADER_RE.finditer(text_value))
    if not headers:
        return [], 0

    posts: list[ForumPost] = []
    seen: set[tuple[str, str]] = set()
    dup_count = 0
    for idx, header in enumerate(headers):
        body_start = header.end()
        body_end = headers[idx + 1].start() if idx + 1 < len(headers) else len(text_value)
        raw_body = text_value[body_start:body_end]
        body = _clean_post_body(raw_body)
        if not body:
            continue

        post_id = header.group("post_id").strip()
        post_num = header.group("post_num").strip()
        author = header.group("author").strip()

        dedupe_key = (post_id, _normalize_ws(body).lower())
        if dedupe_key in seen:
            dup_count += 1
            continue
        seen.add(dedupe_key)

        posts.append(
            ForumPost(
                thread_id=thread_id,
                thread_file=path.name,
                post_num=post_num,
                post_id=post_id,
                author=author,
                body=body,
                source_path=str(path),
            )
        )

    return posts, dup_count


def build_post_markdown(post: ForumPost) -> str:
    return (
        f"# Forum Post\n\n"
        f"- Thread ID: {post.thread_id}\n"
        f"- Thread File: {post.thread_file}\n"
        f"- Post Number: {post.post_num}\n"
        f"- Post ID: {post.post_id}\n"
        f"- Author: {post.author}\n\n"
        f"---\n\n"
        f"{post.body}\n"
    )


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


async def _delete_docs(
    *,
    session,
    search_space_id: int,
    title_regex: str,
    source_like: str,
    dry_run: bool,
) -> int:
    if dry_run:
        count_query = text(
            """
            SELECT COUNT(*)::int AS n
            FROM documents
            WHERE search_space_id = :search_space_id
              AND title ~ :title_regex
              AND COALESCE(document_metadata->>'source_path', '') LIKE :source_like
            """
        )
        row = (await session.execute(count_query, {
            "search_space_id": search_space_id,
            "title_regex": title_regex,
            "source_like": source_like,
        })).mappings().first()
        return int(row["n"]) if row else 0

    delete_query = text(
        """
        DELETE FROM documents
        WHERE search_space_id = :search_space_id
          AND title ~ :title_regex
          AND COALESCE(document_metadata->>'source_path', '') LIKE :source_like
        """
    )
    result = await session.execute(delete_query, {
        "search_space_id": search_space_id,
        "title_regex": title_regex,
        "source_like": source_like,
    })
    await session.commit()
    return int(result.rowcount or 0)


async def ingest(
    *,
    email: str,
    folder: Path,
    search_space_id: int | None,
    glob: str,
    thread_limit: int | None,
    post_limit: int | None,
    dry_run: bool,
    reindex_existing: bool,
    delete_thread_level_docs: bool,
    delete_existing_post_docs: bool,
) -> int:
    if not folder.exists():
        raise RuntimeError(f"Folder not found inside container: {folder}")

    files = sorted((p for p in folder.glob(glob) if p.is_file()), key=_sort_key)
    if thread_limit is not None:
        files = files[:thread_limit]

    tmp_dir = Path("/tmp/surfsense_ingest_posts")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    reindexed = 0
    skipped_existing = 0
    skipped_non_numeric_thread = 0
    skipped_empty = 0
    skipped_duplicates = 0
    processed_ok = 0
    processed_failed = 0
    processed_posts = 0

    async with async_session_maker() as session:
        # Silence SentenceTransformer progress bars for bulk runs.
        from app.config import config as app_config

        try:
            st_model = app_config.embedding_model_instance.model

            def _quiet_embed(text_value: str):
                return st_model.encode(  # type: ignore[attr-defined]
                    text_value, convert_to_numpy=True, show_progress_bar=False
                )

            app_config.embedding_model_instance.embed = _quiet_embed  # type: ignore[assignment]
        except Exception:
            pass

        user = (await session.execute(select(User).where(User.email == email))).scalars().first()
        if not user:
            raise RuntimeError(f"User not found: {email}")
        user_id = str(user.id)

        ss_id = await _resolve_search_space_id(session, user_id, search_space_id)
        task_logger = TaskLoggingService(session, ss_id)

        if delete_thread_level_docs:
            n = await _delete_docs(
                session=session,
                search_space_id=ss_id,
                title_regex=r"^thread_[0-9]+\.md$",
                source_like="%/celestia_forum_data/thread_%",
                dry_run=dry_run,
            )
            msg = "would delete" if dry_run else "deleted"
            print(f"Thread-level forum docs {msg}: {n}")

        if delete_existing_post_docs:
            n = await _delete_docs(
                session=session,
                search_space_id=ss_id,
                title_regex=r"^thread_[0-9]+__post_[^/]+\.md$",
                source_like="%/celestia_forum_data/thread_%",
                dry_run=dry_run,
            )
            msg = "would delete" if dry_run else "deleted"
            print(f"Post-level forum docs {msg}: {n}")

        print(f"User: {email} (id={user_id})")
        print(f"Search space: {ss_id}")
        print(f"Folder: {folder}")
        print(f"Thread files considered: {len(files)}")

        for file_idx, src in enumerate(files, start=1):
            m = THREAD_FILE_RE.match(src.name)
            if not m:
                skipped_non_numeric_thread += 1
                continue

            posts, dup_count = extract_posts_from_thread(src)
            skipped_duplicates += dup_count
            if not posts:
                skipped_empty += 1
                continue

            for post in posts:
                if post_limit is not None and processed_posts >= post_limit:
                    break

                title = f"thread_{post.thread_id}__post_{post.post_id}.md"
                unique_identifier_hash = generate_unique_identifier_hash(DocumentType.FILE, title, ss_id)
                existing = await check_document_by_unique_identifier(session, unique_identifier_hash)

                if existing and not reindex_existing:
                    skipped_existing += 1
                    processed_posts += 1
                    continue

                if existing:
                    reindexed += 1
                else:
                    created += 1

                if dry_run:
                    processed_posts += 1
                    continue

                metadata = {
                    "FILE_NAME": title,
                    "source_path": str(src),
                    "source_fragment": f"post:{post.post_id}",
                    "forum_thread_id": post.thread_id,
                    "forum_thread_file": post.thread_file,
                    "forum_post_id": post.post_id,
                    "forum_post_num": post.post_num,
                    "forum_author": post.author,
                    "forum_ingest_mode": "post",
                    "reindexed_at": get_current_timestamp().isoformat(),
                }

                if existing:
                    document = existing
                    document.title = title
                    document.status = DocumentStatus.pending()
                    document.updated_at = get_current_timestamp()
                    document.document_metadata = {
                        **(document.document_metadata or {}),
                        **metadata,
                    }
                    await session.commit()
                    await session.refresh(document)
                else:
                    document = Document(
                        search_space_id=ss_id,
                        title=title,
                        document_type=DocumentType.FILE,
                        document_metadata=metadata,
                        content="Processing...",
                        content_hash=unique_identifier_hash,
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
                    task_name="celestia_forum_post_ingest",
                    source="local_ingest",
                    message=f"Ingesting {title}",
                    metadata={"document_id": document.id, "source_path": str(src)},
                )

                tmp_path = tmp_dir / f"{document.id}_{title}"
                try:
                    tmp_path.write_text(build_post_markdown(post), encoding="utf-8")
                    await process_file_in_background_with_document(
                        document=document,
                        file_path=str(tmp_path),
                        filename=title,
                        search_space_id=ss_id,
                        user_id=user_id,
                        session=session,
                        task_logger=task_logger,
                        log_entry=log_entry,
                        connector=None,
                        notification=None,
                    )
                    processed_ok += 1
                except Exception as exc:
                    processed_failed += 1
                    try:
                        document.status = DocumentStatus.failed(str(exc))
                        document.updated_at = get_current_timestamp()
                        await session.commit()
                    except Exception:
                        await session.rollback()
                    print(f"FAILED [{title}]: {exc!s}")
                finally:
                    with contextlib.suppress(Exception):
                        os.unlink(tmp_path)

                processed_posts += 1

            if file_idx <= 5 or file_idx % 100 == 0:
                print(
                    f"[thread {file_idx}/{len(files)}] posts_seen={processed_posts} ok={processed_ok} "
                    f"failed={processed_failed} created={created} reindexed={reindexed} "
                    f"skipped_existing={skipped_existing} skipped_dups={skipped_duplicates}"
                )

            if post_limit is not None and processed_posts >= post_limit:
                break

    print(
        "Done. "
        f"posts_seen={processed_posts} created={created} reindexed={reindexed} "
        f"skipped_existing={skipped_existing} skipped_non_numeric_thread={skipped_non_numeric_thread} "
        f"skipped_empty={skipped_empty} skipped_duplicates={skipped_duplicates} "
        f"processed_ok={processed_ok} processed_failed={processed_failed}"
    )
    return 0 if processed_failed == 0 else 2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="test@example.com")
    ap.add_argument("--folder", default=str(DEFAULT_FOLDER))
    ap.add_argument("--search-space-id", type=int, default=None)
    ap.add_argument("--glob", default="thread_*.md")
    ap.add_argument("--thread-limit", type=int, default=None)
    ap.add_argument("--post-limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--reindex-existing",
        action="store_true",
        help="Reprocess already-ingested post-level docs.",
    )
    ap.add_argument(
        "--delete-thread-level-docs",
        action="store_true",
        help="Delete old forum docs titled thread_<id>.md before ingesting post-level docs.",
    )
    ap.add_argument(
        "--delete-existing-post-docs",
        action="store_true",
        help="Delete previously ingested post-level docs before ingesting fresh post-level docs.",
    )
    args = ap.parse_args()

    raise SystemExit(
        asyncio.run(
            ingest(
                email=args.email,
                folder=Path(args.folder),
                search_space_id=args.search_space_id,
                glob=args.glob,
                thread_limit=args.thread_limit,
                post_limit=args.post_limit,
                dry_run=args.dry_run,
                reindex_existing=args.reindex_existing,
                delete_thread_level_docs=args.delete_thread_level_docs,
                delete_existing_post_docs=args.delete_existing_post_docs,
            )
        )
    )


if __name__ == "__main__":
    main()

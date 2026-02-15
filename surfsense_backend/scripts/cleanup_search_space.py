#!/usr/bin/env python3
"""
Cleanup script to delete all documents and chunks for a specific search space.
Useful for wiping a space before re-ingesting fresh data.

Run (inside backend container):
  python /app/scripts/cleanup_search_space.py --search-space-id 1
"""

import argparse
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import config

async def cleanup(search_space_id: int, dry_run: bool):
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        async with session_maker() as session:
            # 1. Count documents
            count_query = text(
                "SELECT COUNT(*)::int FROM documents WHERE search_space_id = :ss_id"
            )
            result = await session.execute(count_query, {"ss_id": search_space_id})
            doc_count = result.scalar() or 0

            if doc_count == 0:
                print(f"No documents found for search space {search_space_id}.")
                return

            if dry_run:
                print(f"[DRY RUN] Would delete {doc_count} documents and their associated chunks for search space {search_space_id}.")
                return

            print(f"Deleting {doc_count} documents for search space {search_space_id}...")
            
            # Chunks have ON DELETE CASCADE on document_id in the DB, 
            # so we just delete from documents.
            delete_query = text(
                "DELETE FROM documents WHERE search_space_id = :ss_id"
            )
            result = await session.execute(delete_query, {"ss_id": search_space_id})
            await session.commit()
            
            print(f"Successfully deleted {result.rowcount} documents.")
    finally:
        await engine.dispose()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-space-id", type=int, required=True, help="ID of the search space to wipe.")
    ap.add_argument("--dry-run", action="store_true", help="Count but don't delete.")
    args = ap.parse_args()

    asyncio.run(cleanup(args.search_space_id, args.dry_run))

if __name__ == "__main__":
    main()

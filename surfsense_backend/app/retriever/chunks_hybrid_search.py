from datetime import datetime
import re


def _extract_longest_quoted_phrase(query_text: str, *, min_len: int = 20) -> str | None:
    phrases = re.findall(r"\"([^\"]+)\"", query_text)
    phrases = [p.strip() for p in phrases if len(p.strip()) >= min_len]
    return max(phrases, key=len) if phrases else None


class ChucksHybridSearchRetriever:
    def __init__(self, db_session):
        """
        Initialize the hybrid search retriever with a database session.

        Args:
            db_session: SQLAlchemy AsyncSession from FastAPI dependency injection
        """
        self.db_session = db_session
        # Prevent huge context payloads from very large documents.
        self.max_chunks_per_document = 60

    async def vector_search(
        self,
        query_text: str,
        top_k: int,
        search_space_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list:
        """
        Perform vector similarity search on chunks.

        Args:
            query_text: The search query text
            top_k: Number of results to return
            search_space_id: The search space ID to search within
            start_date: Optional start date for filtering documents by updated_at
            end_date: Optional end date for filtering documents by updated_at

        Returns:
            List of chunks sorted by vector similarity
        """
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        from app.config import config
        from app.db import Chunk, Document

        # Get embedding for the query
        embedding_model = config.embedding_model_instance
        query_embedding = (
            embedding_model.embed_query(query_text)
            if hasattr(embedding_model, "embed_query")
            else embedding_model.embed(query_text)
        )

        # Build the query filtered by search space
        query = (
            select(Chunk)
            .options(joinedload(Chunk.document).joinedload(Document.search_space))
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.search_space_id == search_space_id)
        )

        # Add time-based filtering if provided
        if start_date is not None:
            query = query.where(Document.updated_at >= start_date)
        if end_date is not None:
            query = query.where(Document.updated_at <= end_date)

        # Add vector similarity ordering
        query = query.order_by(Chunk.embedding.op("<=>")(query_embedding)).limit(top_k)

        # Execute the query
        result = await self.db_session.execute(query)
        chunks = result.scalars().all()

        return chunks

    async def full_text_search(
        self,
        query_text: str,
        top_k: int,
        search_space_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list:
        """
        Perform full-text keyword search on chunks.

        Args:
            query_text: The search query text
            top_k: Number of results to return
            search_space_id: The search space ID to search within
            start_date: Optional start date for filtering documents by updated_at
            end_date: Optional end date for filtering documents by updated_at

        Returns:
            List of chunks sorted by text relevance
        """
        from sqlalchemy import func, select
        from sqlalchemy.orm import joinedload

        from app.db import Chunk, Document

        # Full-text search should work across mixed languages and quoted phrases.
        # - "simple" avoids English-only stemming/stopwords (important for forum data).
        # - Include the document title to make filename/title lookups work (PDFs, docs).
        # - If the user includes a long quoted phrase, prefer phrase search.
        quoted = _extract_longest_quoted_phrase(query_text)
        tsvector = func.to_tsvector("simple", Chunk.content).op("||")(
            func.to_tsvector("simple", Document.title)
        )
        tsquery = (
            func.phraseto_tsquery("simple", quoted)
            if quoted
            else func.websearch_to_tsquery("simple", query_text)
        )

        # Build the query filtered by search space
        query = (
            select(Chunk)
            .options(joinedload(Chunk.document).joinedload(Document.search_space))
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.search_space_id == search_space_id)
            .where(
                tsvector.op("@@")(tsquery)
            )  # Only include results that match the query
        )

        # Add time-based filtering if provided
        if start_date is not None:
            query = query.where(Document.updated_at >= start_date)
        if end_date is not None:
            query = query.where(Document.updated_at <= end_date)

        # Add text search ranking
        query = query.order_by(func.ts_rank_cd(tsvector, tsquery).desc()).limit(top_k)

        # Execute the query
        result = await self.db_session.execute(query)
        chunks = result.scalars().all()

        return chunks

    async def hybrid_search(
        self,
        query_text: str,
        top_k: int,
        search_space_id: int,
        document_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list:
        """
        Hybrid search that returns **documents** (not individual chunks).

        Each returned item is a document-grouped dict that preserves real DB chunk IDs so
        downstream agents can cite with `[citation:<chunk_id>]`.

        Args:
            query_text: The search query text
            top_k: Number of documents to return
            search_space_id: The search space ID to search within
            document_type: Optional document type to filter results (e.g., "FILE", "CRAWLED_URL")
            start_date: Optional start date for filtering documents by updated_at
            end_date: Optional end date for filtering documents by updated_at

        Returns:
            List of dictionaries containing document data and relevance scores. Each dict contains:
              - chunk_id: a "primary" chunk id for compatibility (best-ranked chunk for the doc)
              - content: concatenated chunk content (useful for reranking)
              - chunks: list[{chunk_id, content}] for citation-aware prompting
              - document: {id, title, document_type, metadata}
        """
        from sqlalchemy import case, func, select, text
        from sqlalchemy.orm import joinedload

        from app.config import config
        from app.db import Chunk, Document, DocumentType

        # Get embedding for the query
        embedding_model = config.embedding_model_instance
        query_embedding = (
            embedding_model.embed_query(query_text)
            if hasattr(embedding_model, "embed_query")
            else embedding_model.embed(query_text)
        )

        quoted = _extract_longest_quoted_phrase(query_text)

        # RRF constants
        k = 60
        n_results = top_k * 5  # Fetch extra chunks for better document-level fusion

        # Full-text search should work across mixed languages and quoted phrases.
        # Include document title for better filename/title recall.
        tsvector = func.to_tsvector("simple", Chunk.content).op("||")(
            func.to_tsvector("simple", Document.title)
        )
        tsquery = (
            func.phraseto_tsquery("simple", quoted)
            if quoted
            else func.websearch_to_tsquery("simple", query_text)
        )

        # Base conditions for chunk filtering - search space is required
        base_conditions = [Document.search_space_id == search_space_id]

        # Add document type filter if provided
        if document_type is not None:
            # Convert string to enum value if needed
            if isinstance(document_type, str):
                try:
                    doc_type_enum = DocumentType[document_type]
                    base_conditions.append(Document.document_type == doc_type_enum)
                except KeyError:
                    # If the document type doesn't exist in the enum, return empty results
                    return []
            else:
                base_conditions.append(Document.document_type == document_type)

        # Add time-based filtering if provided
        if start_date is not None:
            base_conditions.append(Document.updated_at >= start_date)
        if end_date is not None:
            base_conditions.append(Document.updated_at <= end_date)

        # CTE for semantic search filtered by search space
        semantic_search_cte = (
            select(
                Chunk.id,
                func.rank()
                .over(order_by=Chunk.embedding.op("<=>")(query_embedding))
                .label("rank"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(*base_conditions)
        )

        semantic_search_cte = (
            semantic_search_cte.order_by(Chunk.embedding.op("<=>")(query_embedding))
            .limit(n_results)
            .cte("semantic_search")
        )

        # CTE for keyword search filtered by search space
        keyword_search_cte = (
            select(
                Chunk.id,
                func.rank()
                .over(order_by=func.ts_rank_cd(tsvector, tsquery).desc())
                .label("rank"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(*base_conditions)
            .where(tsvector.op("@@")(tsquery))
        )

        keyword_search_cte = (
            keyword_search_cte.order_by(func.ts_rank_cd(tsvector, tsquery).desc())
            .limit(n_results)
            .cte("keyword_search")
        )

        # Prefer phrase/keyword ranking for long quoted phrases, but DO NOT return
        # an empty set if the phrase doesn't match due to encoding/normalization
        # differences in the corpus (common in scraped forum data). In that case,
        # fall back to hybrid (semantic + keyword) so the user still gets results.

        async def _exec_hybrid() -> list:
            # Source boost: Prioritize EXTENSION documents (scraped leads) over general registry files.
            source_boost = case(
                (Document.document_type == DocumentType.EXTENSION, 0.5),
                else_=0.0
            ).label("source_boost")

            final_query = (
                select(
                    Chunk,
                    (
                        func.coalesce(1.0 / (k + semantic_search_cte.c.rank), 0.0)
                        + func.coalesce(1.0 / (k + keyword_search_cte.c.rank), 0.0)
                        + source_boost
                    ).label("score"),
                )
                .select_from(
                    semantic_search_cte.outerjoin(
                        keyword_search_cte,
                        semantic_search_cte.c.id == keyword_search_cte.c.id,
                        full=True,
                    )
                )
                .join(
                    Chunk,
                    Chunk.id
                    == func.coalesce(semantic_search_cte.c.id, keyword_search_cte.c.id),
                )
                .join(Document, Chunk.document_id == Document.id)
                .options(joinedload(Chunk.document))
                .order_by(text("score DESC"))
                .limit(n_results)
            )
            result = await self.db_session.execute(final_query)
            return result.all()

        if quoted:
            keyword_only_query = (
                select(
                    Chunk,
                    func.ts_rank_cd(tsvector, tsquery).label("score"),
                )
                .join(Document, Chunk.document_id == Document.id)
                .where(*base_conditions)
                .where(tsvector.op("@@")(tsquery))
                .options(joinedload(Chunk.document))
                .order_by(func.ts_rank_cd(tsvector, tsquery).desc())
                .limit(n_results)
            )
            result = await self.db_session.execute(keyword_only_query)
            chunks_with_scores = result.all()
            if not chunks_with_scores:
                chunks_with_scores = await _exec_hybrid()
        else:
            chunks_with_scores = await _exec_hybrid()

        # If no results were found, return an empty list
        if not chunks_with_scores:
            return []

        # Convert to serializable dictionaries
        serialized_chunk_results: list[dict] = []
        for chunk, score in chunks_with_scores:
            serialized_chunk_results.append(
                {
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "score": float(score),  # Ensure score is a Python float
                    "document": {
                        "id": chunk.document.id,
                        "title": chunk.document.title,
                        "document_type": chunk.document.document_type.value
                        if hasattr(chunk.document, "document_type")
                        else None,
                        "metadata": chunk.document.document_metadata,
                    },
                }
            )

        # Group by document, preserving ranking order by best chunk rank
        doc_scores: dict[int, float] = {}
        doc_order: list[int] = []
        for item in serialized_chunk_results:
            doc_id = item.get("document", {}).get("id")
            if doc_id is None:
                continue
            if doc_id not in doc_scores:
                doc_scores[doc_id] = item.get("score", 0.0)
                doc_order.append(doc_id)
            else:
                # Use the best score as doc score
                doc_scores[doc_id] = max(doc_scores[doc_id], item.get("score", 0.0))

        # Keep only top_k documents by initial rank order.
        doc_ids = doc_order[:top_k]
        if not doc_ids:
            return []

        # Assemble final doc-grouped results in the same order as doc_ids.
        # IMPORTANT:
        # Keep the highest-scoring chunks from the hybrid result order (relevance-first),
        # instead of reloading chunks by chunk_id order, which biases toward document starts
        # and can hide the actual query-matching snippets.
        doc_map: dict[int, dict] = {
            doc_id: {
                "document_id": doc_id,
                "content": "",
                "score": float(doc_scores.get(doc_id, 0.0)),
                "chunks": [],
                "document": {},
                "source": None,
            }
            for doc_id in doc_ids
        }

        per_doc_seen_chunk_ids: dict[int, set[int]] = {doc_id: set() for doc_id in doc_ids}

        for item in serialized_chunk_results:
            doc_info = item.get("document", {}) or {}
            doc_id = doc_info.get("id")
            if doc_id not in doc_map:
                continue

            chunk_id = item.get("chunk_id")
            if chunk_id is None:
                continue

            doc_entry = doc_map[doc_id]
            if len(doc_entry["chunks"]) >= self.max_chunks_per_document:
                continue
            if chunk_id in per_doc_seen_chunk_ids[doc_id]:
                continue

            per_doc_seen_chunk_ids[doc_id].add(chunk_id)
            doc_entry["chunks"].append(
                {"chunk_id": chunk_id, "content": item.get("content", "")}
            )

            if not doc_entry["document"]:
                doc_entry["document"] = {
                    "id": doc_id,
                    "title": doc_info.get("title"),
                    "document_type": doc_info.get("document_type"),
                    "metadata": doc_info.get("metadata") or {},
                }
                doc_entry["source"] = doc_info.get("document_type")

        # Fill concatenated content (useful for reranking)
        final_docs: list[dict] = []
        for doc_id in doc_ids:
            entry = doc_map[doc_id]
            entry["content"] = "\n\n".join(
                c["content"] for c in entry.get("chunks", []) if c.get("content")
            )
            final_docs.append(entry)

        return final_docs

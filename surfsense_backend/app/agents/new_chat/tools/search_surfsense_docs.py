"""
Surfsense documentation search tool.

This tool allows the agent to search the pre-indexed Surfsense documentation
to help users with questions about how to use the application.

The documentation is indexed at deployment time from MDX files and stored
in dedicated tables (surfsense_docs_documents, surfsense_docs_chunks).
"""

import json

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.db import SurfsenseDocsChunk, SurfsenseDocsDocument
from app.services.connector_service import ConnectorService

# Queries containing these terms are likely asking about SurfSense product usage
# rather than user-ingested content.
SURFSENSE_PRODUCT_KEYWORDS = (
    "surfsense",
    "search space",
    "connector",
    "connectors",
    "browser extension",
    "mcp",
    "rbac",
    "permissions",
    "llm config",
    "image generation",
    "podcast generation",
    "docker",
    "setup",
    "installation",
    "install",
    "api key",
)


def _is_surfsense_product_query(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    return any(keyword in q for keyword in SURFSENSE_PRODUCT_KEYWORDS)


def format_surfsense_docs_results(results: list[tuple]) -> str:
    """
    Format search results into XML structure for the LLM context.

    Uses the same XML structure as format_documents_for_context from knowledge_base.py
    but with 'doc-' prefix on chunk IDs. This allows:
    - LLM to use consistent [citation:doc-XXX] format
    - Frontend to detect 'doc-' prefix and route to surfsense docs endpoint

    Args:
        results: List of (chunk, document) tuples from the database query

    Returns:
        Formatted XML string with documentation content and citation-ready chunks
    """
    if not results:
        return "No relevant Surfsense documentation found for your query."

    # Group chunks by document
    grouped: dict[int, dict] = {}
    for chunk, doc in results:
        if doc.id not in grouped:
            grouped[doc.id] = {
                "document_id": f"doc-{doc.id}",
                "document_type": "SURFSENSE_DOCS",
                "title": doc.title,
                "url": doc.source,
                "metadata": {"source": doc.source},
                "chunks": [],
            }
        grouped[doc.id]["chunks"].append(
            {
                "chunk_id": f"doc-{chunk.id}",
                "content": chunk.content,
            }
        )

    # Render XML matching format_documents_for_context structure
    parts: list[str] = []
    for g in grouped.values():
        metadata_json = json.dumps(g["metadata"], ensure_ascii=False)

        parts.append("<document>")
        parts.append("<document_metadata>")
        parts.append(f"  <document_id>{g['document_id']}</document_id>")
        parts.append(f"  <document_type>{g['document_type']}</document_type>")
        parts.append(f"  <title><![CDATA[{g['title']}]]></title>")
        parts.append(f"  <url><![CDATA[{g['url']}]]></url>")
        parts.append(f"  <metadata_json><![CDATA[{metadata_json}]]></metadata_json>")
        parts.append("</document_metadata>")
        parts.append("")
        parts.append("<document_content>")

        for ch in g["chunks"]:
            parts.append(
                f"  <chunk id='{ch['chunk_id']}'><![CDATA[{ch['content']}]]></chunk>"
            )

        parts.append("</document_content>")
        parts.append("</document>")
        parts.append("")

    return "\n".join(parts).strip()


async def search_surfsense_docs_async(
    query: str,
    db_session: AsyncSession,
    top_k: int = 10,
    search_space_id: int | None = None,
    connector_service: ConnectorService | None = None,
    available_connectors: list[str] | None = None,
) -> str:
    """
    Search Surfsense documentation using vector similarity.

    Args:
        query: The search query about Surfsense usage
        db_session: Database session for executing queries
        top_k: Number of results to return

    Returns:
        Formatted string with relevant documentation content
    """
    # If this does not look like a SurfSense product question, route to the
    # personal knowledge base search so user-ingested docs are returned.
    if (
        not _is_surfsense_product_query(query)
        and search_space_id is not None
        and connector_service is not None
    ):
        from app.agents.new_chat.tools.knowledge_base import search_knowledge_base_async

        kb_results = await search_knowledge_base_async(
            query=query,
            search_space_id=search_space_id,
            db_session=db_session,
            connector_service=connector_service,
            top_k=top_k,
            available_connectors=available_connectors,
        )
        if kb_results:
            return kb_results

    # Get embedding for the query
    query_embedding = config.embedding_model_instance.embed(query)

    # Vector similarity search on chunks, joining with documents
    stmt = (
        select(SurfsenseDocsChunk, SurfsenseDocsDocument)
        .join(
            SurfsenseDocsDocument,
            SurfsenseDocsChunk.document_id == SurfsenseDocsDocument.id,
        )
        .order_by(SurfsenseDocsChunk.embedding.op("<=>")(query_embedding))
        .limit(top_k)
    )

    result = await db_session.execute(stmt)
    rows = result.all()

    return format_surfsense_docs_results(rows)


def create_search_surfsense_docs_tool(
    db_session: AsyncSession,
    search_space_id: int | None = None,
    connector_service: ConnectorService | None = None,
    available_connectors: list[str] | None = None,
):
    """
    Factory function to create the search_surfsense_docs tool.

    Args:
        db_session: Database session for executing queries

    Returns:
        A configured tool function for searching Surfsense documentation
    """

    @tool
    async def search_surfsense_docs(query: str, top_k: int = 10) -> str:
        """
        Search Surfsense documentation for help with using the application.

        Use this tool when the user asks questions about:
        - How to use Surfsense features
        - Installation and setup instructions
        - Configuration options and settings
        - Troubleshooting common issues
        - Available connectors and integrations
        - Browser extension usage
        - API documentation

        This searches the official Surfsense documentation that was indexed
        at deployment time.

        If the query appears to be about user content (not SurfSense product usage),
        the tool automatically routes the request to the personal knowledge base search.

        Args:
            query: The search query about Surfsense usage or features
            top_k: Number of documentation chunks to retrieve (default: 10)

        Returns:
            Relevant documentation content formatted with chunk IDs for citations
        """
        return await search_surfsense_docs_async(
            query=query,
            db_session=db_session,
            top_k=top_k,
            search_space_id=search_space_id,
            connector_service=connector_service,
            available_connectors=available_connectors,
        )

    return search_surfsense_docs

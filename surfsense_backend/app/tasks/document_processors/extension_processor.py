"""
Extension document processor for SurfSense browser extension.
"""

import logging
import re
from html import unescape

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, DocumentType
from app.schemas import ExtensionDocumentContent
from app.services.llm_service import get_user_long_context_llm
from app.services.task_logging_service import TaskLoggingService
from app.utils.document_converters import (
    create_document_chunks,
    generate_content_hash,
    generate_document_summary,
    generate_unique_identifier_hash,
)

from .base import (
    check_document_by_unique_identifier,
    get_current_timestamp,
)

_HTML_TAG_PATTERN = re.compile(r"</?[a-zA-Z][^>]{0,200}>")
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_IMAGE_ONLY_LINK_PATTERN = re.compile(
    r"^\s*(?:!\[.*?\]\(.*?\)|\[!\[.*?\]\(.*?\)\]\(.*?\))\s*$"
)
_STANDALONE_LINK_LINE_PATTERN = re.compile(r"^\s*\[[^\]]{1,80}\]\(https?://[^)]+\)\s*$")
_BOILERPLATE_SECTION_HEADERS = (
    "## latest news",
    "### latest news",
    "## we also recommend",
    "### we also recommend",
    "we also recommend",
    "## map",
    "### map",
)
_TRACKING_MARKERS = (
    "smartadserver.com",
    "creatives.sascdn.com",
    "gdpr_consent=",
    "utm_campaign=",
    "opdt=",
    "reqid=",
    "go=https",
)


def _strip_markdown_boilerplate(text: str) -> str:
    """Drop common navigation/ads/footer boilerplate from markdown-like page dumps."""
    out: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        low = line.lower()

        if low in _BOILERPLATE_SECTION_HEADERS:
            break
        if any(marker in low for marker in _TRACKING_MARKERS):
            continue
        if low.startswith("[show map]("):
            continue
        if _IMAGE_ONLY_LINK_PATTERN.match(line):
            continue
        if _STANDALONE_LINK_LINE_PATTERN.match(line):
            continue
        if line.count("](") >= 6 and len(line) > 240:
            continue

        out.append(raw_line)

    cleaned = "\n".join(out).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def normalize_extension_page_content(raw_content: str) -> str:
    """
    Normalize extension page content to markdown/plain text for indexing.

    Extension captures may include raw HTML depending on source page/extractor.
    This keeps chunks clean for lexical/vector search and chat rendering.
    """
    text = (raw_content or "").strip()
    if not text:
        return ""

    text = _HTML_COMMENT_PATTERN.sub(" ", text)
    sample = text[:4000].lower()
    looks_like_html = "<!doctype html" in sample or _HTML_TAG_PATTERN.search(sample)

    if looks_like_html:
        try:
            from markdownify import markdownify

            text = markdownify(text, heading_style="ATX", strip=["script", "style"])
        except Exception:
            # Fallback to simple tag stripping if markdown conversion fails.
            text = re.sub(r"<[^>]+>", " ", text)

    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = _strip_markdown_boilerplate(text)
    return text.strip()


async def add_extension_received_document(
    session: AsyncSession,
    content: ExtensionDocumentContent,
    search_space_id: int,
    user_id: str,
) -> Document | None:
    """
    Process and store document content received from the SurfSense Extension.

    Args:
        session: Database session
        content: Document content from extension
        search_space_id: ID of the search space
        user_id: ID of the user

    Returns:
        Document object if successful, None if failed
    """
    task_logger = TaskLoggingService(session, search_space_id)

    # Log task start
    log_entry = await task_logger.log_task_start(
        task_name="extension_document",
        source="background_task",
        message=f"Processing extension document: {content.metadata.VisitedWebPageTitle}",
        metadata={
            "url": content.metadata.VisitedWebPageURL,
            "title": content.metadata.VisitedWebPageTitle,
            "user_id": str(user_id),
        },
    )

    try:
        normalized_page_content = normalize_extension_page_content(content.pageContent)
        if not normalized_page_content:
            normalized_page_content = (content.pageContent or "").strip()

        # Format document metadata in a more maintainable way
        metadata_sections = [
            (
                "METADATA",
                [
                    f"SESSION_ID: {content.metadata.BrowsingSessionId}",
                    f"URL: {content.metadata.VisitedWebPageURL}",
                    f"TITLE: {content.metadata.VisitedWebPageTitle}",
                    f"REFERRER: {content.metadata.VisitedWebPageReffererURL}",
                    f"TIMESTAMP: {content.metadata.VisitedWebPageDateWithTimeInISOString}",
                    f"DURATION_MS: {content.metadata.VisitedWebPageVisitDurationInMilliseconds}",
                ],
            ),
            (
                "CONTENT",
                ["FORMAT: markdown", "TEXT_START", normalized_page_content, "TEXT_END"],
            ),
        ]

        # Build the document string more efficiently
        document_parts = []
        document_parts.append("<DOCUMENT>")

        for section_title, section_content in metadata_sections:
            document_parts.append(f"<{section_title}>")
            document_parts.extend(section_content)
            document_parts.append(f"</{section_title}>")

        document_parts.append("</DOCUMENT>")
        combined_document_string = "\n".join(document_parts)

        # Generate unique identifier hash for this extension document (using URL)
        unique_identifier_hash = generate_unique_identifier_hash(
            DocumentType.EXTENSION, content.metadata.VisitedWebPageURL, search_space_id
        )

        # Generate content hash
        content_hash = generate_content_hash(combined_document_string, search_space_id)

        # Check if document with this unique identifier already exists
        existing_document = await check_document_by_unique_identifier(
            session, unique_identifier_hash
        )

        if existing_document:
            # Document exists - check if content has changed
            if existing_document.content_hash == content_hash:
                await task_logger.log_task_success(
                    log_entry,
                    f"Extension document unchanged: {content.metadata.VisitedWebPageTitle}",
                    {
                        "duplicate_detected": True,
                        "existing_document_id": existing_document.id,
                    },
                )
                logging.info(
                    f"Document for URL {content.metadata.VisitedWebPageURL} unchanged. Skipping."
                )
                return existing_document
            else:
                # Content has changed - update the existing document
                logging.info(
                    f"Content changed for URL {content.metadata.VisitedWebPageURL}. Updating document."
                )

        # Get user's long context LLM (needed for both create and update)
        user_llm = await get_user_long_context_llm(session, user_id, search_space_id)
        if not user_llm:
            raise RuntimeError(
                f"No long context LLM configured for user {user_id} in search space {search_space_id}"
            )

        # Generate summary with metadata
        document_metadata = {
            "session_id": content.metadata.BrowsingSessionId,
            "url": content.metadata.VisitedWebPageURL,
            "title": content.metadata.VisitedWebPageTitle,
            "referrer": content.metadata.VisitedWebPageReffererURL,
            "timestamp": content.metadata.VisitedWebPageDateWithTimeInISOString,
            "duration_ms": content.metadata.VisitedWebPageVisitDurationInMilliseconds,
            "document_type": "Browser Extension Capture",
        }
        summary_content, summary_embedding = await generate_document_summary(
            combined_document_string, user_llm, document_metadata
        )

        # Process chunks
        chunks = await create_document_chunks(normalized_page_content)

        from app.utils.blocknote_converter import convert_markdown_to_blocknote

        # Convert markdown to BlockNote JSON
        blocknote_json = await convert_markdown_to_blocknote(combined_document_string)
        if not blocknote_json:
            logging.warning(
                f"Failed to convert extension document '{content.metadata.VisitedWebPageTitle}' "
                f"to BlockNote JSON, document will not be editable"
            )

        # Update or create document
        if existing_document:
            # Update existing document
            existing_document.title = content.metadata.VisitedWebPageTitle
            existing_document.content = summary_content
            existing_document.content_hash = content_hash
            existing_document.embedding = summary_embedding
            existing_document.document_metadata = content.metadata.model_dump()
            existing_document.chunks = chunks
            existing_document.blocknote_document = blocknote_json
            existing_document.updated_at = get_current_timestamp()

            await session.commit()
            await session.refresh(existing_document)
            document = existing_document
        else:
            # Create new document
            document = Document(
                search_space_id=search_space_id,
                title=content.metadata.VisitedWebPageTitle,
                document_type=DocumentType.EXTENSION,
                document_metadata=content.metadata.model_dump(),
                content=summary_content,
                embedding=summary_embedding,
                chunks=chunks,
                content_hash=content_hash,
                unique_identifier_hash=unique_identifier_hash,
                blocknote_document=blocknote_json,
                updated_at=get_current_timestamp(),
                created_by_id=user_id,
            )

            session.add(document)
            await session.commit()
            await session.refresh(document)

        # Log success
        await task_logger.log_task_success(
            log_entry,
            f"Successfully processed extension document: {content.metadata.VisitedWebPageTitle}",
            {
                "document_id": document.id,
                "content_hash": content_hash,
                "url": content.metadata.VisitedWebPageURL,
            },
        )

        return document

    except SQLAlchemyError as db_error:
        await session.rollback()
        await task_logger.log_task_failure(
            log_entry,
            f"Database error processing extension document: {content.metadata.VisitedWebPageTitle}",
            str(db_error),
            {"error_type": "SQLAlchemyError"},
        )
        raise db_error
    except Exception as e:
        await session.rollback()
        await task_logger.log_task_failure(
            log_entry,
            f"Failed to process extension document: {content.metadata.VisitedWebPageTitle}",
            str(e),
            {"error_type": type(e).__name__},
        )
        raise RuntimeError(f"Failed to process extension document: {e!s}") from e

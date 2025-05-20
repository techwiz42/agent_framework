from typing import Dict, Any, Optional, List
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from agents import (
    function_tool,
    RunContextWrapper,
    GuardrailFunctionOutput,
    input_guardrail
)
from agents.tool import FunctionTool

from app.models.domain.models import Thread
from app.services.rag.query_service import rag_query_service
from app.services.agents.base_agent import BaseAgent
from app.services.agents.common_context import CommonAgentContext
from app.core.config import settings

logger = logging.getLogger(__name__)

# Custom context type for document search
class DocumentSearchContext:
    def __init__(self, thread_id: str, db: AsyncSession):
        self.thread_id = thread_id
        self.db = db
        self.thread: Optional[Thread] = None
        self.owner_id: Optional[str] = None
        self.query_results: Dict[str, Any] = {}

# Define standalone functions for tools
@function_tool
async def search_documents(
    context: RunContextWrapper[Any],  # Accept any context type for flexibility
    query: str,
    max_results: int
) -> str:
    """
    Search for relevant documents based on the query.

    Args:
        query: The search query text
        max_results: Maximum number of results to return (recommended: 5)

    Returns:
        A formatted HTML string containing document search results with clickable links
    """
    try:
        # Check if we're using CommonAgentContext or DocumentSearchContext
        owner_id = None
        thread_id = None

        # Handle either context type gracefully
        if isinstance(context.context, DocumentSearchContext):
            # Original DocumentSearchContext
            owner_id = context.context.owner_id
            thread_id = context.context.thread_id
            query_results = context.context.query_results
        elif isinstance(context.context, CommonAgentContext):
            # CommonAgentContext (from agent_manager)
            owner_id = context.context.owner_id
            thread_id = context.context.thread_id
            # Create a query_results attribute if it doesn't exist
            if not hasattr(context.context, 'query_results'):
                context.context.query_results = {}
            query_results = context.context.query_results
        else:
            # Fallback for any other context type
            logger.warning(f"Unexpected context type: {type(context.context)}")
            if hasattr(context.context, 'owner_id'):
                owner_id = context.context.owner_id
            if hasattr(context.context, 'thread_id'):
                thread_id = context.context.thread_id
            # Add a query_results attribute dynamically if needed
            if not hasattr(context.context, 'query_results'):
                context.context.query_results = {}
            query_results = context.context.query_results

        # Check for owner_id directly from the stored context
        if not owner_id:
            logger.error("Document search error: Owner ID not available in context")
            return "Error: User information not available. Please try again."

        # Debug information
        logger.info(f"Document search - Thread ID: {thread_id}, Owner ID: {owner_id}")
        logger.info(f"Document search query: '{query}'")

        # Search for documents - documents belong to the conversation owner, not threads
        results = await rag_query_service.query_knowledge(
            owner_id=owner_id,
            query_text=query,
            k=max_results
        )

        # Store in context for later use
        context.context.query_results = results

        # Debugging: Log the full results
        logger.info(f"Document search results: found {len(results.get('documents', []))} documents")
        if len(results.get('documents', [])) > 0:
            for i, (doc, meta) in enumerate(zip(
                results.get('documents', [])[:2],  # Only log first 2 for brevity
                results.get('metadatas', [])[:2]
            )):
                logger.info(f"Doc {i} metadata: {meta}")
                logger.info(f"Doc {i} preview: {doc[:100]}...")

        # Format response
        document_count = len(results.get('documents', []))

        if document_count == 0:
            return "No relevant documents found in the knowledge base. Try a different query or upload documents to search through."

        response_parts = ["<h1>Found " + str(document_count) + " relevant documents:</h1>"]

        for i, (doc, metadata, distance) in enumerate(zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("distances", [])
        )):
            # Get filename from metadata
            filename = metadata.get('filename') or metadata.get('name') or 'Untitled Document'

            # Calculate similarity score
            similarity = round((1 - distance) * 100, 1)

            # Get document URL from metadata if available
            doc_url = metadata.get('web_url') or metadata.get('url')
            document_id = metadata.get('document_id') or metadata.get('id') or metadata.get('file_id') or f"doc_{i}"

            # Create document link based on available information
            if doc_url:
                # Use direct web_url if available (for OneDrive or Google Drive)
                # Using markdown format for consistency
                doc_link = f"[{filename}]({doc_url})"
            else:
                # Fallback to document viewer route
                doc_link = f"[{filename}](/documents/view/{document_id})"

            # Format document information with link - HTML format with enhanced clickability
            # Make sure URL is absolute and has target="_blank" and rel attributes for security
            full_url = doc_url or f"/documents/view/{document_id}"
            response_parts.append(f"<h2>📄 Document {i+1}: <a href=\"{full_url}\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"document-link\" onclick=\"window.open('{full_url}', '_blank'); return false;\">{filename}</a> <span class=\"relevance-score\">(Relevance: {similarity}%)</span></h2>")

            # Add content extracted from the RAG
            raw_text = doc[:400] + "..." if len(doc) > 400 else doc

            # Clean up the text as needed (remove excessive newlines, etc.)
            clean_text = raw_text.replace('\n\n\n', '\n\n').strip()

            # Create a summary - first few sentences from the document
            sentences = clean_text.split('.')[:3]
            summary = '. '.join(sentences) + '.' if sentences else clean_text
            summary = summary[:200] + "..." if len(summary) > 200 else summary

            # Add both summary and extracted text using HTML
            response_parts.append(f"<p><strong>Summary:</strong> {summary}</p>")
            response_parts.append(f"<div><strong>Extracted text:</strong><pre>{clean_text}</pre></div>")

            # Add download link using HTML with enhanced clickability
            if doc_url:
                response_parts.append(f"<a href=\"{doc_url}\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"document-action\" onclick=\"window.open('{doc_url}', '_blank'); return false;\">Download link</a>")

        # Add note about permissions at the bottom
        response_parts.append("<p class=\"document-note\"><em>Some users may require permission from document owners to view</em></p>")

        return "\n".join(response_parts)

    except Exception as e:
        logger.error(f"Error in document search: {e}")
        logger.error(traceback.format_exc())

        # Provide more specific error messages for debugging
        error_message = f"Error searching documents: {str(e)}"

        # Check for common issues
        if "thread" in str(e).lower():
            error_message = "Error accessing thread information. Please ensure the thread exists and you have permission to access it."
        elif "collection" in str(e).lower():
            error_message = "Error accessing document collection. The RAG system may not be properly initialized."
        elif "permission" in str(e).lower() or "access" in str(e).lower():
            error_message = "Permission error when accessing documents. Please ensure you have the correct permissions."

        return error_message

@function_tool
async def format_document_analysis(
    context: RunContextWrapper[Any],  # Accept any context type for flexibility
    summary: str,
    key_points: List[str],
    relevant_quotes: List[str]
) -> str:
    """
    Format an analysis of document search results with summary and key points.

    Args:
        summary: A brief summary of the document findings
        key_points: List of key points extracted from the documents
        relevant_quotes: Optional list of relevant quotes from the documents

    Returns:
        Formatted document analysis
    """
    parts = ["## Document Analysis", f"\n{summary}\n"]

    if key_points:
        parts.append("### Key Points")
        for point in key_points:
            parts.append(f"- {point}")

    if relevant_quotes and len(relevant_quotes) > 0:
        parts.append("\n### Relevant Quotes")
        for quote in relevant_quotes:
            parts.append(f"> {quote}")

    # Get query_results safely based on context type
    query_results = None
    if isinstance(context.context, DocumentSearchContext):
        query_results = context.context.query_results
    elif hasattr(context.context, 'query_results'):
        query_results = context.context.query_results

    # Add source attribution if available
    if query_results and query_results.get("metadatas"):
        parts.append("\n### Sources")
        for i, metadata in enumerate(query_results.get("metadatas", [])[:5]):
            filename = metadata.get('filename') or metadata.get('name') or metadata.get('source') or 'Unknown'

            # Get document URL from metadata if available
            doc_url = metadata.get('web_url') or metadata.get('url')
            document_id = metadata.get('document_id') or metadata.get('id') or metadata.get('file_id') or f"doc_{i}"

            # Create document link based on available information
            if doc_url:
                # Use direct web_url if available (for OneDrive or Google Drive)
                # Using markdown format for consistency
                doc_link = f"[{filename}]({doc_url})"
            else:
                # Fallback to document viewer route
                doc_link = f"[{filename}](/documents/view/{document_id})"

            parts.append(f"- {doc_link}")

    return "\n".join(parts)

@input_guardrail
def validate_document_search_context(
    context: RunContextWrapper[Any],  # Accept any context type
    agent: Any,
    input: str
) -> GuardrailFunctionOutput:
    """Validate that we have a thread context for document search."""
    thread_id = None
    owner_id = None

    # Safely get thread_id and owner_id regardless of context type
    if hasattr(context.context, 'thread_id'):
        thread_id = context.context.thread_id

    if hasattr(context.context, 'owner_id'):
        owner_id = context.context.owner_id

    if not thread_id:
        return GuardrailFunctionOutput(
            output_info="Missing thread_id for document search",
            tripwire_triggered=True
        )

    if not owner_id:
        return GuardrailFunctionOutput(
            output_info="Missing owner_id for document search",
            tripwire_triggered=True
        )

    return GuardrailFunctionOutput(
        output_info="Context validation passed",
        tripwire_triggered=False
    )

class DocumentSearchAgent(BaseAgent[Any]):  # Use Any to accept all context types
    """
    An agent specialized in searching and analyzing documents.
    Inherits from BaseAgent and adds document-specific functionality.
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize the DocumentSearchAgent with specific instructions and tools."""
        super().__init__(
            name="DOCUMENTSEARCH",
            instructions="""You are a document search specialist who helps find and understand relevant documents and context.

Your PRIMARY RESPONSIBILITIES include:
- Search document collections effectively
- Find relevant context for queries
- Provide document summaries
- Extract key information
- Link to source documents
- Highlight relevant passages
- Note document metadata
- Verify document relevance

When collaborating with other agents:
- Provide document context to support their work
- Find supporting documentation for claims
- Verify factual claims against documents
- Note document limitations
- Highlight cross-document connections
- Support evidence-based discussion
- Add historical context from documents

Always be neutral and focus on the factual content of documents, not your own opinions.
""",
            functions=[
                search_documents,
                format_document_analysis
            ],
            model=model,
            output_type=str
        )

        # Add guardrails
        self.input_guardrails.append(validate_document_search_context)
    
    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """Initialize the agent context by loading the thread."""
        # Skip if needed attributes aren't available
        thread_id = getattr(context.context, 'thread_id', None)
        db = getattr(context.context, 'db', None)

        if not thread_id or not db:
            logger.warning("Missing thread_id or db in context, skipping thread loading")
            return

        try:
            # Check if we already have the owner_id
            if hasattr(context.context, 'owner_id') and context.context.owner_id:
                logger.info(f"Already have owner_id: {context.context.owner_id}")
                return

            # Load the thread to get owner_id
            result = await db.execute(
                select(Thread).where(Thread.id == thread_id)
            )
            thread = await result.scalar_one_or_none()

            # Set thread if we can
            if hasattr(context.context, 'thread'):
                context.context.thread = thread

            # Set the owner_id from the thread
            if thread:
                # Set owner_id dynamically if the attribute doesn't exist
                context.context.owner_id = str(thread.owner_id)
                logger.info(f"Set owner_id to {context.context.owner_id} for document search")
            else:
                logger.error(f"Thread not found with ID: {thread_id}")
        except Exception as e:
            logger.error(f"Error loading thread: {e}")
            logger.error(traceback.format_exc())

# Create the singleton instance
document_search_agent = DocumentSearchAgent()
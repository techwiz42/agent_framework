from typing import Dict, Any, List, Optional
import logging
import traceback
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SummaryAgent(BaseAgent):
    """
    SummaryAgent is a specialized agent that creates concise, informative summaries of document content.
    
    This agent specializes in creating summaries optimized for RAG systems and document retrieval.
    """

    def __init__(
        self,
        name: str = "Summary Agent",
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a SummaryAgent with specialized summary instructions.
        
        Args:
            name: The name of the agent. Defaults to "Summary Agent".
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            model: The model to use. Defaults to settings.DEFAULT_AGENT_MODEL.
            **kwargs: Additional arguments to pass to the BaseAgent constructor.
        """
        # Define the summary agent instructions
        summary_instructions = """You are an agent that specializes in creating concise but informative summaries of document content.
            
Your summaries should:
1. Compress content at roughly a 15:1 ratio (longer summaries for longer documents)
2. Capture main ideas, key points, and important details
3. Include significant topics, terms, and concepts to aid in document discovery
4. Be written in a clear, objective style
5. Preserve the most searchable and important content"""

        # Define the tools using the function_tool decorator from Agent SDK
        tools = [
            function_tool(self.create_rag_summary),
            function_tool(self.summarize_with_metadata),
            function_tool(self.create_bullet_summary),
            function_tool(self.create_executive_summary),
            function_tool(self.create_topic_summary)
        ]
        
        # Use the provided model or fall back to default
        agent_model = model if model is not None else settings.DEFAULT_AGENT_MODEL
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            instructions=summary_instructions,
            functions=tools,
            model=agent_model,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the SummaryAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for SummaryAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Creates concise, informative summaries of document content"

    def create_rag_summary(
        self,
        context: RunContextWrapper,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a RAG-optimized summary of document content.
        
        Args:
            context: The run context wrapper.
            content: The document content to summarize.
            metadata: Optional dictionary containing document metadata like filename, mime type, etc.
                
        Returns:
            A concise summary optimized for RAG systems, focusing on key topics and concepts.
        """
        if not content or len(content.strip()) == 0:
            return "Empty document"
        
        try:
            # Limit content to 50,000 characters while being mindful of word boundaries
            content_limited = content[:50000]
            if len(content) > 50000:
                # Try to break at last period or newline
                last_period = content_limited.rfind('.')
                last_newline = content_limited.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > 0:
                    content_limited = content_limited[:break_point + 1]
                logger.info(f"Content truncated from {len(content)} to {len(content_limited)} characters")
            
            # Create context about the document
            context = ""
            if metadata:
                context = f"""This is a {metadata.get('mime_type', 'document')} file named "{metadata.get('filename', 'unknown')}"."""
            
            # Mock summary generation (in a real implementation, this would call an LLM)
            content_words = len(content_limited.split())
            target_words = max(50, content_words // 15)  # Apply 15:1 compression ratio with minimum of 50 words
            
            # In a non-mock implementation, we would use the model to generate the summary
            # For testing purposes, we'll create a simulated summary
            first_line = content_limited.split('\n', 1)[0] if '\n' in content_limited else content_limited[:100]
            summary = f"Summary of {content_words} words in approximately {target_words} words. "
            summary += f"Document begins with: '{first_line}...'. "
            
            if metadata:
                summary += f"Document type: {metadata.get('mime_type', 'unknown')}. "
                summary += f"Filename: {metadata.get('filename', 'unknown')}."
            
            return summary
        
        except Exception as e:
            logger.error(f"Error creating RAG summary: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error generating summary: {str(e)}"
    
    def summarize_with_metadata(
        self,
        context: RunContextWrapper,
        content: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        date: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a summary that incorporates document metadata.
        
        Args:
            context: The run context wrapper.
            content: The document content to summarize.
            title: Optional document title.
            author: Optional document author.
            date: Optional document creation/publication date.
            document_type: Optional document type (article, report, etc.).
            
        Returns:
            A dictionary containing the summary and enhanced metadata.
        """
        try:
            # Limit content similar to rag_summary
            content_limited = content[:50000]
            if len(content) > 50000:
                last_period = content_limited.rfind('.')
                last_newline = content_limited.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > 0:
                    content_limited = content_limited[:break_point + 1]
            
            # Create basic summary
            basic_summary = "This document "
            
            if title:
                basic_summary += f"titled '{title}' "
            
            if author:
                basic_summary += f"by {author} "
            
            if date:
                basic_summary += f"from {date} "
            
            if document_type:
                basic_summary += f"is a {document_type} that "
            
            # Extract first and last paragraphs for context
            paragraphs = [p for p in content_limited.split('\n\n') if p.strip()]
            first_paragraph = paragraphs[0] if paragraphs else ""
            last_paragraph = paragraphs[-1] if len(paragraphs) > 1 else ""
            
            # Create a mock summary
            content_words = len(content_limited.split())
            basic_summary += f"contains approximately {content_words} words. "
            basic_summary += f"It begins with: '{first_paragraph[:100]}...' "
            if last_paragraph != first_paragraph:
                basic_summary += f"and concludes with: '{last_paragraph[:100]}...'"
            
            # Generate metadata insights
            metadata_insights = {}
            if title:
                metadata_insights["title_analysis"] = f"The title '{title}' suggests this document is about..."
            if document_type:
                metadata_insights["type_analysis"] = f"As a {document_type}, this document follows typical conventions of..."
            
            # Return combined result
            return {
                "summary": basic_summary,
                "word_count": content_words,
                "metadata_insights": metadata_insights,
                "estimated_reading_time": f"{content_words // 250} minutes"  # Assuming 250 words per minute
            }
            
        except Exception as e:
            logger.error(f"Error creating summary with metadata: {str(e)}")
            logger.error(traceback.format_exc())
            return {"summary": f"Error generating summary: {str(e)}"}
    
    def create_bullet_summary(
        self,
        context: RunContextWrapper,
        content: str,
        max_bullets: int,
        focus_areas: Optional[List[str]] = None
    ) -> List[str]:
        """
        Create a bulleted summary of key points from the document.
        
        Args:
            context: The run context wrapper.
            content: The document content to summarize.
            max_bullets: Maximum number of bullet points to generate.
            focus_areas: Optional list of specific areas to focus on.
            
        Returns:
            A list of bullet points summarizing key information.
        """
        try:
            # Default value handling moved to function body
            max_bullets = max_bullets if max_bullets is not None else 10
            
            # Limit content size
            content_limited = content[:50000]
            if len(content) > 50000:
                content_limited = content_limited[:content_limited.rfind('.') + 1]
            
            # Split into paragraphs
            paragraphs = [p for p in content_limited.split('\n\n') if p.strip()]
            
            # Generate bullets (in real implementation, would use ML to extract key points)
            bullets = []
            
            # Add an initial bullet about document length
            content_words = len(content_limited.split())
            bullets.append(f"Document contains approximately {content_words} words")
            
            # Extract sentences that might contain key information
            remaining_bullets = min(max_bullets - 1, len(paragraphs))
            
            for i in range(min(remaining_bullets, len(paragraphs))):
                # In a real implementation, use NLP to extract important sentences
                # For mock, take the first sentence of each paragraph
                paragraph = paragraphs[i]
                sentences = paragraph.split('. ')
                if sentences:
                    first_sentence = sentences[0].strip()
                    if len(first_sentence) > 10:  # Avoid very short sentences
                        bullets.append(first_sentence)
            
            # If focus areas specified, add points for each
            if focus_areas:
                for area in focus_areas[:max(0, max_bullets - len(bullets))]:
                    bullets.append(f"Regarding {area}: Content includes relevant information...")
            
            # Ensure we don't exceed max_bullets
            return bullets[:max_bullets]
            
        except Exception as e:
            logger.error(f"Error creating bullet summary: {str(e)}")
            logger.error(traceback.format_exc())
            return [f"Error generating summary: {str(e)}"]
    
    def create_executive_summary(
        self,
        context: RunContextWrapper,
        content: str,
        sections: Optional[List[str]],
        max_length: int
    ) -> Dict[str, str]:
        """
        Create an executive summary with optional section-specific summaries.
        
        Args:
            context: The run context wrapper.
            content: The document content to summarize.
            sections: Optional list of document sections to summarize separately.
            max_length: Maximum character length for the overall summary.
            
        Returns:
            A dictionary with an overall summary and section summaries if requested.
        """
        try:
            # Default value handling moved to function body
            max_length = max_length if max_length is not None else 500
            
            # Limit content
            content_limited = content[:50000]
            
            # Create mock executive summary
            content_words = len(content_limited.split())
            exec_summary = f"This document of approximately {content_words} words "
            
            # Add document beginning
            first_lines = content_limited.split('\n', 5)[:5]
            first_paragraph = ' '.join(first_lines).strip()
            exec_summary += f"begins with: '{first_paragraph[:100]}...'. "
            
            # Add key points placeholder
            exec_summary += "Key points include: point one, point two, and point three. "
            
            # Add conclusion placeholder
            exec_summary += "The document concludes with recommendations for future action."
            
            # Truncate to max_length
            if len(exec_summary) > max_length:
                exec_summary = exec_summary[:max_length-3] + "..."
            
            # Build result
            result = {
                "overall_summary": exec_summary,
                "executive_highlights": [
                    "Key highlight one",
                    "Key highlight two",
                    "Key highlight three"
                ]
            }
            
            # Add section summaries if requested
            if sections:
                section_summaries = {}
                for section in sections:
                    section_summaries[section] = f"Summary of {section} section..."
                result["section_summaries"] = section_summaries
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {str(e)}")
            logger.error(traceback.format_exc())
            return {"overall_summary": f"Error generating summary: {str(e)}"}
    
    def create_topic_summary(
        self,
        context: RunContextWrapper,
        content: str,
        extract_topics: bool,
        topic_threshold: int
    ) -> Dict[str, Any]:
        """
        Create a summary that identifies and highlights key topics in the document.
        
        Args:
            context: The run context wrapper.
            content: The document content to summarize.
            extract_topics: Whether to extract topics from the document.
            topic_threshold: Minimum number of mentions for a topic to be included.
            
        Returns:
            A dictionary with summary and identified topics with their frequencies.
        """
        try:
            # Default value handling moved to function body
            extract_topics = extract_topics if extract_topics is not None else True
            topic_threshold = topic_threshold if topic_threshold is not None else 3
            
            # Limit content
            content_limited = content[:50000]
            content_words = len(content_limited.split())
            
            # Create basic summary
            basic_summary = f"This document contains approximately {content_words} words. "
            
            # Extract first paragraph
            paragraphs = [p for p in content_limited.split('\n\n') if p.strip()]
            if paragraphs:
                basic_summary += f"It begins with: '{paragraphs[0][:100]}...'. "
            
            # Mock topic extraction
            topic_summary = {}
            if extract_topics:
                # In real implementation, use NLP for topic modeling/extraction
                # For mocking purposes, count common words excluding stopwords
                words = content_limited.lower().split()
                word_count = {}
                for word in words:
                    if len(word) > 4:  # Simple filter for potentially meaningful words
                        word = word.strip('.,;:?!()"\'')
                        if word:
                            word_count[word] = word_count.get(word, 0) + 1
                
                # Filter by threshold and sort by frequency
                potential_topics = {
                    word: count for word, count in word_count.items() 
                    if count >= topic_threshold
                }
                top_topics = dict(sorted(potential_topics.items(), key=lambda x: x[1], reverse=True)[:10])
                
                topic_summary["identified_topics"] = top_topics
                topic_summary["topic_based_summary"] = "This document primarily discusses " + ", ".join(list(top_topics.keys())[:5])
            
            # Combine into final output
            result = {
                "summary": basic_summary,
                "word_count": content_words,
                "topic_analysis": topic_summary
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating topic summary: {str(e)}")
            logger.error(traceback.format_exc())
            return {"summary": f"Error generating summary: {str(e)}"}

# Create a singleton instance
summary_agent = SummaryAgent()

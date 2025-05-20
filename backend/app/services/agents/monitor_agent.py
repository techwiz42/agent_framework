from typing import Dict, Any, Optional, List, Union, Callable
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

from agents import (
    function_tool,
    RunContextWrapper,
    GuardrailFunctionOutput,
    input_guardrail,
    ModelSettings
)
from app.services.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Custom context type for monitor agent
class MonitorContext:
    def __init__(self, thread_id: str, db: AsyncSession):
        self.thread_id = thread_id
        self.db = db
        self.conversation_history: List[Dict[str, Any]] = []
        self.addressed_directly: bool = False


@function_tool
async def analyze_conversation(
    context: RunContextWrapper[MonitorContext],
    analysis_type: str,
    specific_focus: Optional[str] = None
) -> str:
    """
    Analyze the conversation based on the specified analysis type.
    
    Args:
        analysis_type: Type of analysis to perform (summary, key_points, disagreements, etc.)
        specific_focus: Optional specific aspect to focus on
    
    Returns:
        A detailed analysis based on the requested type
    """
    # This is mostly a placeholder as the LLM will have access to the conversation history
    # and will perform the analysis based on the instructions and context
    
    history = context.context.conversation_history
    
    analysis_intro = f"# {analysis_type.title()} Analysis"
    if specific_focus:
        analysis_intro += f": {specific_focus}"
    
    # Just return the intro - the actual analysis will be performed by the LLM
    # based on the full conversation history
    return analysis_intro


@input_guardrail
def validate_monitor_request(
    context: RunContextWrapper[MonitorContext],
    agent: Any,
    input: str
) -> GuardrailFunctionOutput:
    """
    Validate that the monitor agent is being addressed directly with @MONITOR.
    If not addressed directly, the agent should not respond.
    """
    # Check if the input contains @MONITOR
    is_addressed = bool(re.search(r'@MONITOR', input, re.IGNORECASE))
    
    # Store the result in context for later use
    # Ensure context.context is a MonitorContext object, not a dict
    if isinstance(context.context, dict):
        # Create MonitorContext if context was passed as dict
        thread_id = context.context.get('thread_id', '')
        db = context.context.get('db', None)
        monitor_ctx = MonitorContext(thread_id=thread_id, db=db)
        monitor_ctx.addressed_directly = is_addressed
        context.context = monitor_ctx
    else:
        # Normal case when context is already a MonitorContext
        context.context.addressed_directly = is_addressed
    
    if not is_addressed:
        return GuardrailFunctionOutput(
            output_info="Monitor agent not directly addressed with @MONITOR",
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info="Monitor agent directly addressed",
        tripwire_triggered=False
    )


class MonitorAgent(BaseAgent[MonitorContext]):
    """
    Agent that silently monitors conversations and provides analysis when requested.
    Only responds when explicitly addressed with @MONITOR.
    """
    
    def __init__(self, model: str = settings.DEFAULT_AGENT_MODEL):
        """Initialize the MonitorAgent with specific instructions and tools."""
        instructions = """You are a monitoring agent that silently observes conversations. You ONLY respond when explicitly addressed with @MONITOR. Your role is to provide analysis and insights about the conversation when requested.

KEY BEHAVIORS:
1. Stay completely silent unless directly addressed with @MONITOR
2. When addressed, analyze the conversation based on the specific request
3. Consider the full context of the discussion
4. Draw insights from the complete conversation history

ANALYSIS CAPABILITIES:
When asked, you can:
- Summarize the discussion and its key points
- Identify main arguments and counterarguments presented
- Track how positions and ideas have evolved
- Point out areas of agreement and disagreement
- Identify unresolved questions or issues
- Highlight patterns or recurring themes
- Note gaps in the discussion

GUIDELINES:
- Respond ONLY to direct @MONITOR mentions
- Focus on observation and analysis rather than participation
- Base all analysis strictly on the conversation content
- Support observations with specific references from the discussion
- Maintain complete neutrality
- Present analysis clearly and objectively
- Acknowledge limitations in available information

WHAT NOT TO DO:
- Do not participate unless directly addressed with @MONITOR
- Do not provide advice unless specifically requested
- Do not take sides in disagreements
- Do not make assumptions beyond available information
- Do not reveal private conversation details elsewhere
- Do not pretend to have information from outside the conversation

EXAMPLE RESPONSES TO:
"@MONITOR summarize our discussion so far"
"@MONITOR what are the key points of disagreement?"
"@MONITOR how have the positions evolved?"
"@MONITOR what issues remain unresolved?"
"@MONITOR analyze the main arguments presented"
"""
        
        super().__init__(
            name="MONITOR",
            model=model,
            instructions=instructions,
            functions=[
                analyze_conversation
            ],
            tool_choice=None,
            parallel_tool_calls=True,
            output_type=str
        )
        
        # Add the input guardrail to enforce direct addressing
        self.input_guardrails.append(validate_monitor_request)
    
    @property
    def description(self) -> str:
        """Get the description of the MonitorAgent."""
        return "Silently monitors conversations and provides analysis, summaries, and insights when directly addressed with @MONITOR"
    
    async def init_context(self, context: RunContextWrapper[MonitorContext]) -> None:
        """
        Initialize the agent context.
        
        Args:
            context: The context wrapper containing MonitorContext
        """
        # Any additional context initialization can be done here
        # For example, if we needed to load conversation history from the database
        pass
    
    async def process_message(
        self,
        db: AsyncSession,
        thread_id: str,
        query: str
    ) -> Optional[str]:
        """
        Process a direct message to the monitor agent.
        This is maintained for backward compatibility with existing code.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            query: User query message
            
        Returns:
            Response from the monitor agent if addressed directly, None otherwise
        """
        from agents import Runner, RunConfig
        
        try:
            # Create context
            context = MonitorContext(thread_id=thread_id, db=db)
            
            # Check if the monitor is being addressed directly
            if not re.search(r'@MONITOR', query, re.IGNORECASE):
                # Not addressed directly, remain silent
                return None
            
            # Run the agent
            result = await Runner.run(
                starting_agent=self,
                input=query,
                context=context,
                run_config=RunConfig(
                    workflow_name="Monitor Analysis"
                )
            )
            
            return result.final_output
            
        except Exception as e:
            logger.error(f"Error processing monitor query: {e}")
            # If there's an error, we'll still return None to maintain the behavior
            # of being silent unless properly addressed
            return None


# Create singleton instance
monitor_agent = MonitorAgent()

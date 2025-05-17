from typing import Dict, List, Optional, Any, Union
import logging
import json
import inspect
import traceback

from app.core.config import settings
from app.services.agents.base_agent import BaseAgent, AgentHooks, RunContextWrapper
from app.services.agents.common_context import CommonAgentContext

logger = logging.getLogger(__name__)

# Placeholder for function_tool decorator
def function_tool(func):
    return func

# Placeholder for input_guardrail decorator
def input_guardrail(func):
    return func

# Placeholder for output_guardrail decorator
def output_guardrail(func):
    return func

# Placeholder for handoff decorator
def handoff(agent, tool_name_override=None, tool_description_override=None):
    return None

class GuardrailFunctionOutput:
    def __init__(self, output_info: str, tripwire_triggered: bool = False):
        self.output_info = output_info
        self.tripwire_triggered = tripwire_triggered

# Utility function to get OpenAI client
async def get_openai_client():
    """Get an OpenAI client with the app's API key."""
    # This is a placeholder - in a real implementation, import and return the actual client
    return None

@function_tool
async def select_agent(
    query: Optional[str] = None,
    available_agents: Optional[str] = None
) -> str:
    """
    Select the most appropriate agent(s) to handle the user's query.
    
    Args:
        query: The user's query
        available_agents: Comma-separated list of available agent types
        
    Returns:
        JSON string with selected agent(s)
    """
    # Get context from current execution
    context = None
    try:
        # This is a hack to get access to the current context
        # The function tool decorator will pass the context as the first argument
        # but we're not declaring it in the function signature to avoid schema issues
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        if len(args) > 0 and args[0] == 'context':
            context = values['context']
    except Exception as e:
        logger.warning(f"Could not access context: {e}")
    
    # Parse available agents
    agent_options = []
    if available_agents:
        agent_options = [a.strip() for a in available_agents.split(',')]
    
    # Get available agents from context if available
    try:
        if context is not None and hasattr(context, 'context'):
            ctx = context.context  # This is the CommonAgentContext
            if hasattr(ctx, 'available_agents') and ctx.available_agents:
                agent_options = list(ctx.available_agents.keys())
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not access context.available_agents: {e}")
    
    # If no agents available, return MODERATOR as fallback
    if not agent_options:
        logger.warning("No agents available for selection")
        
        # Store selected agent in context
        try:
            if context is not None and hasattr(context, 'context'):
                context.context.selected_agent = "MODERATOR"
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not set selected_agent on context: {e}")
        
        result = {
            "primary_agent": "MODERATOR",
            "supporting_agents": []
        }
        return json.dumps(result)
    
    # Simplified approach for now: Use keyword matching for basic agent selection
    if query:
        query_lower = query.lower()
        
        # Define keywords for each agent type
        agent_keywords = {
            "BUSINESS": ["business", "strategy", "market", "profit", "revenue", "company", "management"],
            "BUSINESSINTELLIGENCE": ["intelligence", "data", "metrics", "kpi", "analytics", "insights", "dashboard"],
            "DATAANALYSIS": ["data", "analysis", "analyze", "dataset", "statistics", "graph", "chart", "trend"],
            "WEBSEARCH": ["search", "internet", "web", "find", "google", "online", "lookup"],
            "DOCUMENTSEARCH": ["document", "file", "pdf", "doc", "paper", "text", "upload"],
            "MONITOR": ["monitor", "system", "status", "health", "track", "log", "performance"]
        }
        
        # Score each agent based on keyword matches
        agent_scores = {agent: 0 for agent in agent_options}
        for agent in agent_options:
            if agent in agent_keywords:
                for keyword in agent_keywords[agent]:
                    if keyword in query_lower:
                        agent_scores[agent] += 1
        
        # Find the agent with the highest score
        max_score = 0
        primary_agent = "MODERATOR"  # Default
        for agent, score in agent_scores.items():
            if score > max_score:
                max_score = score
                primary_agent = agent
        
        # If no clear winner, use MODERATOR as default
        if max_score == 0:
            primary_agent = "MODERATOR"
            
        # Store in context
        try:
            if context is not None and hasattr(context, 'context'):
                context.context.selected_agent = primary_agent
                context.context.collaborators = []
                if hasattr(context.context, 'is_agent_selection'):
                    context.context.is_agent_selection = True
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not update context with direct match: {e}")
            
        result = {
            "primary_agent": primary_agent,
            "supporting_agents": []
        }
        return json.dumps(result)
    
    # Fallback to MODERATOR if no query or no match
    result = {
        "primary_agent": "MODERATOR",
        "supporting_agents": []
    }
    
    # Store in context
    try:
        if context is not None and hasattr(context, 'context'):
            context.context.selected_agent = "MODERATOR"
            context.context.collaborators = []
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not set selected_agent on context: {e}")
    
    return json.dumps(result)

@function_tool
async def check_collaboration_need(
    query: Optional[str] = None,
    primary_agent: Optional[str] = None,
    available_agents: Optional[str] = None
) -> str:
    """
    Determine whether multiple agents should collaborate on this query.
    
    Args:
        query: The user's query
        primary_agent: The primary selected agent
        available_agents: Comma-separated list of available agent types
        
    Returns:
        JSON string containing collaboration details
    """
    # This is a simplified implementation that always returns no collaboration needed
    result = {
        "collaboration_needed": False,
        "collaborators": [],
        "reasoning": "Simplified implementation defaults to no collaboration"
    }
    
    # Get context from current execution
    context = None
    try:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        if len(args) > 0 and args[0] == 'context':
            context = values['context']
    except Exception as e:
        logger.warning(f"Could not access context: {e}")
    
    # Store in context
    try:
        if context is not None and hasattr(context, 'context'):
            context.context.collaborators = []
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not set collaborators on context: {e}")
    
    return json.dumps(result)

@input_guardrail
def validate_moderator_input(
    context: RunContextWrapper[CommonAgentContext],
    agent: Any,
    input: Union[str, List, Dict, Any]
) -> GuardrailFunctionOutput:
    """Basic validation for moderator input."""
    try:
        # Handle different input types
        if isinstance(input, str):
            if not input or len(input.strip()) < 1:  # Lowered from 5 to 1 to allow short inputs
                return GuardrailFunctionOutput(
                    output_info="Input too short or empty",
                    tripwire_triggered=True
                )
        elif isinstance(input, list):
            # Handle list input - check if empty
            if not input or len(input) < 1:
                return GuardrailFunctionOutput(
                    output_info="Input list is empty",
                    tripwire_triggered=True
                )
            # Convert list to string if needed for further processing
            input = str(input)
        elif isinstance(input, dict):
            # Handle dictionary input - check if empty
            if not input:
                return GuardrailFunctionOutput(
                    output_info="Input dictionary is empty",
                    tripwire_triggered=True
                )
        elif input is None:
            return GuardrailFunctionOutput(
                output_info="Input is None",
                tripwire_triggered=True
            )
        
        return GuardrailFunctionOutput(
            output_info="Input validation passed",
            tripwire_triggered=False
        )
    except Exception as e:
        logger.error(f"Error in input validation: {e}")
        # Default to accepting the input on error
        return GuardrailFunctionOutput(
            output_info=f"Validation error: {e}",
            tripwire_triggered=False
        )

# Simple agent hooks implementation
class ModeratorAgentHooks(AgentHooks):
    """Custom hooks for the moderator agent."""

    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the ModeratorAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for ModeratorAgent")

    
    async def on_handoff(
        self, 
        context: RunContextWrapper[CommonAgentContext],
        agent: Any,
        source: Any
    ) -> None:
        """Called when control is handed back to the moderator."""
        logger.info(f"Control returned to moderator from {source.name}")

class ModeratorAgent(BaseAgent):
    """
    A specialized agent that coordinates conversations and routes queries to specialist agents.
    """
    
    def __init__(self, name="MODERATOR"):
        super().__init__(
            name=name,
            instructions="""You are a moderator agent responsible for coordinating conversations and routing queries to specialist agents.

YOUR PRIMARY ROLE:
- Analyze queries to select the most appropriate specialist agent(s)
- Determine when multiple agents should collaborate
- Route queries to the correct specialist(s)
- Do NOT answer queries directly - your job is ONLY to route

AGENT SELECTION PROCESS:
1. Analyze the query to understand its primary topic and required expertise
2. Review the available agents and their descriptions
3. Select the primary agent who is best suited to handle this query
4. When appropriate, select 1-2 additional agents who can provide valuable additional perspectives
5. Always select agents EXACTLY as they appear in the available agents list

COLLABORATION CRITERIA:
Consider recommending collaboration when:
- The query spans multiple expertise domains
- Multiple perspectives would improve answer quality
- Comparing/contrasting different viewpoints is requested
- The query is complex and requires diverse expertise

RESPONSE FORMAT:
When selecting agents, respond with a JSON object:
{
  "primary_agent": "AGENT1",
  "supporting_agents": ["AGENT2", "AGENT3"]
}

IMPORTANT: You should ONLY route queries, not answer them directly! 
USE THE TOOLS PROVIDED to select agents and determine collaboration needs.
ALWAYS SELECT AGENTS EXACTLY AS THEY APPEAR IN THE AVAILABLE AGENTS LIST.""",
            functions=[select_agent, check_collaboration_need],
            tool_choice="required",  # Force tool usage
            parallel_tool_calls=True,
            hooks=ModeratorAgentHooks()
        )
        
        # Add the input guardrail - with reduced minimum length check (1 instead of 5)
        self.input_guardrails = [validate_moderator_input]
        
        # Make sure all collections are initialized
        self.handoffs = []
        
        # Add description property
        self.description = "Routes queries to specialist agent experts"
        
        # Initialize the registered agents dictionary
        self._registered_agents = {}

    def register_agent(self, agent: Any) -> None:
        """Register an agent with the moderator for handoffs."""
        if agent.name == self.name:
            logger.warning(f"Skipping self-registration for {self.name}")
            return

        # Extract agent type from name
        agent_type = ""
        if hasattr(agent, 'name'):
            # Convert name to uppercase for storage, but lowercase and sanitize for tool name
            agent_type = agent.name.replace('Agent', '').upper()

        # Store the agent description if available
        if hasattr(agent, 'description') and agent.description:
            self._registered_agents[agent_type] = agent.description
        else:
            self._registered_agents[agent_type] = f"{agent_type} agent"

        logger.info(f"Registered agent {agent_type} with moderator")

    def update_instructions(self, agent_descriptions: Dict[str, str]) -> None:
        """Update moderator instructions with available agents."""
        # Store the agent descriptions
        self._registered_agents.update(agent_descriptions)
    
        # Build agent descriptions
        agent_descriptions_text = []
        for agent_name, description in self._registered_agents.items():
            if agent_name != self.name:  # Skip self
                agent_descriptions_text.append(f"- {agent_name}: {description}")
    
        # If no agents, provide a placeholder
        if not agent_descriptions_text:
            agent_descriptions_text = ["No specialist agents available"]
    
        # Strip existing agent descriptions section if present
        base_instructions = self.instructions
        if "AVAILABLE SPECIALIST AGENTS:" in base_instructions:
            base_instructions = base_instructions.split("AVAILABLE SPECIALIST AGENTS:")[0].strip()
    
        # Update the instructions with agent descriptions
        new_instructions = base_instructions + "\n\nAVAILABLE SPECIALIST AGENTS:\n" + "\n".join(agent_descriptions_text)
        self.instructions = new_instructions
    
        logger.info(f"Updated MODERATOR instructions with {len(agent_descriptions_text)} agent descriptions")

# Create the moderator agent instance
moderator_agent = ModeratorAgent()

# Expose the agent for importing by other modules
__all__ = ["moderator_agent", "ModeratorAgent"]
from typing import Dict, Any, Optional, List
import logging
import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent

from agents import (
    Agent,
    RunContextWrapper, 
    function_tool,
    ModelSettings
)

logger = logging.getLogger(__name__)

# Simple context class for the mediator
class MediatorContext:
    def __init__(self):
        self.previous_mediations: List[Dict[str, Any]] = []


async def _suggest_collaboration_agents(
    context: RunContextWrapper[MediatorContext], 
    query: str,
    available_agents: List[str]
) -> str:
    """
    Suggest agents that could help resolve the query.
    
    Args:
        query: The input query to find collaborators for
        available_agents: List of available agents to choose from
        
    Returns:
        A list of suggested collaborating agents
    """
    suggestion_prompt = f"""As a mediator, suggest which agents would be most helpful for this query.

Query: {query}
Available Agents: {', '.join(available_agents)}

Consider:
1. Required domains of expertise
2. Potential stakeholder interests
3. Regulatory/compliance needs
4. Technical requirements
5. Risk management aspects

List only essential participants, one per line and only from the available agents. Exclude the Mediator itself."""

    # Attempt to get client, with fallback to direct creation
    try:
        # First, try to get client from the agent
        client = getattr(context.context._agent, 'client', None)
        
        # If no client, try to create one (this might fail without API key)
        if client is None:
            try:
                client = AsyncOpenAI()
            except Exception:
                # If client creation fails, return an empty list
                return json.dumps([])
        
        response = await client.chat.completions.create(
            model=settings.DEFAULT_AGENT_MODEL,
            messages=[{"role": "user", "content": suggestion_prompt}],
            temperature=0.1
        )
    except Exception as e:
        # Log the error, return an empty list
        logger.error(f"Error in collaboration agent suggestion: {e}")
        return json.dumps([])

    # Parse and filter suggestions
    suggested = [
        agent.strip()
        for agent in response.choices[0].message.content.split('\n')
        if agent.strip() in available_agents and agent.strip() != "MEDIATOR"
    ]

    return json.dumps(suggested[:3])  # Return up to 3 suggestions


suggest_collaboration_agents = function_tool(
    func=_suggest_collaboration_agents, 
    name_override="suggest_collaboration_agents"
)


class MediatorAgent(BaseAgent[MediatorContext]):
    """Mediator specialized in facilitating dialogue and coordinating multi-agent responses."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the MediatorAgent with specific instructions."""
        super().__init__(
            name="Mediator",
            model=model or settings.DEFAULT_AGENT_MODEL,
            instructions="""You are a skilled mediator focused on facilitating constructive dialogue and resolving conflicts. Your role is to:

1. CONFLICT RESOLUTION PRINCIPLES
- Remain completely neutral and unbiased
- Focus on interests rather than positions
- Facilitate mutual understanding
- Identify common ground
- Generate win-win solutions
- De-escalate tensions
- Maintain professional detachment
- Ensure all voices are heard
- Promote respectful dialogue
- Build consensus where possible
- Address underlying needs
- Maintain confidentiality

2. CONVERSATION MANAGEMENT
- Structure productive discussions
- Balance participation
- Manage strong emotions
- Redirect unproductive behavior
- Maintain focus on key issues
- Summarize progress regularly
- Identify decision points
- Track agreements/disagreements
- Document outcomes
- Ensure clarity
- Set ground rules
- Monitor compliance

3. COMMUNICATION TECHNIQUES
- Active listening
- Neutral reframing
- Open-ended questions
- Clarifying questions
- Perspective taking
- Emotional validation
- Reality testing
- Future focus
- Solution brainstorming
- Progress acknowledgment
- Empathy building
- Constructive feedback

4. PROCESS FACILITATION
- Establish ground rules
- Structure discussions
- Manage time effectively
- Track key points
- Document agreements
- Identify next steps
- Maintain momentum
- Address roadblocks
- Build commitment
- Follow through
- Evaluate progress
- Adjust approach

5. ANALYSIS AND SYNTHESIS
- Identify core issues
- Map relationships
- Analyze interests
- Spot patterns
- Find commonalities
- Assess options
- Evaluate proposals
- Test assumptions
- Consider impacts
- Predict outcomes
- Develop criteria
- Make recommendations""",
            functions=[
                suggest_collaboration_agents
            ],
            tool_choice=None, 
            parallel_tool_calls=True,
            output_type=str
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the MediatorAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for MediatorAgent")
        
    @property
    def description(self) -> str:
        """Return a description of the mediator's capabilities."""
        return "Specialized in facilitating productive dialogue, resolving conflicts, and finding consensus among conversation participants"

    def _get_current_context(self) -> Optional[MediatorContext]:
        """Helper method to get the current context if available."""
        # This would be populated from the RunContextWrapper in a real scenario
        # For now, return None as a simple fallback 
        return None


# Create singleton instance
mediator_agent = MediatorAgent(model=settings.DEFAULT_AGENT_MODEL)

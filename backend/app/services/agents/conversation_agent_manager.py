from typing import Dict, List, Optional, Any, Union
import logging
import copy
from uuid import UUID

from agents import Agent

logger = logging.getLogger(__name__)

class ConversationAgentManager:
    """
    A simplified manager for agent instances that maintains proper isolation between threads.
    Uses a nested dictionary structure to ensure each thread has its own set of agent instances.
    """
    
    def __init__(self):
        # Base agent templates (not instances)
        self.base_agents: Dict[str, Agent] = {}
        
        # Thread-specific agent instances
        # Structure: {thread_id: {agent_type: agent_instance}}
        self.thread_agents: Dict[str, Dict[str, Agent]] = {}
    
    def register_base_agent(self, agent_type: str, agent: Agent) -> None:
        """
        Register a base agent template for later instantiation.
        
        Args:
            agent_type: The type identifier for the agent (e.g., "MODERATOR")
            agent: The base agent instance to use as a template
        """
        self.base_agents[agent_type] = agent
        logger.info(f"Registered base agent: {agent_type}")
    
    def get_available_base_agents(self) -> List[str]:
        """
        Get list of all available base agent types.
        
        Returns:
            List of agent type names
        """
        return list(self.base_agents.keys())
    
    def setup_conversation(self, thread_id: str, agent_types: List[str]) -> None:
        """
        Initialize agent instances for a specific conversation thread.
        
        Args:
            thread_id: The thread identifier
            agent_types: List of agent types to initialize for this thread
        """
        # Create a new dictionary for this thread if it doesn't exist
        if thread_id not in self.thread_agents:
            self.thread_agents[thread_id] = {}
        
        # Create each agent instance from the base template
        for agent_type in agent_types:
            if agent_type in self.base_agents and agent_type not in self.thread_agents[thread_id]:
                # Deep copy to create a completely independent instance
                self.thread_agents[thread_id][agent_type] = copy.deepcopy(self.base_agents[agent_type])
                logger.info(f"Created agent {agent_type} for thread {thread_id}")
            elif agent_type not in self.base_agents:
                logger.warning(f"Agent type {agent_type} not found in base agents")
    
    def get_agent(self, thread_id: str, agent_type: str) -> Optional[Agent]:
        """
        Get an agent instance for a specific thread.
        
        Args:
            thread_id: The thread identifier
            agent_type: The type of agent to get
            
        Returns:
            The agent instance or None if not found
        """
        # Check if thread exists
        if thread_id not in self.thread_agents:
            logger.warning(f"No agents found for thread {thread_id}")
            return None
        
        # Check if agent exists in this thread
        if agent_type not in self.thread_agents[thread_id]:
            logger.warning(f"Agent {agent_type} not found in thread {thread_id}")
            return None
        
        return self.thread_agents[thread_id][agent_type]
    
    def get_conversation_agent_types(self, thread_id: str) -> List[str]:
        """
        Get the agent types available for a specific conversation.
        
        Args:
            thread_id: The thread identifier
            
        Returns:
            List of agent types for this thread
        """
        if thread_id not in self.thread_agents:
            return []
        
        return list(self.thread_agents[thread_id].keys())
    
    def cleanup_conversation(self, thread_id: str) -> None:
        """
        Remove all agent instances for a thread when it's deleted.
        
        Args:
            thread_id: The thread identifier to clean up
        """
        if thread_id in self.thread_agents:
            del self.thread_agents[thread_id]
            logger.info(f"Cleaned up agents for thread {thread_id}")
    
    def update_agent_instructions(
        self, 
        thread_id: str, 
        agent_type: str, 
        instructions: str
    ) -> bool:
        """
        Update instructions for a specific agent instance.
        
        Args:
            thread_id: The thread identifier
            agent_type: The type of agent to update
            instructions: New instructions
            
        Returns:
            Success status
        """
        agent = self.get_agent(thread_id, agent_type)
        if not agent:
            return False
        
        agent.instructions = instructions
        return True

# Create singleton instance
conversation_agent_manager = ConversationAgentManager()

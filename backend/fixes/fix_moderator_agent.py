#!/usr/bin/env python
"""
Standalone script to fix the moderator agent by refreshing all handoff tools.
Run this script directly to rebuild the moderator agent's handoffs.
"""

import os
import sys
import logging
import importlib

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_moderator')

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    try:
        # First, import the agent_manager
        logger.info("Importing agent manager...")
        from app.services.agents.agent_manager import agent_manager
        
        # Then, import the moderator module
        logger.info("Importing moderator agent...")
        from app.services.agents.moderator_agent import moderator_agent, ModeratorAgent
        
        # Check if moderator_agent is properly initialized
        if moderator_agent is None:
            logger.error("moderator_agent is None - cannot fix")
            return False
            
        # Check if moderator_agent is an instance of ModeratorAgent
        if not isinstance(moderator_agent, ModeratorAgent):
            logger.error(f"moderator_agent is not a ModeratorAgent instance: {type(moderator_agent)}")
            return False
            
        # Clear existing handoffs
        logger.info(f"Clearing {len(moderator_agent.handoffs)} existing handoffs")
        moderator_agent.handoffs = []
        
        # Get all available agents
        available_agents = agent_manager.agents
        logger.info(f"Found {len(available_agents)} agents to register")
        
        # Re-register all agents with the moderator
        for agent_type, agent in available_agents.items():
            if agent_type != "MODERATOR":
                logger.info(f"Registering agent {agent_type} with moderator")
                try:
                    # Make sure agent has a name attribute
                    if not hasattr(agent, 'name'):
                        agent.name = agent_type
                    moderator_agent.register_agent(agent)
                except Exception as e:
                    logger.error(f"Error registering agent {agent_type}: {e}")
                    
        # Update moderator instructions
        try:
            agent_descriptions = agent_manager.get_agent_descriptions()
            moderator_agent.update_instructions(agent_descriptions)
            logger.info("Updated moderator instructions")
        except Exception as e:
            logger.error(f"Error updating moderator instructions: {e}")
            
        # Verify handoffs
        logger.info(f"Moderator now has {len(moderator_agent.handoffs)} handoffs")
        for h in moderator_agent.handoffs:
            logger.info(f" - {h.tool_name if hasattr(h, 'tool_name') else 'unnamed handoff'}")
            
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if main():
        logger.info("Successfully fixed moderator agent!")
    else:
        logger.error("Failed to fix moderator agent.")

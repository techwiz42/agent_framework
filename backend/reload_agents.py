#!/usr/bin/env python
"""
Script to reload all agents with proper calculator tools.
"""

import logging
import sys
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent_reloader")

async def reload_agents():
    """
    Re-initialize all agents by recreating the agent manager.
    This allows the fixed calculator tool to be used by all agents.
    """
    try:
        # Import agent manager
        from app.services.agents.agent_manager import AgentManager
        
        # Reset and initialize agent interface
        from app.services.agents.agent_interface import agent_interface
        
        # Clear the base_agents dictionary
        agent_interface.base_agents = {}
        agent_interface.agent_descriptions = {}
        
        # Re-create the agent manager to reload all agents
        logger.info("Initializing new AgentManager instance...")
        new_agent_manager = AgentManager()
        
        # Number of agents registered
        agent_count = len(agent_interface.base_agents)
        logger.info(f"Initialized {agent_count} agents")
        
        # List the agent types
        agent_types = list(agent_interface.base_agents.keys())
        logger.info(f"Agent types: {agent_types}")
        
        # Verify calculator-using agents were registered
        calculator_agents = [
            "ACCOUNTING",
            "BUSINESS",
            "BUSINESSINTELLIGENCE",
            "DATAANALYSIS", 
            "FINANCE"
        ]
        
        for agent_type in calculator_agents:
            if agent_type in agent_interface.base_agents:
                logger.info(f"Calculator agent {agent_type} registered successfully")
            else:
                logger.error(f"Calculator agent {agent_type} was not registered")
        
        # Update the global agent_manager (repointing the singleton reference)
        import app.services.agents.agent_manager
        app.services.agents.agent_manager.agent_manager = new_agent_manager
        
        return True
    
    except Exception as e:
        logger.exception(f"Error reloading agents: {e}")
        return False

async def test_calculator():
    """Test the calculator functionality on one of the agents."""
    try:
        # Import agent interface and agent manager
        from app.services.agents.agent_interface import agent_interface
        from app.services.agents.agent_manager import agent_manager
        
        # Test agent type
        agent_type = "ACCOUNTING"
        
        # Set up a test conversation
        thread_id = "test_calculator_fix"
        
        # Set up agent for conversation
        agent_interface.setup_conversation(thread_id, [agent_type])
        
        # Process a calculation request
        test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
        
        logger.info(f"Testing calculator with query: {test_query}")
        
        result = await agent_manager.process_conversation(
            message=test_query,
            conversation_agents=[agent_type],
            agents_config={},
            mention=agent_type,
            thread_id=thread_id
        )
        
        # Clean up
        agent_interface.cleanup_conversation(thread_id)
        
        # Check result
        logger.info(f"Test result: {result}")
        if "error" in result[1].lower():
            logger.error("Test failed - error in response")
            return False
        else:
            logger.info("Test passed successfully")
            return True
    
    except Exception as e:
        logger.exception(f"Error testing calculator: {e}")
        return False

async def main():
    """Main function to reload agents and test."""
    logger.info("Starting agent reload script")
    
    # Reload agents
    if await reload_agents():
        logger.info("Agents reloaded successfully")
        
        # Test calculator
        test_success = await test_calculator()
        if test_success:
            logger.info("Calculator test passed")
            return True
        else:
            logger.error("Calculator test failed")
            return False
    else:
        logger.error("Failed to reload agents")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("Agent reload and testing successful")
        sys.exit(0)
    else:
        logger.error("Agent reload or testing failed")
        sys.exit(1)
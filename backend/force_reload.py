#!/usr/bin/env python
"""
Force a reload of the entire application.
This script will completely reset and reload modules to apply the schema fixes.
"""

import sys
import importlib
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("force_reload")

# List of modules to force reload
MODULES_TO_RELOAD = [
    'app.services.agents.agent_calculator_tool',
    'app.services.agents.accounting_agent',
    'app.services.agents.business_agent',
    'app.services.agents.business_intelligence_agent',
    'app.services.agents.data_analysis_agent',
    'app.services.agents.finance_agent',
    'app.services.agents.agent_interface',
    'app.services.agents.agent_manager',
]

def force_reload_modules():
    """Force reload all important modules."""
    logger.info("Force reloading modules...")
    
    for module_name in MODULES_TO_RELOAD:
        try:
            # Check if the module is loaded
            if module_name in sys.modules:
                logger.info(f"Reloading module: {module_name}")
                
                # Force reload the module
                module = importlib.import_module(module_name)
                importlib.reload(module)
                
                logger.info(f"Successfully reloaded: {module_name}")
            else:
                logger.info(f"Module not yet loaded, importing: {module_name}")
                importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"Error reloading {module_name}: {e}")

async def recreate_agent_manager():
    """Recreate the agent_manager singleton."""
    logger.info("Recreating agent_manager...")
    
    try:
        # Import the AgentManager class and the singleton
        from app.services.agents.agent_manager import AgentManager, agent_manager
        
        # Create a new instance
        new_manager = AgentManager()
        
        # Replace the singleton instance with our new one
        import app.services.agents.agent_manager
        app.services.agents.agent_manager.agent_manager = new_manager
        
        logger.info("Successfully recreated agent_manager")
        return True
    except Exception as e:
        logger.error(f"Error recreating agent_manager: {e}")
        return False

async def test_calculator():
    """Test the calculator functionality using agent_manager."""
    logger.info("Testing calculator functionality...")
    
    try:
        # Import necessary components
        from app.services.agents.agent_manager import agent_manager
        from app.services.agents.agent_interface import agent_interface
        
        # Test with accounting agent
        agent_type = "ACCOUNTING"
        thread_id = "force_reload_test"
        
        # Set up conversation
        agent_interface.setup_conversation(thread_id, [agent_type])
        
        # Process a calculation request
        test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
        
        logger.info("Sending calculation request...")
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
        logger.info(f"Response: {result[1]}")
        
        if "error" in result[1].lower():
            logger.error("Test failed - error in response")
            return False
        else:
            logger.info("Test passed successfully!")
            return True
    
    except Exception as e:
        logger.error(f"Error testing calculator: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function to force reload and test."""
    logger.info("Starting force reload process")
    
    # Step 1: Force reload modules
    force_reload_modules()
    
    # Step 2: Recreate agent_manager
    if not await recreate_agent_manager():
        logger.error("Failed to recreate agent_manager")
        return False
    
    # Step 3: Test the calculator
    if await test_calculator():
        logger.info("Force reload and test successful!")
        return True
    else:
        logger.error("Force reload failed to fix the issue")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("Process completed successfully")
        sys.exit(0)
    else:
        logger.error("Process failed")
        sys.exit(1)
#!/usr/bin/env python3
"""
Debug and test the calculator tool with the OpenAI API.

This script creates a minimal test case that simulates how the calculator tool
is used in the agent_manager's process_conversation method, to verify that
our schema fixes resolve the validation errors.
"""

import logging
import sys
import json
import asyncio
from app.services.agents.accounting_agent import AccountingAgent
from app.services.agents.agent_manager import agent_manager
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_calculator_agent_integration():
    """Test the calculator tool in the context of the agent manager."""
    try:
        # First, verify that we can directly use the calculator tools
        logger.info("Testing calculator tools directly")
        
        from app.services.agents.agent_calculator_tool import AgentCalculatorTool
        calculator = AgentCalculatorTool()
        
        result = calculator.calculate(
            operation_type="arithmetic",
            operation="add",
            values=[1, 2, 3, 4, 5]
        )
        logger.info(f"Direct calculation result: {result}")
        
        # Verify that the tool's schema can be serialized to JSON
        calculator_tool = get_calculator_tool()
        if hasattr(calculator_tool, 'params_json_schema'):
            schema_json = json.dumps(calculator_tool.params_json_schema)
            logger.info(f"Successfully serialized schema: {len(schema_json)} characters")
        else:
            logger.error("Calculator tool missing params_json_schema attribute")
        
        # Now test with the agent_manager.process_conversation method
        logger.info("\nTesting with agent_manager.process_conversation")
        
        # Setup agent_manager with minimal required args
        try:
            result = await agent_manager.process_conversation(
                message="Can you calculate the sum of 1, 2, 3, 4, and 5?",
                conversation_agents=["ACCOUNTING"],
                agents_config={},
                mention="ACCOUNTING"  # Explicitly use the accounting agent
            )
            logger.info(f"process_conversation result type: {type(result)}")
            logger.info(f"process_conversation result: {result}")
            
            # If we get here without exception, the test passed
            logger.info("PASS: agent_manager.process_conversation completed without schema errors")
        except Exception as e:
            logger.error(f"Error in process_conversation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_calculator_agent_integration())
#!/usr/bin/env python
"""
Script to reproduce the calculator tool error.
This script will create an instance of one of the problematic agents
and attempt to invoke its calculator tool to reproduce the 400 error.
"""

import asyncio
import logging
import json
from typing import Dict, Any
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("calculator_error_test")

# Import the relevant agents
from app.services.agents.accounting_agent import AccountingAgent
from app.services.agents.business_agent import BusinessAgent
from app.services.agents.business_intelligence_agent import BusinessIntelligenceAgent
from app.services.agents.data_analysis_agent import DataAnalysisAgent
from app.services.agents.finance_agent import FinanceAgent
from app.services.agents.agent_interface import agent_interface
from app.services.agents.agent_manager import agent_manager

# Import necessary classes from the Agents SDK
from agents import Agent, RunConfig, Runner, ModelSettings, function_tool
from agents.run_context import RunContextWrapper

async def test_agent_calculator(agent_instance: Agent, agent_type: str):
    """Test calculator functionality for a specific agent."""
    logger.info(f"Testing calculator for {agent_type} agent")
    
    # Register the agent with the agent interface for testing
    test_thread_id = f"test_thread_{agent_type}"
    agent_interface.setup_conversation(test_thread_id, [agent_type])
    agent_interface.register_base_agent(agent_type, agent_instance)
    
    try:
        # Log information about the agent's tools
        tools = agent_instance.tools if hasattr(agent_instance, 'tools') else []
        logger.info(f"Agent has {len(tools)} tools")
        
        # Find the calculator tool
        calculator_tool = None
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, 'name', f"Tool {i+1}")
            logger.info(f"Tool {i+1}: {tool_name} - {type(tool)}")
            
            if tool_name == 'calculate':
                calculator_tool = tool
                logger.info(f"Found calculator tool: {tool_name}")
                
                # Check and log the schema
                if hasattr(tool, 'schema'):
                    schema = tool.schema
                    logger.info(f"Schema for calculator tool: {json.dumps(schema, indent=2)}")
                    
                    # Check if the context property has a type
                    if 'parameters' in schema and 'properties' in schema['parameters']:
                        properties = schema['parameters']['properties']
                        if 'context' in properties:
                            context_prop = properties['context']
                            if 'type' not in context_prop:
                                logger.error("ERROR: 'context' property is missing the required 'type' key")
                            else:
                                logger.info(f"Context property has type: {context_prop['type']}")
        
        if not calculator_tool:
            logger.warning("Calculator tool not found in agent tools")
            return
            
        # Test invoking the calculator tool directly
        logger.info("Testing direct calculator function call...")
        try:
            # Direct function call without context
            if hasattr(calculator_tool, 'function'):
                result = calculator_tool.function(
                    operation_type="arithmetic",
                    operation="add",
                    values=[1, 2, 3, 4, 5]
                )
                logger.info(f"Direct function call result: {result}")
        except Exception as e:
            logger.error(f"Error in direct function call: {e}")
        
        # Create a run context for testing
        test_context = RunContextWrapper({})
        
        # Test the agent with a simple message that should trigger calculator use
        logger.info("Testing agent through Runner API...")
        try:
            # Create a run config
            run_config = RunConfig(
                workflow_name=f"{agent_type} Calculator Test",
                model="claude-3-haiku-20240307"
            )
            
            # Test query that should trigger calculator
            test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
            
            # Run the agent
            result = await Runner.run(
                starting_agent=agent_instance,
                input=test_query,
                context=test_context,
                run_config=run_config
            )
            
            logger.info(f"Agent response: {result.final_output}")
            
        except Exception as e:
            logger.error(f"Error running agent with Runner: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error testing {agent_type} agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # Clean up
        agent_interface.cleanup_conversation(test_thread_id)

async def test_all_calculator_agents():
    """Test calculator functionality across all problematic agents."""
    agents = [
        (AccountingAgent(), "ACCOUNTING"),
        (BusinessAgent(), "BUSINESS"),
        (BusinessIntelligenceAgent(), "BUSINESSINTELLIGENCE"),
        (DataAnalysisAgent(), "DATAANALYSIS"),
        (FinanceAgent(), "FINANCE")
    ]
    
    for agent_instance, agent_type in agents:
        logger.info(f"===== Testing {agent_type} Agent =====")
        await test_agent_calculator(agent_instance, agent_type)
        logger.info(f"===== Completed {agent_type} Agent Test =====\n")

async def mentioned_agent_test():
    """Simulate the 'mentioned' agent scenario that causes the 400 error."""
    logger.info("Testing 'mentioned' agent scenario...")
    
    # Create an agent instance
    agent_instance = AccountingAgent()
    agent_type = "ACCOUNTING"
    
    # Setup conversation with agent manager
    test_thread_id = "test_mentioned_agent"
    owner_id = None  # Not needed for this test
    
    try:
        # Register the agent with agent_interface for use by agent_manager
        available_agents = [agent_type]
        agent_interface.setup_conversation(test_thread_id, available_agents)
        agent_interface.register_base_agent(agent_type, agent_instance)
        
        # Use the agent_manager.process_conversation method with mention
        logger.info("Calling agent_manager.process_conversation with explicit mention...")
        test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
        
        # This should trigger the 400 error when using the calculator tool
        result = await agent_manager.process_conversation(
            message=test_query,
            conversation_agents=available_agents,
            agents_config={},
            mention=agent_type,  # Explicitly mention the agent with calculator
            thread_id=test_thread_id,
            owner_id=owner_id
        )
        
        logger.info(f"Result from agent_manager: {result}")
        
    except Exception as e:
        logger.error(f"Error in mentioned agent test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # Clean up
        agent_interface.cleanup_conversation(test_thread_id)

async def run_tests():
    """Run all the tests."""
    logger.info("Starting calculator tool error reproduction tests")
    
    # First test individual agents
    await test_all_calculator_agents()
    
    # Then test the mentioned agent scenario that causes the 400 error
    await mentioned_agent_test()
    
    logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(run_tests())
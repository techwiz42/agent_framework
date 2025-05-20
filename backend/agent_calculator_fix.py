#!/usr/bin/env python
"""
Direct fix for the calculator tool schema issue.
This will fix the tools in the base agents where the issue originates.
"""

import logging
import sys
import json
import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("calculator_fix")

# Import required components
from app.services.agents.agent_interface import agent_interface
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

def fix_calculator_tools():
    """Fix the calculator tools directly in the base agents."""
    # Get the calculator tools with fixed schemas
    fixed_calculator_tool = get_calculator_tool()
    fixed_interpreter_tool = get_interpreter_tool()
    
    # List of agents using calculator tools
    calculator_agents = [
        "ACCOUNTING",
        "BUSINESS",
        "BUSINESSINTELLIGENCE",
        "DATAANALYSIS",
        "FINANCE"
    ]
    
    fixed_count = 0
    
    # Access the base_agents directly to replace the tools
    for agent_type, agent in agent_interface.base_agents.items():
        if agent_type in calculator_agents:
            logger.info(f"Fixing calculator tools for agent: {agent_type}")
            
            if not hasattr(agent, 'tools'):
                logger.warning(f"Agent {agent_type} has no tools attribute")
                continue
                
            # Find and replace the calculator tools
            replaced = False
            for i, tool in enumerate(agent.tools):
                tool_name = getattr(tool, 'name', '')
                
                if tool_name == 'calculate':
                    logger.info(f"Replacing calculator tool in {agent_type}")
                    agent.tools[i] = fixed_calculator_tool
                    replaced = True
                    fixed_count += 1
                    
                elif tool_name == 'interpret_calculation_results':
                    logger.info(f"Replacing interpreter tool in {agent_type}")
                    agent.tools[i] = fixed_interpreter_tool
                    replaced = True
                    fixed_count += 1
            
            if replaced:
                logger.info(f"Successfully replaced calculator tools in {agent_type}")
            else:
                logger.warning(f"No calculator tools found in {agent_type}")
    
    return fixed_count

def test_agent(agent_type="ACCOUNTING"):
    """
    Test a calculator-using agent to verify the fix.
    This only checks if we can access the schema without errors.
    """
    logger.info(f"Testing agent: {agent_type}")
    
    # Get the agent
    agent = agent_interface.base_agents.get(agent_type)
    if not agent:
        logger.error(f"Agent {agent_type} not found in base_agents")
        return False
    
    # Find the calculator tool
    calculator_tool = None
    for tool in agent.tools:
        if getattr(tool, 'name', '') == 'calculate':
            calculator_tool = tool
            break
    
    if not calculator_tool:
        logger.error(f"Calculator tool not found in {agent_type}")
        return False
    
    # Check if the tool has a valid schema
    if hasattr(calculator_tool, 'schema'):
        schema = calculator_tool.schema
        if 'parameters' in schema and 'properties' in schema['parameters'] and 'context' in schema['parameters']['properties']:
            context_prop = schema['parameters']['properties']['context']
            if 'type' in context_prop:
                logger.info(f"Schema valid: context property has type '{context_prop['type']}'")
                return True
            else:
                logger.error(f"Schema invalid: context property has no type key")
                return False
    
    logger.error(f"Could not verify schema")
    return False

def main():
    """Main function"""
    logger.info("Starting calculator tool fix")
    
    # Fix the calculator tools
    fixed_count = fix_calculator_tools()
    logger.info(f"Fixed {fixed_count} calculator tools")
    
    # Test a calculator-using agent
    for agent_type in ["ACCOUNTING", "BUSINESS", "FINANCE", "DATAANALYSIS", "BUSINESSINTELLIGENCE"]:
        success = test_agent(agent_type)
        if success:
            logger.info(f"Test passed for {agent_type}")
        else:
            logger.error(f"Test failed for {agent_type}")
    
    return fixed_count > 0

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Calculator tool fix applied successfully")
        sys.exit(0)
    else:
        logger.error("Calculator tool fix failed")
        sys.exit(1)
#!/usr/bin/env python
"""
Script to fix all the schema issues in the loaded agents.
This script applies the fix to all calculator tools in all agents that have been initialized.
"""

import asyncio
import logging
import sys
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("schema_fixer")

# Import agents
from app.services.agents.agent_interface import agent_interface
from app.services.agents.agent_manager import agent_manager

def fix_tool_schema(tool):
    """Fix the schema of a single tool."""
    schema_fixed = False
    schema_attr = None
    
    # Find which attribute contains the schema
    if hasattr(tool, 'schema'):
        schema_attr = 'schema'
    elif hasattr(tool, 'params_json_schema'):
        schema_attr = 'params_json_schema'
    
    if not schema_attr:
        logger.warning(f"Tool {getattr(tool, 'name', 'unknown')} has no schema attribute")
        return False
    
    schema = getattr(tool, schema_attr)
    if not isinstance(schema, dict):
        logger.warning(f"Schema for {getattr(tool, 'name', 'unknown')} is not a dictionary: {type(schema)}")
        return False
    
    # Navigate to the properties section
    if 'parameters' in schema and 'properties' in schema['parameters']:
        properties = schema['parameters']['properties']
    elif 'properties' in schema:
        properties = schema['properties']
    else:
        logger.warning(f"No properties section found in schema for {getattr(tool, 'name', 'unknown')}")
        return False
    
    # Fix the context property
    if 'context' in properties:
        context_prop = properties['context']
        
        # Add type if it's missing
        if 'type' not in context_prop:
            logger.info(f"Fixing context property for tool: {getattr(tool, 'name', 'unknown')}")
            
            # Properly set the type
            if 'anyOf' in context_prop:
                # Add type to the property with anyOf
                context_prop['type'] = 'object'
                schema_fixed = True
            else:
                # Replace with a properly formed schema
                properties['context'] = {
                    'type': 'object',
                    'description': context_prop.get('description', 'The run context wrapper.')
                }
                schema_fixed = True
    
    # Fix other object properties that may be missing type
    for prop_name, prop in properties.items():
        if prop_name != 'context' and isinstance(prop, dict) and 'type' not in prop:
            if prop_name == 'values':
                # Ensure values has array type and items schema
                properties[prop_name]['type'] = 'array'
                if 'items' not in properties[prop_name]:
                    properties[prop_name]['items'] = {'type': 'number'}
                schema_fixed = True
            elif prop_name == 'calculation_results':
                # Ensure calculation_results has object type
                properties[prop_name]['type'] = 'object'
                schema_fixed = True
            else:
                # Default to string for other properties
                properties[prop_name]['type'] = 'string'
                schema_fixed = True
    
    # Make all parameters optional for maximum compatibility
    if 'parameters' in schema and 'required' in schema['parameters']:
        schema['parameters']['required'] = []
        schema_fixed = True
    
    return schema_fixed

def fix_agent_tools(agent):
    """Fix all tools in a single agent."""
    if not hasattr(agent, 'tools') or not agent.tools:
        logger.info(f"Agent {agent.name} has no tools")
        return 0
    
    fixed_count = 0
    
    for i, tool in enumerate(agent.tools):
        tool_name = getattr(tool, 'name', f"Tool {i+1}")
        logger.debug(f"Checking tool: {tool_name}")
        
        # Apply schema fix to this tool
        if fix_tool_schema(tool):
            logger.info(f"Fixed schema for tool: {tool_name}")
            fixed_count += 1
    
    return fixed_count

def fix_all_agents():
    """Fix all agents available in the agent interface."""
    fixed_agents = 0
    fixed_tools = 0
    
    # Get all agent types
    agent_types = agent_interface.get_agent_types()
    logger.info(f"Found {len(agent_types)} agent types")
    
    # Process each agent type
    for agent_type in agent_types:
        # Try to get the base agent through an appropriate method
        try:
            # First see if there's a direct access method
            if hasattr(agent_interface, '_base_agents') and agent_type in agent_interface._base_agents:
                agent = agent_interface._base_agents[agent_type]
            else:
                # If the agent is not accessible directly, create a temporary thread and get it
                tmp_thread_id = f"tmp_thread_{agent_type}"
                agent_interface.setup_conversation(tmp_thread_id, [agent_type])
                agent = agent_interface.get_agent(tmp_thread_id, agent_type)
                agent_interface.cleanup_conversation(tmp_thread_id)
        except Exception as e:
            logger.error(f"Error accessing agent {agent_type}: {e}")
            continue
        
        if not agent:
            logger.warning(f"Agent {agent_type} not found in interface")
            continue
        
        logger.info(f"Processing agent: {agent_type}")
        
        # Fix all tools in this agent
        tools_fixed = fix_agent_tools(agent)
        
        if tools_fixed > 0:
            fixed_agents += 1
            fixed_tools += tools_fixed
            logger.info(f"Fixed {tools_fixed} tools in agent {agent_type}")
    
    return fixed_agents, fixed_tools

async def main():
    """Main function to run the fix."""
    logger.info("Starting agent schema fix script")
    
    try:
        # Fix all agents
        fixed_agents, fixed_tools = fix_all_agents()
        
        logger.info(f"Schema fix complete. Fixed {fixed_tools} tools across {fixed_agents} agents.")
        
        # Test with a calculator-using agent
        logger.info("Testing fixes by calling a calculator-using agent")
        
        try:
            # Test with accounting agent
            test_thread_id = "test_schema_fix"
            agent_type = "ACCOUNTING"
            available_agents = [agent_type]
            
            # Set up conversation with the agent
            agent_interface.setup_conversation(test_thread_id, available_agents)
            
            # Use the agent_manager to process a calculation request
            test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
            
            result = await agent_manager.process_conversation(
                message=test_query,
                conversation_agents=available_agents,
                agents_config={},
                mention=agent_type,
                thread_id=test_thread_id
            )
            
            logger.info(f"Test result: {result}")
            
            # Clean up
            agent_interface.cleanup_conversation(test_thread_id)
            
            if "error" in result[1].lower():
                logger.error("Test failed - error in response")
                return False
            else:
                logger.info("Test passed - no error in response")
                return True
            
        except Exception as e:
            logger.exception(f"Error testing agent: {e}")
            return False
        
    except Exception as e:
        logger.exception(f"Error fixing schemas: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("Schema fixes applied and tested successfully")
        sys.exit(0)
    else:
        logger.error("Schema fixes failed or test unsuccessful")
        sys.exit(1)
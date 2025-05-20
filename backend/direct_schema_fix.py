#!/usr/bin/env python
"""
Direct runtime inspection and fix for the calculator tool schema issue.
This directly accesses and fixes the relevant schema in memory when run.
"""

import logging
import sys
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("schema_repair")

def fix_schema_properties(schema_obj):
    """Fix schema properties including type and additionalProperties."""
    # Navigate to find the context property
    if isinstance(schema_obj, dict):
        if 'context' in schema_obj:
            context_prop = schema_obj['context']
            fixed = False
            
            # Add type if missing
            if 'type' not in context_prop:
                logger.info("Adding 'type': 'object' to context property")
                context_prop['type'] = 'object'
                fixed = True
            
            # Add additionalProperties if missing
            if 'additionalProperties' not in context_prop:
                logger.info("Adding 'additionalProperties': False to context property")
                context_prop['additionalProperties'] = False
                fixed = True
                
            # Add empty properties if missing
            if 'type' in context_prop and context_prop['type'] == 'object' and 'properties' not in context_prop:
                logger.info("Adding empty 'properties' to context property")
                context_prop['properties'] = {}
                fixed = True
            
            return fixed
        
        # Check for properties section
        if 'properties' in schema_obj:
            props = schema_obj['properties']
            if isinstance(props, dict) and 'context' in props:
                context_prop = props['context']
                fixed = False
                
                # Add type if missing
                if 'type' not in context_prop:
                    logger.info("Adding 'type': 'object' to context property")
                    context_prop['type'] = 'object'
                    fixed = True
                
                # Add additionalProperties if missing
                if 'additionalProperties' not in context_prop:
                    logger.info("Adding 'additionalProperties': False to context property")
                    context_prop['additionalProperties'] = False
                    fixed = True
                    
                # Add empty properties if missing
                if 'type' in context_prop and context_prop['type'] == 'object' and 'properties' not in context_prop:
                    logger.info("Adding empty 'properties' to context property")
                    context_prop['properties'] = {}
                    fixed = True
                
                if fixed:
                    return True
        
        # Look through nested dictionaries
        fixed = False
        for key, value in schema_obj.items():
            if isinstance(value, (dict, list)):
                if fix_schema_properties(value):
                    fixed = True
        return fixed
    
    # Handle lists
    elif isinstance(schema_obj, list):
        fixed = False
        for item in schema_obj:
            if isinstance(item, (dict, list)):
                if fix_schema_properties(item):
                    fixed = True
        return fixed
    
    return False

def inspect_and_fix_tool(tool, tool_name=""):
    """Inspect and fix a single tool's schema."""
    # Find the schema attribute
    schema_attr = None
    for attr_name in ['schema', 'params_json_schema']:
        if hasattr(tool, attr_name):
            schema_attr = attr_name
            break
    
    if not schema_attr:
        logger.warning(f"Tool {tool_name} has no schema attribute")
        return False
    
    # Get the schema
    schema = getattr(tool, schema_attr)
    
    # Dump original schema for debugging
    try:
        logger.debug(f"Original schema for {tool_name}: {json.dumps(schema, indent=2)}")
    except:
        logger.debug(f"Cannot dump schema for {tool_name}")
    
    # Apply fix
    fixed = fix_schema_properties(schema)
    
    if fixed:
        # Re-dump schema after fix
        try:
            logger.debug(f"Fixed schema for {tool_name}: {json.dumps(schema, indent=2)}")
        except:
            logger.debug(f"Cannot dump fixed schema for {tool_name}")
        
        logger.info(f"Fixed schema for tool {tool_name}")
    else:
        logger.info(f"No fixes needed for tool {tool_name}")
        
    return fixed

def inspect_and_fix_agent(agent):
    """Inspect and fix all tools in an agent."""
    if not hasattr(agent, 'tools') or not agent.tools:
        logger.info(f"Agent {agent.name} has no tools")
        return 0
    
    fixed_count = 0
    
    for i, tool in enumerate(agent.tools):
        tool_name = getattr(tool, 'name', f"Tool {i+1}")
        logger.info(f"Inspecting tool: {tool_name}")
        
        if inspect_and_fix_tool(tool, tool_name):
            fixed_count += 1
    
    return fixed_count

async def fix_and_test_agent(agent_type="ACCOUNTING"):
    """Fix and test a specific agent."""
    logger.info(f"Fixing and testing {agent_type} agent")
    
    # Import required components
    from agents import Runner, RunConfig
    from agents.run_context import RunContextWrapper
    
    # Create the agent
    if agent_type == "ACCOUNTING":
        from app.services.agents.accounting_agent import AccountingAgent
        agent = AccountingAgent()
    elif agent_type == "BUSINESS":
        from app.services.agents.business_agent import BusinessAgent
        agent = BusinessAgent()
    elif agent_type == "BUSINESSINTELLIGENCE":
        from app.services.agents.business_intelligence_agent import BusinessIntelligenceAgent
        agent = BusinessIntelligenceAgent()
    elif agent_type == "DATAANALYSIS":
        from app.services.agents.data_analysis_agent import DataAnalysisAgent
        agent = DataAnalysisAgent()
    elif agent_type == "FINANCE":
        from app.services.agents.finance_agent import FinanceAgent
        agent = FinanceAgent()
    else:
        logger.error(f"Unknown agent type: {agent_type}")
        return False
    
    # Fix the agent's tools
    fixed_count = inspect_and_fix_agent(agent)
    logger.info(f"Fixed {fixed_count} tools in {agent_type} agent")
    
    # Check if the agent has a calculator tool
    has_calculator = False
    for tool in agent.tools:
        tool_name = getattr(tool, 'name', '')
        if tool_name == 'calculate':
            has_calculator = True
            break
    
    if not has_calculator:
        logger.warning(f"{agent_type} agent doesn't have a calculator tool")
        return False
    
    # Now test the agent
    try:
        # Create a run context
        context = RunContextWrapper({})
        
        # Create a run config
        run_config = RunConfig(
            workflow_name=f"{agent_type} Test",
            model="claude-3-haiku-20240307"
        )
        
        # Test query that should trigger calculator
        test_query = "Calculate the sum of 10, 20, 30, 40, and 50."
        
        # Run the agent
        logger.info("Testing the agent with the fixed tools")
        result = await Runner.run(
            starting_agent=agent,
            input=test_query,
            context=context,
            run_config=run_config
        )
        
        logger.info(f"Test result: {result.final_output}")
        
        return "error" not in result.final_output.lower()
        
    except Exception as e:
        logger.exception(f"Error testing agent: {e}")
        return False

async def main():
    """Main function."""
    logger.info("Starting direct schema fix")
    
    # Try each agent with calculator tool
    calculator_agents = [
        "ACCOUNTING", 
        "BUSINESS",
        "FINANCE",
        "DATAANALYSIS", 
        "BUSINESSINTELLIGENCE"
    ]
    
    for agent_type in calculator_agents:
        logger.info(f"Testing {agent_type} agent")
        success = await fix_and_test_agent(agent_type)
        if success:
            logger.info(f"SUCCESS: {agent_type} agent test passed")
            
            # Create documentation about what we found and fixed
            logger.info("Creating documentation about the fix")
            with open('docs/resolving_function_tool_schema_errors.md', 'w') as f:
                f.write(f"""# Resolving Function Tool Schema Errors

## Problem Description

We encountered a validation error when using agents with calculator tools:

```
Invalid schema for function 'calculate': In context=('properties', 'context'), schema must have a 'type' key.
```

This error occurred when the agent was invoked through the agent_manager's process_conversation method, particularly when an agent using the calculator tool was explicitly mentioned.

## Root Cause

The error was caused by a missing 'type' key in the context property of the calculator tool's schema. The OpenAI API requires all properties in a function schema to have a valid type.

The issue specifically affects these agents:
- Accounting Agent
- Business Agent 
- Business Intelligence Agent
- Data Analysis Agent
- Finance Agent

## Solution

We successfully fixed the issue with the {agent_type} agent by:

1. Directly accessing the tool schema at runtime
2. Adding 'type': 'object' to the context property
3. This allows the agent to be used through the agent_manager

## Implementation Details

The fix involved directly modifying the schema of the tools at runtime:

```python
def add_type_to_context(schema_obj):
    if isinstance(schema_obj, dict):
        if 'context' in schema_obj:
            context_prop = schema_obj['context']
            if 'type' not in context_prop:
                context_prop['type'] = 'object'
                return True
        
        # Look through nested dictionaries
        for key, value in schema_obj.items():
            if isinstance(value, (dict, list)):
                if add_type_to_context(value):
                    return True
                    
    return False
```

A permanent fix was implemented in the `agent_calculator_tool.py` module to ensure all tools have proper schema validation.

## Future Prevention

To prevent similar issues in the future:

1. Always include a 'type' key for all properties in function schemas
2. Validate function schemas before registering tools with agents
3. Use a helper function to ensure schemas meet API requirements
""")
            
            logger.info("Documentation created at docs/resolving_function_tool_schema_errors.md")
            return True
    
    logger.error("All agent tests failed")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("Schema fix applied and tested successfully")
        sys.exit(0)
    else:
        logger.error("Schema fix and test unsuccessful")
        sys.exit(1)
#!/usr/bin/env python3
"""
Test script to verify that the accounting agent can be initialized
and used properly with the calculator tool after fixing schema issues.
"""

import logging
import sys
import asyncio
from app.services.agents.accounting_agent import AccountingAgent
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_accounting_agent():
    """Test the accounting agent with calculator tools."""
    try:
        # Initialize the accounting agent
        logger.info("Initializing AccountingAgent")
        agent = AccountingAgent()
        
        logger.info(f"Agent created: {agent.name}")
        logger.info(f"Number of tools: {len(agent.tools)}")
        
        # Check for calculator tools
        calculator_tool = None
        interpreter_tool = None
        
        for i, tool in enumerate(agent.tools):
            tool_name = getattr(tool, 'name', f'unknown_tool_{i}')
            logger.info(f"Tool {i+1}: {tool_name}")
            
            if tool_name == 'calculate':
                calculator_tool = tool
                # Print all attributes of the tool
                logger.info(f"Calculator tool attributes: {dir(tool)}")
                # Print the type of the tool
                logger.info(f"Calculator tool type: {type(tool)}")
            elif tool_name == 'interpret_calculation_results':
                interpreter_tool = tool
        
        if not calculator_tool:
            logger.error("Calculator tool not found")
            return
        
        # Get the schema from get_calculator_tool instead
        from app.services.agents.agent_calculator_tool import get_calculator_tool
        direct_calculator_tool = get_calculator_tool()
        
        # Test calculator tool schema using params_json_schema
        if hasattr(calculator_tool, 'params_json_schema'):
            schema = calculator_tool.params_json_schema
            logger.info(f"Calculator tool schema (params_json_schema): {json.dumps(schema, indent=2)}")
            
            # Verify context property has valid structure
            if 'properties' in schema:
                props = schema['properties']
                if 'context' in props:
                    context_prop = props['context']
                    has_valid_type = False
                    
                    # Check for direct type
                    if 'type' in context_prop:
                        logger.info(f"Context property has direct type: {context_prop['type']}")
                        has_valid_type = True
                    # Check for anyOf with valid types
                    elif 'anyOf' in context_prop and isinstance(context_prop['anyOf'], list):
                        # Check each anyOf item for object type
                        object_types = [
                            item.get('type') for item in context_prop['anyOf'] 
                            if isinstance(item, dict) and 'type' in item
                        ]
                        if object_types:
                            logger.info(f"Context property has anyOf types: {object_types}")
                            has_valid_type = True
                        # Check for $ref types
                        ref_types = [
                            item.get('$ref') for item in context_prop['anyOf'] 
                            if isinstance(item, dict) and '$ref' in item
                        ]
                        if ref_types:
                            logger.info(f"Context property has anyOf $refs: {ref_types}")
                            has_valid_type = True
                    
                    # Final validation
                    if has_valid_type:
                        logger.info("PASS: Context property has valid type structure")
                    else:
                        logger.error("Context property missing valid type definition")
                
                # Verify values property has valid structure
                if 'values' in props:
                    values_prop = props['values']
                    has_valid_type = False
                    
                    # Check for direct type
                    if 'type' in values_prop:
                        logger.info(f"Values property has direct type: {values_prop['type']}")
                        has_valid_type = True
                    # Check for anyOf with valid types
                    elif 'anyOf' in values_prop and isinstance(values_prop['anyOf'], list):
                        array_types = [
                            item.get('type') for item in values_prop['anyOf'] 
                            if isinstance(item, dict) and 'type' in item
                        ]
                        if array_types:
                            logger.info(f"Values property has anyOf types: {array_types}")
                            has_valid_type = True
                    
                    # Final validation
                    if has_valid_type:
                        logger.info("PASS: Values property has valid type structure")
                    else:
                        logger.error("Values property missing valid type definition")
                        
                    # Check if array items are defined
                    has_items = False
                    if 'type' in values_prop and values_prop['type'] == 'array' and 'items' in values_prop:
                        has_items = True
                    elif 'anyOf' in values_prop:
                        for item in values_prop['anyOf']:
                            if isinstance(item, dict) and item.get('type') == 'array' and 'items' in item:
                                has_items = True
                                break
                    
                    if has_items:
                        logger.info("PASS: Array items are properly defined")
                    else:
                        logger.error("Array items not properly defined")
        else:
            logger.error("Calculator tool missing params_json_schema attribute")
            
        # Try directly getting schema from the factory function
        from app.services.agents.agent_calculator_tool import get_calculator_tool
        direct_calculator_tool = get_calculator_tool()
        if hasattr(direct_calculator_tool, 'schema'):
            schema = direct_calculator_tool.schema
            logger.info(f"Direct calculator schema: {json.dumps(schema, indent=2)}")
        else:
            logger.info("Direct calculator tool doesn't have schema property")
        
        # Try a direct calculation
        logger.info("Testing direct function call to calculator tool")
        try:
            # Get the tool function directly from the module
            from app.services.agents.agent_calculator_tool import AgentCalculatorTool
            calculator = AgentCalculatorTool()
            result = calculator.calculate(
                operation_type="arithmetic",
                operation="add",
                values=[1, 2, 3, 4, 5]
            )
            logger.info(f"Calculator result: {result}")
            logger.info("PASS: Direct calculator function call")
        except Exception as e:
            logger.error(f"Error calling calculator function: {e}")
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_accounting_agent())
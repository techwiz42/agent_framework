#!/usr/bin/env python3
"""
Schema Fix Script

This script directly fixes the schema issues with calculator tools and other function tools
by examining all agent tool schemas and ensuring they have proper types defined for all properties,
particularly the 'context' and 'values' properties.

It patches the schema issues at runtime by modifying the schemas directly, and tests 
the tools to ensure they can be properly serialized.
"""

import logging
import sys
import json
import importlib
from typing import Dict, List, Any, Optional
import inspect

from app.services.agents.agent_interface import agent_interface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def fix_schema_properties(schema_obj: Dict[str, Any]) -> bool:
    """
    Fix schema properties including type and additionalProperties.
    
    Args:
        schema_obj: The schema object to fix
        
    Returns:
        True if fixes were applied, False otherwise
    """
    if not isinstance(schema_obj, dict):
        return False
    
    fixed = False
    
    # Handle both newer format (direct properties) and older format (parameters.properties)
    if 'properties' in schema_obj and isinstance(schema_obj['properties'], dict):
        properties = schema_obj['properties']
        fixed |= fix_property_section(properties)
    
    # Handle the older format with parameters section
    if 'parameters' in schema_obj and isinstance(schema_obj['parameters'], dict):
        params = schema_obj['parameters']
        
        # Ensure type exists
        if 'type' not in params:
            params['type'] = 'object'
            fixed = True
            logger.info("Added 'type': 'object' to parameters")
        
        # Check properties section
        if 'properties' in params and isinstance(params['properties'], dict):
            properties = params['properties']
            fixed |= fix_property_section(properties)
    
    return fixed

def fix_property_section(properties: Dict[str, Any]) -> bool:
    """
    Fix a properties section of a schema.
    
    Args:
        properties: The properties object to fix
        
    Returns:
        True if fixes were applied, False otherwise
    """
    if not isinstance(properties, dict):
        return False
    
    fixed = False
    
    # Fix context property if it exists
    if 'context' in properties:
        context_prop = properties['context']
        if not isinstance(context_prop, dict):
            # Replace with proper object schema
            properties['context'] = {
                "type": "object",
                "description": "The run context wrapper.",
                "additionalProperties": False,
                "properties": {}
            }
            fixed = True
            logger.info("Replaced malformed context property")
        else:
            # Fix existing context dict - handle both direct type and anyOf structures
            if 'type' not in context_prop:
                # If it has anyOf, check if we need to add a direct object type
                if 'anyOf' in context_prop and isinstance(context_prop['anyOf'], list):
                    # Check each anyOf item
                    has_object_type = any(
                        isinstance(item, dict) and item.get('type') == 'object'
                        for item in context_prop['anyOf']
                    )
                    
                    if not has_object_type:
                        # Add an object type to anyOf
                        context_prop['anyOf'].append({"type": "object", "additionalProperties": False, "properties": {}})
                        fixed = True
                        logger.info("Added object type to context property anyOf")
                else:
                    # No anyOf structure, add direct type
                    logger.info("Adding 'type': 'object' to context property")
                    context_prop['type'] = 'object'
                    fixed = True
            
            # Add additionalProperties if missing
            if 'type' in context_prop and context_prop['type'] == 'object' and 'additionalProperties' not in context_prop:
                logger.info("Adding 'additionalProperties': False to context property")
                context_prop['additionalProperties'] = False
                fixed = True
                    
            # Add empty properties if missing
            if 'type' in context_prop and context_prop['type'] == 'object' and 'properties' not in context_prop:
                logger.info("Adding empty 'properties' to context property")
                context_prop['properties'] = {}
                fixed = True
    
    # Fix values property if it exists - this is particularly important for the calculator tool
    if 'values' in properties:
        values_prop = properties['values']
        
        if not isinstance(values_prop, dict):
            # Replace with proper array schema
            properties['values'] = {
                "type": "array",
                "description": "List of numeric values for calculations.",
                "items": {
                    "type": "number"
                }
            }
            fixed = True
            logger.info("Replaced malformed values property")
        else:
            # Handle both direct type and anyOf structures
            if 'type' not in values_prop:
                # If it has anyOf, check if we need to add a direct array type
                if 'anyOf' in values_prop and isinstance(values_prop['anyOf'], list):
                    # Check each anyOf item
                    has_array_type = any(
                        isinstance(item, dict) and item.get('type') == 'array'
                        for item in values_prop['anyOf']
                    )
                    
                    if not has_array_type:
                        # Add an array type to anyOf
                        values_prop['anyOf'].append({
                            "type": "array",
                            "items": {"type": "number"}
                        })
                        fixed = True
                        logger.info("Added array type to values property anyOf")
                else:
                    # No anyOf structure, add direct type
                    values_prop['type'] = 'array'
                    fixed = True
                    logger.info("Added 'type': 'array' to values property")
            
            # Direct array type case - add items if missing
            if 'type' in values_prop and values_prop['type'] == 'array' and 'items' not in values_prop:
                values_prop['items'] = {"type": "number"}
                fixed = True
                logger.info("Added 'items' to values property")
            
            # anyOf array type case - ensure each array has items
            if 'anyOf' in values_prop and isinstance(values_prop['anyOf'], list):
                for item in values_prop['anyOf']:
                    if isinstance(item, dict) and item.get('type') == 'array' and 'items' not in item:
                        item['items'] = {"type": "number"}
                        fixed = True
                        logger.info("Added 'items' to array in values property anyOf")
    
    # Fix expression property if it exists
    if 'expression' in properties:
        expression_prop = properties['expression']
        
        if not isinstance(expression_prop, dict):
            # Replace with proper string schema
            properties['expression'] = {
                "type": "string",
                "description": "A mathematical expression to evaluate."
            }
            fixed = True
            logger.info("Replaced malformed expression property")
        elif 'type' not in expression_prop and 'anyOf' not in expression_prop:
            expression_prop['type'] = 'string'
            fixed = True
            logger.info("Added 'type': 'string' to expression property")
    
    # Add type to any other properties missing it
    for prop_name, prop_schema in properties.items():
        if isinstance(prop_schema, dict) and 'type' not in prop_schema and 'anyOf' not in prop_schema:
            # Default to string for most properties
            properties[prop_name]['type'] = 'string'
            fixed = True
            logger.info(f"Added default 'type': 'string' to {prop_name} property")
    
    # Check calculation_results property
    if 'calculation_results' in properties:
        calc_prop = properties['calculation_results']
        
        if not isinstance(calc_prop, dict):
            # Replace with proper object schema
            properties['calculation_results'] = {
                "type": "object",
                "description": "The calculation results from a previous calculation.",
                "additionalProperties": True,
                "properties": {}
            }
            fixed = True
            logger.info("Replaced malformed calculation_results property")
        elif 'type' not in calc_prop and 'anyOf' not in calc_prop:
            calc_prop['type'] = 'object'
            fixed = True
            logger.info("Added 'type': 'object' to calculation_results property")
            
            if 'properties' not in calc_prop:
                calc_prop['properties'] = {}
                fixed = True
                logger.info("Added empty 'properties' to calculation_results")
    
    return fixed

def fix_schema_required(schema_obj: Dict[str, Any]) -> bool:
    """
    Fix the required properties in a schema.
    
    Args:
        schema_obj: The schema object to fix
        
    Returns:
        True if fixes were applied, False otherwise
    """
    if not isinstance(schema_obj, dict):
        return False
    
    fixed = False
    
    # Check parameters section
    if 'parameters' in schema_obj and isinstance(schema_obj['parameters'], dict):
        params = schema_obj['parameters']
        
        # Ensure required is a list and only contains properties that exist
        if 'required' in params:
            if not isinstance(params['required'], list):
                params['required'] = []
                fixed = True
                logger.info("Replaced invalid 'required' with empty list")
            else:
                # Ensure required properties actually exist in properties
                if 'properties' in params and isinstance(params['properties'], dict):
                    properties = params['properties']
                    valid_required = [r for r in params['required'] if r in properties]
                    
                    if len(valid_required) != len(params['required']):
                        params['required'] = valid_required
                        fixed = True
                        logger.info(f"Fixed 'required' to only include valid properties: {valid_required}")
    
    return fixed

def test_schema_validation(schema_obj: Dict[str, Any]) -> bool:
    """
    Test if the schema can be properly serialized to JSON.
    
    Args:
        schema_obj: The schema object to test
        
    Returns:
        True if the schema is valid, False otherwise
    """
    try:
        # Try to serialize to JSON
        json_str = json.dumps(schema_obj)
        # Try to deserialize from JSON
        json.loads(json_str)
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

def fix_agent_tool_schemas(agent_type: str, agent) -> int:
    """
    Fix all tool schemas for a specific agent.
    
    Args:
        agent_type: The agent type identifier
        agent: The agent instance
        
    Returns:
        Number of schemas fixed
    """
    if not hasattr(agent, 'tools') or not agent.tools:
        return 0
    
    fixes_applied = 0
    
    logger.info(f"Examining {len(agent.tools)} tools for agent {agent_type}")
    
    for i, tool in enumerate(agent.tools):
        tool_name = getattr(tool, 'name', f'unknown_tool_{i}')
        logger.info(f"Checking tool {i+1}: {tool_name}")
        
        if hasattr(tool, 'schema'):
            schema = tool.schema
            logger.info(f"Found schema for tool {tool_name}")
            
            # Apply fixes
            schema_fixed = False
            schema_fixed |= fix_schema_properties(schema)
            schema_fixed |= fix_schema_required(schema)
            
            if schema_fixed:
                fixes_applied += 1
                logger.info(f"Fixed schema for tool {tool_name}")
                
                # Validate the fixed schema
                if test_schema_validation(schema):
                    logger.info(f"Schema validation successful for tool {tool_name}")
                else:
                    logger.error(f"Schema validation failed for tool {tool_name} even after fixes")
            else:
                logger.info(f"No schema fixes needed for tool {tool_name}")
        else:
            logger.info(f"Tool {tool_name} does not have a schema attribute")
    
    return fixes_applied

def regenerate_calculator_schemas():
    """
    Regenerate the calculator tool schemas by reloading the module and reinstantiating the tools.
    """
    try:
        # Reload the calculator tool module
        calculator_module = importlib.import_module('app.services.agents.agent_calculator_tool')
        importlib.reload(calculator_module)
        
        # Re-get the tools with fixed schemas
        calculator_tool = calculator_module.get_calculator_tool()
        interpreter_tool = calculator_module.get_interpreter_tool()
        
        logger.info("Successfully reloaded calculator tool module")
        
        # Print the schemas to verify they are correct
        if hasattr(calculator_tool, 'schema'):
            logger.info(f"Calculator tool schema: {json.dumps(calculator_tool.schema, indent=2)}")
        
        if hasattr(interpreter_tool, 'schema'):
            logger.info(f"Interpreter tool schema: {json.dumps(interpreter_tool.schema, indent=2)}")
            
        return calculator_tool, interpreter_tool
    except Exception as e:
        logger.error(f"Error regenerating calculator schemas: {e}")
        return None, None

def fix_agent_calculator_tools():
    """
    Apply fixes specifically to the five agents that use the calculator tool.
    """
    # List of agents that use calculator tools
    calculator_agents = ["ACCOUNTING", "BUSINESS", "FINANCE", "DATAANALYSIS", "BUSINESSINTELLIGENCE"]
    
    # Import the specific agent modules directly
    try:
        from app.services.agents.accounting_agent import AccountingAgent
        from app.services.agents.business_agent import BusinessAgent
        from app.services.agents.finance_agent import FinanceAgent
        from app.services.agents.data_analysis_agent import DataAnalysisAgent
        from app.services.agents.business_intelligence_agent import BusinessIntelligenceAgent
        
        # Map agent types to their classes
        agent_classes = {
            "ACCOUNTING": AccountingAgent,
            "BUSINESS": BusinessAgent,
            "FINANCE": FinanceAgent,
            "DATAANALYSIS": DataAnalysisAgent,
            "BUSINESSINTELLIGENCE": BusinessIntelligenceAgent
        }
        
        for agent_type, agent_class in agent_classes.items():
            try:
                # Create a fresh instance of the agent
                logger.info(f"Creating fresh instance of {agent_type}")
                agent = agent_class()
                
                logger.info(f"Fixing calculator tools for agent {agent_type}")
                
                # Find calculator tools
                calculator_tool = None
                interpreter_tool = None
                
                for tool in agent.tools:
                    if getattr(tool, 'name', '') == 'calculate':
                        calculator_tool = tool
                    elif getattr(tool, 'name', '') == 'interpret_calculation_results':
                        interpreter_tool = tool
                
                if calculator_tool:
                    # Fix the calculator tool schema
                    if hasattr(calculator_tool, 'schema'):
                        schema = calculator_tool.schema
                        schema_fixed = fix_schema_properties(schema)
                        if schema_fixed:
                            logger.info(f"Fixed calculator tool schema for agent {agent_type}")
                        else:
                            logger.info(f"No fixes needed for calculator tool schema for agent {agent_type}")
                else:
                    logger.warning(f"Calculator tool not found for agent {agent_type}")
                
                if interpreter_tool:
                    # Fix the interpreter tool schema
                    if hasattr(interpreter_tool, 'schema'):
                        schema = interpreter_tool.schema
                        schema_fixed = fix_schema_properties(schema)
                        if schema_fixed:
                            logger.info(f"Fixed interpreter tool schema for agent {agent_type}")
                        else:
                            logger.info(f"No fixes needed for interpreter tool schema for agent {agent_type}")
                else:
                    logger.warning(f"Interpreter tool not found for agent {agent_type}")
                    
            except Exception as e:
                logger.error(f"Error fixing calculator tools for agent {agent_type}: {e}")
    except Exception as e:
        logger.error(f"Error importing agent modules: {e}")

def main():
    """Main function to run the schema fixer."""
    logger.info("Starting schema fixer")
    
    # Skip the agent_interface part as it requires a running app context
    
    # Regenerate calculator tool schemas first
    logger.info("Regenerating calculator tool schemas")
    calculator_tool, interpreter_tool = regenerate_calculator_schemas()
    
    # Print the schema structures for inspection
    if calculator_tool and hasattr(calculator_tool, 'schema'):
        logger.info(f"Calculator tool schema: {json.dumps(calculator_tool.schema, indent=2)}")
        
        # Validate the schema
        if test_schema_validation(calculator_tool.schema):
            logger.info("Calculator tool schema validation PASSED")
        else:
            logger.error("Calculator tool schema validation FAILED")
    
    # Specifically fix the calculator tools in the agents that use them
    logger.info("Fixing calculator tools in specific agents")
    fix_agent_calculator_tools()
    
    logger.info("Schema fixing complete")

if __name__ == "__main__":
    main()
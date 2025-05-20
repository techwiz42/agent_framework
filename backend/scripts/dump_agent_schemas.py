#!/usr/bin/env python
"""
This script dumps the schemas for all tools in all agents with detailed debug information.
"""

import sys
import json
from pathlib import Path
import argparse
import logging
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
from app.services.agents.base_agent import BaseAgent

def find_all_agent_classes():
    """Find all agent classes in the app/services/agents directory."""
    import importlib
    import pkgutil
    import inspect
    import os
    
    agent_classes = {}
    
    # Import the agents package
    from app.services.agents import base_agent
    from app.services.agents.base_agent import BaseAgent
    from agents import Agent
    agents_package = importlib.import_module("app.services.agents")
    
    # Get the directory path
    package_path = os.path.dirname(agents_package.__file__)
    
    # Find all modules in the package
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        # Skip __init__ and other non-agent modules
        if module_name in ["__init__", "__pycache__"] or not module_name.endswith("_agent"):
            continue
            
        try:
            # Import the module
            module = importlib.import_module(f"app.services.agents.{module_name}")
            
            # Find all classes in the module that inherit from BaseAgent or Agent
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    ((issubclass(obj, BaseAgent) and obj != BaseAgent) or 
                     (issubclass(obj, Agent) and obj != Agent)) and
                    name.endswith("Agent")):
                    agent_classes[name] = obj
                    
        except Exception as e:
            logger.error(f"Error processing module {module_name}: {e}")
    
    return agent_classes

def inspect_agent_tool(tool, verbose=False):
    """Inspect a tool in detail."""
    
    # Get basic information
    tool_name = getattr(tool, "name", "unknown")
    tool_type = type(tool).__name__
    
    # Print basic info
    print(f"\nInspecting tool: {tool_name} (Type: {tool_type})")
    
    # Examine the tool's attributes
    all_attributes = dir(tool)
    interesting_attrs = [attr for attr in all_attributes if not attr.startswith("__")]
    
    # Public schema
    if hasattr(tool, "schema"):
        print(f"  Public schema exists: {bool(tool.schema)}")
        if tool.schema:
            print(f"  Schema type: {type(tool.schema)}")
            if verbose:
                print(f"  Schema content:\n{json.dumps(tool.schema, indent=2)}")
            else:
                # Print essential schema parts
                if isinstance(tool.schema, dict):
                    if "parameters" in tool.schema:
                        params = tool.schema["parameters"]
                        if "properties" in params:
                            props = params["properties"]
                            print(f"  Properties: {list(props.keys())}")
                        if "required" in params:
                            req = params["required"]
                            print(f"  Required: {req}")
                            
                            # Check for mismatches
                            if "properties" in params and isinstance(params["properties"], dict):
                                props = params["properties"].keys()
                                missing = [r for r in req if r not in props]
                                extra = [p for p in props if p not in req]
                                
                                if missing:
                                    print(f"  ⚠️ Required has items not in properties: {missing}")
                                if extra:
                                    print(f"  ⚠️ Properties has items not in required: {extra}")
    else:
        print("  ❌ No public schema attribute!")
    
    # Internal schema
    if hasattr(tool, "_schema"):
        print(f"  Internal _schema exists: {bool(tool._schema)}")
        if tool._schema:
            print(f"  _schema type: {type(tool._schema)}")
            if verbose:
                print(f"  _schema content:\n{json.dumps(tool._schema, indent=2)}")
            else:
                # Print essential schema parts
                if isinstance(tool._schema, dict):
                    if "parameters" in tool._schema:
                        params = tool._schema["parameters"]
                        if "properties" in params:
                            props = params["properties"]
                            print(f"  _schema properties: {list(props.keys())}")
                        if "required" in params:
                            req = params["required"]
                            print(f"  _schema required: {req}")
                            
                            # Check for mismatches
                            if "properties" in params and isinstance(params["properties"], dict):
                                props = params["properties"].keys()
                                missing = [r for r in req if r not in props]
                                extra = [p for p in props if p not in req]
                                
                                if missing:
                                    print(f"  ⚠️ _schema required has items not in properties: {missing}")
                                if extra:
                                    print(f"  ⚠️ _schema properties has items not in required: {extra}")
    else:
        print("  ❌ No internal _schema attribute!")
    
    # Function details if it's a function tool
    if hasattr(tool, "function"):
        func = tool.function
        print(f"  Has function: {bool(func)}")
        if func:
            print(f"  Function name: {func.__name__ if hasattr(func, '__name__') else 'unknown'}")
            
            # Check function signature
            try:
                sig = inspect.signature(func)
                print(f"  Function parameters: {list(sig.parameters.keys())}")
                
                # Compare with schema
                if hasattr(tool, "schema") and tool.schema:
                    schema = tool.schema
                    if "parameters" in schema and "properties" in schema["parameters"]:
                        schema_props = list(schema["parameters"]["properties"].keys())
                        func_params = [p for p in sig.parameters.keys() if p != "self"]
                        
                        missing_in_schema = [p for p in func_params if p not in schema_props]
                        extra_in_schema = [p for p in schema_props if p not in func_params]
                        
                        if missing_in_schema:
                            print(f"  ⚠️ Function params not in schema: {missing_in_schema}")
                        if extra_in_schema:
                            print(f"  ⚠️ Schema props not in function: {extra_in_schema}")
            except Exception as e:
                print(f"  ❌ Error inspecting function: {e}")
    
    # Check for wrapped function
    if hasattr(tool, "__wrapped__"):
        print("  Has __wrapped__ function")
        wrapped = tool.__wrapped__
        print(f"  Wrapped function name: {wrapped.__name__ if hasattr(wrapped, '__name__') else 'unknown'}")
    
    # Check for metadata hints about why schema might be missing
    if not hasattr(tool, "schema") or not tool.schema:
        # Check other attributes that might hold schema info
        schema_related_attrs = [attr for attr in interesting_attrs if "schema" in attr.lower()]
        print(f"  Schema-related attributes: {schema_related_attrs}")

def dump_agent_schemas(agent_class, verbose=False):
    """Dump the schemas for all tools in an agent."""
    print(f"\n{'='*50}")
    print(f"Agent: {agent_class.__name__}")
    print(f"{'='*50}")
    
    try:
        # Create an instance of the agent
        agent = agent_class()
        
        # Get all tools
        if not hasattr(agent, "tools"):
            print("❌ Agent has no tools attribute.")
            return
            
        tools = agent.tools
        print(f"Found {len(tools)} tools")
        
        # Inspect each tool
        for i, tool in enumerate(tools):
            inspect_agent_tool(tool, verbose)
                
    except Exception as e:
        print(f"❌ Error dumping schemas for {agent_class.__name__}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Dump agent function schemas")
    parser.add_argument("--agent", help="Dump schemas for a specific agent class")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full schemas")
    
    args = parser.parse_args()
    
    # Find all agent classes
    agent_classes = find_all_agent_classes()
    print(f"Found {len(agent_classes)} agent classes")
    
    # Filter by agent name if provided
    if args.agent:
        if args.agent not in agent_classes:
            print(f"Agent class {args.agent} not found")
            return 1
        
        agent_classes = {args.agent: agent_classes[args.agent]}
    
    # Dump schemas for each agent class
    for _, cls in agent_classes.items():
        dump_agent_schemas(cls, args.verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
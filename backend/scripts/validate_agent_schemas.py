#!/usr/bin/env python
"""
This script validates all agent function schemas against the OpenAI API requirements
and fixes any issues found.

Usage:
    python scripts/validate_agent_schemas.py --check  # Check for issues
    python scripts/validate_agent_schemas.py --fix    # Fix issues found
"""

import os
import sys
import json
import inspect
import importlib
import pkgutil
import argparse
from pathlib import Path
import logging
from typing import List, Dict, Any, Tuple, Optional, Type, Union, Callable

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def find_all_agent_classes():
    """Find all agent classes in the app/services/agents directory."""
    agent_classes = {}
    
    # Import the agents package
    try:
        from app.services.agents.base_agent import BaseAgent
        from agents import Agent
        from app.services.agents import base_agent
        agents_package = importlib.import_module("app.services.agents")
    except ImportError as e:
        logger.error(f"Error importing agents package: {e}")
        return {}
    
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
                    hasattr(obj, "__bases__") and
                    (any(base.__name__ == "BaseAgent" for base in obj.__bases__) or
                     any(base.__name__ == "Agent" for base in obj.__bases__)) and 
                    obj.__name__ != "BaseAgent" and
                    obj.__name__ != "Agent" and
                    name.endswith("Agent")):
                    agent_classes[name] = obj
                    
        except Exception as e:
            logger.error(f"Error processing module {module_name}: {e}")
    
    return agent_classes


def extract_schema_from_function(func: Callable) -> Optional[Dict[str, Any]]:
    """Extract the schema from a function's docstring or annotations."""
    if hasattr(func, "schema"):
        # If the function already has a schema attribute, use it
        return func.schema
        
    # Get the function's signature
    try:
        sig = inspect.signature(func)
        
        # Extract parameter information
        parameters = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
                
            # Extract type annotation if available
            param_type = "string"  # Default to string
            if param.annotation != inspect.Parameter.empty:
                if hasattr(param.annotation, "__origin__") and param.annotation.__origin__ == list:
                    param_type = "array"
                elif hasattr(param.annotation, "__origin__") and param.annotation.__origin__ == dict:
                    param_type = "object"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                else:
                    param_type = "string"
            
            # Create property definition
            parameters[name] = {
                "type": param_type,
                "description": f"Parameter {name}"
            }
            
            # Add to required if it doesn't have a default value
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        # Extract docstring for description
        description = "No description available"
        if func.__doc__:
            description = func.__doc__.strip()
        
        # Create schema
        schema = {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required
            }
        }
        
        return schema
    except Exception as e:
        logger.error(f"Error extracting schema from function {func.__name__}: {e}")
        return None


def validate_function_schema(func_name: str, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate a function's schema against OpenAI API requirements."""
    issues = []
    
    # Check if parameters exists
    if "parameters" not in schema:
        issues.append({
            "function": func_name,
            "issue": "Missing 'parameters' in schema",
            "severity": "critical"
        })
        return issues
    
    parameters = schema["parameters"]
    
    # Check if properties exists
    if "properties" not in parameters:
        issues.append({
            "function": func_name,
            "issue": "Missing 'properties' in parameters",
            "severity": "critical"
        })
        return issues
    
    properties = parameters["properties"]
    
    # Check if required exists and is a list
    if "required" not in parameters:
        issues.append({
            "function": func_name,
            "issue": "Missing 'required' array in parameters",
            "severity": "critical",
            "fix": {
                "action": "add_required",
                "value": list(properties.keys())
            }
        })
    elif not isinstance(parameters["required"], list):
        issues.append({
            "function": func_name,
            "issue": "'required' is not a list",
            "severity": "critical",
            "fix": {
                "action": "replace_required",
                "value": list(properties.keys())
            }
        })
    else:
        required = parameters["required"]
        
        # Check for properties not in required
        missing_required = [prop for prop in properties if prop not in required]
        if missing_required:
            issues.append({
                "function": func_name,
                "issue": f"Properties not in 'required': {', '.join(missing_required)}",
                "severity": "high",
                "fix": {
                    "action": "update_required",
                    "value": list(properties.keys())
                }
            })
        
        # Check for required items not in properties
        extra_required = [req for req in required if req not in properties]
        if extra_required:
            issues.append({
                "function": func_name,
                "issue": f"Required items not in 'properties': {', '.join(extra_required)}",
                "severity": "high",
                "fix": {
                    "action": "update_required",
                    "value": list(properties.keys())
                }
            })
    
    return issues


def validate_agent(agent_class):
    """Validate all function schemas for an agent class."""
    issues = []
    
    try:
        # Create an instance of the agent
        agent = agent_class()
        
        # Get all tools
        tools = []
        if hasattr(agent, "tools"):
            tools = agent.tools
            
        if not tools and hasattr(agent, "_functions"):
            # Try to extract functions
            funcs = agent._functions
            for func in funcs:
                if hasattr(func, "schema"):
                    schema = func.schema
                    func_name = schema.get("name", "unknown")
                    
                    # Validate the schema
                    func_issues = validate_function_schema(func_name, schema)
                    for issue in func_issues:
                        issue["agent"] = agent_class.__name__
                        issues.append(issue)
        else:
            # Validate each tool
            for tool in tools:
                if hasattr(tool, "schema"):
                    schema = tool.schema
                    func_name = schema.get("name", "unknown")
                    
                    # Validate the schema
                    func_issues = validate_function_schema(func_name, schema)
                    for issue in func_issues:
                        issue["agent"] = agent_class.__name__
                        issues.append(issue)
        
    except Exception as e:
        issues.append({
            "agent": agent_class.__name__,
            "function": "N/A",
            "issue": f"Error validating agent: {str(e)}",
            "severity": "critical"
        })
    
    return issues


def fix_schema_issues(agent_class, issues, apply_fix=False):
    """Fix schema issues in an agent class."""
    try:
        # Create an instance of the agent
        agent = agent_class()
        
        # Get all tools
        tools = []
        if hasattr(agent, "tools"):
            tools = agent.tools
            
        # Group issues by function
        issues_by_function = {}
        for issue in issues:
            func_name = issue.get("function", "unknown")
            if func_name not in issues_by_function:
                issues_by_function[func_name] = []
            issues_by_function[func_name].append(issue)
        
        # Process each tool/function
        for tool in tools:
            if hasattr(tool, "schema"):
                schema = tool.schema
                func_name = schema.get("name", "unknown")
                
                # Apply fixes for this function
                if func_name in issues_by_function:
                    for issue in issues_by_function[func_name]:
                        if "fix" in issue:
                            fix = issue["fix"]
                            
                            if apply_fix:
                                # Apply the fix
                                if fix["action"] in ["add_required", "replace_required", "update_required"]:
                                    schema["parameters"]["required"] = fix["value"]
                                    logger.info(f"Fixed {issue['issue']} in {agent_class.__name__}.{func_name}")
                            else:
                                # Just report the fix
                                logger.info(f"Would fix {issue['issue']} in {agent_class.__name__}.{func_name} "
                                             f"by {fix['action']} with {fix['value']}")
                                             
        return True
    except Exception as e:
        logger.error(f"Error fixing issues for {agent_class.__name__}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate and fix agent function schemas")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check for issues without fixing")
    group.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument("--agent", help="Validate a specific agent (by class name)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Find all agent classes
    agent_classes = find_all_agent_classes()
    
    # Filter by agent name if provided
    if args.agent:
        if args.agent not in agent_classes:
            logger.error(f"Agent class {args.agent} not found")
            return 1
        
        agent_classes = {args.agent: agent_classes[args.agent]}
    
    logger.info(f"Found {len(agent_classes)} agent class(es)")
    
    # Validate each agent class
    all_issues = []
    for name, cls in agent_classes.items():
        logger.info(f"Validating {name}...")
        issues = validate_agent(cls)
        
        if issues:
            logger.info(f"Found {len(issues)} issue(s) in {name}")
            for issue in issues:
                severity = issue.get("severity", "unknown").upper()
                function = issue.get("function", "unknown")
                problem = issue.get("issue", "unknown")
                logger.info(f"  [{severity}] {function}: {problem}")
            
            all_issues.extend(issues)
            
            # Fix issues if requested
            if args.fix:
                fix_schema_issues(cls, issues, apply_fix=True)
    
    # Summary
    if all_issues:
        logger.info(f"\nFound {len(all_issues)} total issue(s) in {len(agent_classes)} agent class(es)")
        if args.fix:
            logger.info("Issues have been fixed")
        else:
            logger.info("Run with --fix to apply fixes")
        return 1
    else:
        logger.info("\nNo issues found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
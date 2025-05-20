#!/usr/bin/env python
"""
This script checks for function parameters with default values that cause OpenAI API validation issues.

Usage:
    python scripts/check_default_params.py
"""

import os
import sys
import re
import importlib
import pkgutil
import logging
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def find_agent_modules():
    """Find all agent modules in the app/services/agents directory."""
    agent_modules = []
    
    try:
        # Import the agents package
        from app.services.agents import base_agent
        agents_package = importlib.import_module("app.services.agents")
        
        # Get the directory path
        package_path = os.path.dirname(agents_package.__file__)
        
        # Find all modules in the package
        for _, module_name, _ in pkgutil.iter_modules([package_path]):
            # Skip __init__ and other non-agent modules
            if module_name in ["__init__", "__pycache__"]:
                continue
                
            module_path = os.path.join(package_path, f"{module_name}.py")
            agent_modules.append(module_path)
    
    except Exception as e:
        logger.error(f"Error finding agent modules: {e}")
    
    return agent_modules

def check_default_params(file_path):
    """Check for string parameters with default values in a file."""
    problems = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find function definitions with parameters that have string default values
        pattern = r'def\s+([\w_]+)\s*\([^)]*([\w_]+)\s*:\s*str\s*=\s*["\'](low|medium|high|enterprise|weekly|daily|critical)["\'][^)]*\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            func_name = match.group(1)
            param_name = match.group(2)
            problems.append((func_name, param_name))
            
    except Exception as e:
        logger.error(f"Error checking {file_path}: {e}")
    
    return problems

def main():
    # Find all agent modules
    agent_modules = find_agent_modules()
    logger.info(f"Found {len(agent_modules)} agent modules")
    
    # Check each module for problems
    all_problems = []
    for module_path in agent_modules:
        module_name = os.path.basename(module_path)
        problems = check_default_params(module_path)
        
        if problems:
            logger.info(f"Found {len(problems)} issues in {module_name}:")
            for func_name, param_name in problems:
                logger.info(f"  Function {func_name} has parameter {param_name} with string default value")
                all_problems.append((module_name, func_name, param_name))
    
    # Summary
    if all_problems:
        logger.info(f"\nFound {len(all_problems)} total issues in {len(agent_modules)} agent modules")
        return 1
    else:
        logger.info("\nNo issues found")
        return 0

if __name__ == "__main__":
    sys.exit(main())
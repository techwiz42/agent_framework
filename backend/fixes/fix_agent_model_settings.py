#!/usr/bin/env python3
"""
This script fixes agent initialization issues by removing explicit model_settings
arguments and replacing them with direct parameters (tool_choice, parallel_tool_calls, max_tokens).

It addresses issues with:
1. Duplicate model_settings parameters (fixed by removing model_settings and using direct parameters)
2. Incorrect formatting/indentation of parameters (fixed by ensuring consistent formatting)
3. Missing RunContextWrapper imports
"""

import os
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the agents directory
AGENTS_DIR = os.path.join("app", "services", "agents")

def fix_agent_files():
    """Main function to fix all agent files."""
    agent_dir = Path(AGENTS_DIR)
    if not agent_dir.exists():
        logger.error(f"Directory {AGENTS_DIR} not found!")
        return
    
    agent_files = list(agent_dir.glob("*.py"))
    if not agent_files:
        logger.error(f"No Python files found in {AGENTS_DIR}")
        return
    
    for file_path in agent_files:
        if "__init__" in file_path.name or "base_agent" in file_path.name:
            logger.info(f"Skipping {file_path}")
            continue
        
        logger.info(f"Processing {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        updated_content = content
        
        # 1. Fix duplicate model_settings parameters
        # Replace model_settings=ModelSettings(...) with direct parameters
        model_settings_pattern = r'model_settings=ModelSettings\(\s*tool_choice=([^,]*?)(?:,\s*parallel_tool_calls=([^,\)]*?))?(?:,\s*max_tokens=([^,\)]*?))?\s*\)'
        
        def model_settings_replacement(match):
            tool_choice = match.group(1).strip()
            parallel_tool_calls = match.group(2).strip() if match.group(2) else 'True'
            max_tokens = match.group(3).strip() if match.group(3) else None
            
            result = f"tool_choice={tool_choice},\n            parallel_tool_calls={parallel_tool_calls}"
            if max_tokens:
                result += f",\n            max_tokens={max_tokens}"
            return result
        
        updated_content = re.sub(model_settings_pattern, model_settings_replacement, updated_content)
        
        # 2. Fix indentation/formatting issues
        # Fix misplaced tool_choice and related parameters
        misplaced_params_pattern = r'(functions=[^,]*?,)\s*\n(\s*)tool_choice='
        updated_content = re.sub(misplaced_params_pattern, r'\1\n            tool_choice=', updated_content)
        
        # Fix missing comma after parallel_tool_calls
        comma_pattern = r'(parallel_tool_calls=[^,\)]*?)(\s*\n\s*\*\*kwargs)'
        updated_content = re.sub(comma_pattern, r'\1,\2', updated_content)
        
        # 3. Add RunContextWrapper import if missing
        if 'RunContextWrapper' in updated_content and 'from agents.run_context import' not in updated_content:
            import_pattern = r'from agents import ([^\n]*)'
            if re.search(import_pattern, updated_content):
                updated_content = re.sub(
                    import_pattern,
                    r'from agents import \1\nfrom agents.run_context import RunContextWrapper',
                    updated_content, 
                    count=1
                )
            else:
                # Add import at the top if no existing imports
                updated_content = f"from agents.run_context import RunContextWrapper\n{updated_content}"
        
        # 4. Fix tools vs functions parameter
        # Some agents use 'tools' instead of 'functions'
        tools_pattern = r'(\s+)tools=([^,]*?),'
        if re.search(tools_pattern, updated_content):
            tools_match = re.search(tools_pattern, updated_content)
            # Only replace if it's in __init__
            init_pattern = r'def __init__[^{]*?{.*?' + re.escape(tools_match.group(0))
            if re.search(init_pattern, updated_content, re.DOTALL):
                updated_content = re.sub(tools_pattern, r'\1functions=\2,', updated_content)
        
        # Write back changes if any were made
        if updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            logger.info(f"Fixed issues in {file_path}")
        else:
            logger.info(f"No issues found in {file_path}")

if __name__ == "__main__":
    fix_agent_files()
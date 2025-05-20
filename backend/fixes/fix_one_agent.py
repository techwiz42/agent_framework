#!/usr/bin/env python3
"""
This script fixes agent initialization issues in a specific agent file.
"""

import re
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_technologist_type_agent(file_path):
    """
    Fix agents that have the comma syntax error and ** error with bool and dict.
    These agents have syntax like:
    
    super().__init__(
        name=name,
        instructions=instructions,
        functions=tools,
    tool_choice=tool_choice, parallel_tool_calls=parallel_tool_calls
        
        **kwargs
    )
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix the incorrect placement of parameters
    pattern = r'super\(\)\.__init__\(\s*(?:[^,]*,\s*)*?([^,]*?)\s*tool_choice=([^,]*?), parallel_tool_calls=([^,\)]*?)(?:, max_tokens=([^,\)]*?))?(?:,\s*\**kwargs)?\s*\)'
    
    # Define replacement based on whether max_tokens exists
    def replacement(match):
        head_params = match.group(1).strip()
        tool_choice = match.group(2).strip()
        parallel_tool_calls = match.group(3).strip()
        max_tokens = match.group(4)
        
        # Build the model_settings dictionary
        if max_tokens:
            model_settings = f"model_settings=ModelSettings(tool_choice={tool_choice}, parallel_tool_calls={parallel_tool_calls}, max_tokens={max_tokens})"
        else:
            model_settings = f"model_settings=ModelSettings(tool_choice={tool_choice}, parallel_tool_calls={parallel_tool_calls})"
        
        # Add kwargs if present in the original
        kwargs_str = ""
        if "**kwargs" in content[match.start():match.end()]:
            kwargs_str = "**kwargs"
        
        # Determine if we need a comma before model_settings
        comma = "" if head_params.endswith(",") or not head_params else ", "
        
        # Build the full replacement
        result = f"super().__init__({head_params}{comma}{model_settings}{', ' + kwargs_str if kwargs_str else ''})"
        return result
    
    # Apply the fix
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write fixed content back
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    return updated_content != content  # Return True if changes were made

def fix_syntax_errors(file_path):
    """Fix syntax errors in agent files."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix comma before line with 'tool_choice='
    pattern1 = r',\s*tool_choice='
    replacement1 = '\n            tool_choice='
    
    # Fix comma before line with 'parallel_tool_calls='
    pattern2 = r',\s*parallel_tool_calls='
    replacement2 = '\n            parallel_tool_calls='
    
    # Fix comma before line with 'model='
    pattern3 = r',\s*model='
    replacement3 = '\n            model='
    
    # Apply fixes
    updated_content = re.sub(pattern1, replacement1, content)
    updated_content = re.sub(pattern2, replacement2, updated_content)
    updated_content = re.sub(pattern3, replacement3, updated_content)
    
    # Write fixed content back
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    return updated_content != content  # Return True if changes were made

def fix_specific_agent(file_path):
    """Fix a specific agent file."""
    logger.info(f"Processing {file_path}...")
    
    # First try to fix syntax errors
    syntax_fixed = fix_syntax_errors(file_path)
    
    # Then try the technologist-type fix
    tech_fixed = fix_technologist_type_agent(file_path)
    
    if syntax_fixed or tech_fixed:
        fixes = []
        if syntax_fixed: fixes.append("syntax errors")
        if tech_fixed: fixes.append("technologist-type errors")
        logger.info(f"Fixed {', '.join(fixes)} in {file_path}")
    else:
        logger.info(f"No issues found in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Please provide the path to the agent file to fix")
        sys.exit(1)
    
    file_path = sys.argv[1]
    fix_specific_agent(file_path)
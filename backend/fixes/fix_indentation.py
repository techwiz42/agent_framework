#!/usr/bin/env python3
"""
This script only fixes the indentation/formatting issues in agent files.
"""

import os
import re
import glob

# Define the agents directory
AGENTS_DIR = os.path.join("app", "services", "agents")

def fix_indentation(file_path):
    """Fix indentation and formatting issues in agent files."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix misaligned tool_choice parameter
    # Pattern: 'function=tools,\ntool_choice=...' -> 'function=tools,\n            tool_choice=...'
    pattern = r'(functions=tools,)\s*\n(\s*)tool_choice='
    replacement = r'\1\n            tool_choice='
    
    updated_content = re.sub(pattern, replacement, content)
    
    # Add missing comma after parallel_tool_calls parameter
    pattern2 = r'(parallel_tool_calls=[^,\)]*?)(\s*\n\s*\*\*kwargs)'
    replacement2 = r'\1,\2'
    
    updated_content = re.sub(pattern2, replacement2, updated_content)
    
    # Wrap each parameter with consistent indentation
    pattern3 = r'tool_choice=([^,]*?), parallel_tool_calls=([^,\)]*?)(?:, max_tokens=([^,\)]*?))?(\s*\n\s*\*\*kwargs)'
    
    def replacement3(match):
        tc = match.group(1)
        ptc = match.group(2)
        mt = match.group(3)
        kwargs = match.group(4)
        
        result = f"tool_choice={tc},\n            parallel_tool_calls={ptc}"
        if mt:
            result += f",\n            max_tokens={mt}"
        result += f",{kwargs}"
        
        return result
    
    updated_content = re.sub(pattern3, replacement3, updated_content)
    
    # Only write if there were changes
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f"Fixed indentation in {file_path}")
        return True
    
    return False

# Get all agent files
agent_files = glob.glob(os.path.join(AGENTS_DIR, "*.py"))
fixed_count = 0

# Fix each file
for file_path in agent_files:
    if fix_indentation(file_path):
        fixed_count += 1

print(f"Fixed {fixed_count} files")
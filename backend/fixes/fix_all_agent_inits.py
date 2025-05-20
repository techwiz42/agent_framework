#!/usr/bin/env python3
"""
This script fixes all agent initialization issues to ensure agents load correctly.
It addresses issues with:
1. Missing commas in super().__init__() calls
2. Duplicate model_settings parameters
3. Misplaced parameters for model settings
"""

import os
import re
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the agents directory
AGENTS_DIR = os.path.join("app", "services", "agents")

def fix_agent_file(file_path):
    """Fix all initialization issues in a single agent file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    updated_content = content
    
    # 1. Fix missing commas in init calls
    pattern_missing_commas = r'(\s*name=.*?[^\s,]\s*)\n(\s*model=)'
    updated_content = re.sub(pattern_missing_commas, r'\1,\n\2', updated_content)
    
    pattern_missing_commas2 = r'(\s*functions=.*?[^\s,]\s*)\n(\s*tool_choice=)'
    updated_content = re.sub(pattern_missing_commas2, r'\1,\n\2', updated_content)
    
    # 2. Fix model_settings parameter
    # First, replace existing model_settings= parameter with direct parameters
    pattern_model_settings = r'model_settings=ModelSettings\(\s*tool_choice=([^,]*?),\s*parallel_tool_calls=([^,\)]*?)(?:,\s*max_tokens=([^,\)]*?))?\s*\)'
    
    def replacement_model_settings(match):
        tool_choice = match.group(1).strip()
        parallel_tool_calls = match.group(2).strip()
        max_tokens = match.group(3)
        
        if max_tokens:
            return f"tool_choice={tool_choice},\n            parallel_tool_calls={parallel_tool_calls},\n            max_tokens={max_tokens}"
        else:
            return f"tool_choice={tool_choice},\n            parallel_tool_calls={parallel_tool_calls}"
    
    updated_content = re.sub(pattern_model_settings, replacement_model_settings, updated_content)
    
    # 3. Fix misplaced or incorrectly formatted parameters
    # Handle the 'tool_choice=XX, parallel_tool_calls=YY' outside the parameter list
    pattern_misplaced = r'super\(\)\.__init__\(\s*(?:[^,]*?,\s*)*?\s*\)(?:\s*,?\s*tool_choice=([^,]*?))?(?:\s*,?\s*parallel_tool_calls=([^,\)]*?))?(?:\s*,?\s*max_tokens=([^,\)]*?))?'
    
    def replacement_misplaced(match):
        init_call = match.group(0).split(')')[0]
        tool_choice = match.group(1)
        parallel_tool_calls = match.group(2)
        max_tokens = match.group(3)
        
        # Only modify if we found misplaced parameters
        if not (tool_choice or parallel_tool_calls or max_tokens):
            return match.group(0)
        
        # Build new parameters
        new_params = []
        if tool_choice:
            new_params.append(f"tool_choice={tool_choice}")
        if parallel_tool_calls:
            new_params.append(f"parallel_tool_calls={parallel_tool_calls}")
        if max_tokens:
            new_params.append(f"max_tokens={max_tokens}")
        
        # Build the replacement
        if init_call.strip().endswith(','):
            return f"{init_call} {', '.join(new_params)})"
        else:
            return f"{init_call}, {', '.join(new_params)})"
    
    updated_content = re.sub(pattern_misplaced, replacement_misplaced, updated_content)
    
    # 4. Fix any remaining syntax errors with commas and extra keywords
    # Fix missing comma before **kwargs
    pattern_kwargs = r'([a-zA-Z0-9_]+=[^,\)]*?)\s*\n\s*\*\*kwargs'
    updated_content = re.sub(pattern_kwargs, r'\1,\n            **kwargs', updated_content)
    
    # Fix RunContextWrapper import if missing
    if 'RunContextWrapper' in updated_content and 'from agents.run_context import' not in updated_content:
        updated_content = updated_content.replace(
            'from agents import Agent',
            'from agents import Agent\nfrom agents.run_context import RunContextWrapper'
        )
    
    # Write updated content back
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return True
    
    return False

def fix_all_agents():
    """Fix initialization issues in all agent files."""
    agent_files = glob.glob(os.path.join(AGENTS_DIR, "*.py"))
    
    fixed_count = 0
    for file_path in agent_files:
        if "__init__" in file_path or "base_agent" in file_path:
            logger.info(f"Skipping {file_path}")
            continue
            
        logger.info(f"Processing {file_path}")
        if fix_agent_file(file_path):
            fixed_count += 1
            logger.info(f"  Fixed issues in {file_path}")
        else:
            logger.info(f"  No issues found in {file_path}")
    
    logger.info(f"Fixed issues in {fixed_count} files")

if __name__ == "__main__":
    fix_all_agents()
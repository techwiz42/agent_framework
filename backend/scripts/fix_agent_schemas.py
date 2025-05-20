#!/usr/bin/env python
"""
This script fixes schema validation issues in agent function parameters by:
1. Removing default values from function parameters
2. Moving default value handling inside function bodies

Run with --check to identify issues without making changes
Run with --fix to automatically fix issues
"""

import ast
import os
import sys
import argparse
import re
from pathlib import Path

def find_agent_files():
    """Find all agent Python files in the app/services/agents directory."""
    agent_dir = Path("app/services/agents")
    if not agent_dir.exists():
        print(f"Directory not found: {agent_dir}")
        return []
    return list(agent_dir.glob("*_agent.py"))

def process_file(file_path, fix_mode):
    """Process a single agent file to check or fix schema issues."""
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False
    
    # Flag to track if we found issues
    issues_found = False
    
    # Track function info for reporting and fixing
    function_issues = []
    
    # Use regex to find function definitions with default values
    # This is simpler than full AST parsing for our specific use case
    class_pattern = r'class\s+(\w+)\s*\(.*?\):'
    function_pattern = r'def\s+(\w+)\s*\(([^)]*)\)'
    
    # Find all classes
    for class_match in re.finditer(class_pattern, content, re.DOTALL):
        class_name = class_match.group(1)
        if not class_name.endswith('Agent'):
            continue
        
        # Find all functions within this class's section
        class_start = class_match.start()
        next_class = re.search(class_pattern, content[class_start + 1:], re.DOTALL)
        class_end = len(content) if next_class is None else class_start + 1 + next_class.start()
        class_content = content[class_start:class_end]
        
        for func_match in re.finditer(function_pattern, class_content, re.DOTALL):
            func_name = func_match.group(1)
            
            # Skip helper methods and special methods
            if func_name.startswith('_') or func_name in ['__init__', 'clone', 'get_function']:
                continue
                
            func_params = func_match.group(2)
            
            # Look for parameters with default values
            param_issues = []
            param_pattern = r'(\w+)\s*:\s*([^=]+)\s*=\s*([^,\)]+)'
            
            for param_match in re.finditer(param_pattern, func_params):
                param_name = param_match.group(1)
                param_type = param_match.group(2).strip()
                default_value = param_match.group(3).strip()
                
                # Skip self parameter
                if param_name == 'self':
                    continue
                
                issues_found = True
                param_issues.append({
                    'param': param_name,
                    'type': param_type,
                    'default': default_value,
                    'full_match': param_match.group(0)
                })
            
            if param_issues:
                function_issues.append({
                    'function': func_name,
                    'class_name': class_name, 
                    'params': param_issues,
                    'func_start': class_start + func_match.start(),
                    'params_text': func_params
                })
    
    # Report or fix issues
    if issues_found:
        if not fix_mode:
            print(f"Issues found in {file_path}:")
            for issue in function_issues:
                print(f"  Function '{issue['function']}' in class {issue['class_name']}:")
                for param in issue['params']:
                    print(f"    - Parameter '{param['param']}' has default value: {param['default']}")
        else:
            # Fix the issues by modifying the content
            fixed_content = fix_param_defaults(content, function_issues)
            
            # Write the updated content
            with open(file_path, 'w') as f:
                f.write(fixed_content)
            
            print(f"✅ Fixed {sum(len(issue['params']) for issue in function_issues)} parameter defaults in {file_path}")
            
        return True  # Issues found
    else:
        print(f"No issues found in {file_path}")
        return False  # No issues

def fix_param_defaults(content, function_issues):
    """
    Fix parameter defaults by:
    1. Removing default values from function signatures
    2. Adding None handling inside the function body
    """
    # Sort issues by position in descending order to avoid offset issues
    function_issues.sort(key=lambda x: x['func_start'], reverse=True)
    
    # Make a copy of the content to modify
    fixed_content = content
    
    for func_issue in function_issues:
        # 1. Fix the function signature by removing default values
        for param in func_issue['params']:
            # Replace "param: type = default" with "param: Optional[type] = None"
            old_param = param['full_match']
            param_name = param['param']
            param_type = param['type'].strip()
            
            # Handle different type annotations
            if param_type.startswith('Optional['):
                new_param = f"{param_name}: {param_type}"
            elif param_type.startswith('List') or param_type.startswith('Dict'):
                new_param = f"{param_name}: Optional[{param_type}]"
            else:
                new_param = f"{param_name}: Optional[{param_type}]"
            
            fixed_content = fixed_content.replace(old_param, new_param)
        
        # 2. Add default value handling inside the function body
        func_match = re.search(
            rf'def\s+{func_issue["function"]}\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:', 
            fixed_content
        )
        
        if not func_match:
            continue
            
        # Find the beginning of the function body
        func_end = func_match.end()
        body_start = fixed_content.find(':', func_end - 10) + 1
        
        # Skip past docstring if present
        docstring_match = re.search(r'^\s*"""', fixed_content[body_start:], re.MULTILINE)
        if docstring_match:
            docstring_start = body_start + docstring_match.start()
            docstring_end = fixed_content.find('"""', docstring_start + 3)
            if docstring_end > 0:
                body_start = docstring_end + 3
        
        # Determine indentation
        next_line_match = re.search(r'^\s+', fixed_content[body_start:], re.MULTILINE)
        if next_line_match:
            indent = next_line_match.group(0)
        else:
            indent = "    "  # Default to 4 spaces if we can't determine
        
        # Check if there's already a "Handle defaults" section
        handle_defaults_exists = "# Handle defaults" in fixed_content[body_start:body_start+500]
        
        # Create default handling code
        default_lines = []
        if not handle_defaults_exists:
            default_lines.append(f"\n{indent}# Handle defaults inside the function")
        
        for param in func_issue['params']:
            param_name = param['param']
            default_value = param['default']
            default_lines.append(f"{indent}if {param_name} is None:")
            default_lines.append(f"{indent}    {param_name} = {default_value}")
        
        # Insert the default handling code at the beginning of the function body
        if default_lines:
            fixed_content = (
                fixed_content[:body_start] + 
                "".join(default_lines) + 
                (fixed_content[body_start:] if handle_defaults_exists else "\n" + fixed_content[body_start:])
            )
    
    # Add Optional import if needed
    if "Optional[" in fixed_content and "Optional" not in fixed_content.split("\n")[0]:
        if "from typing import" in fixed_content:
            fixed_content = re.sub(
                r'from typing import (.*)', 
                r'from typing import \1, Optional', 
                fixed_content
            )
        else:
            fixed_content = "from typing import Optional\n" + fixed_content
    
    return fixed_content

def main():
    parser = argparse.ArgumentParser(description="Fix agent schema issues")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check for issues without making changes")
    group.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument("--file", help="Process a specific file instead of all agent files")
    
    args = parser.parse_args()
    fix_mode = args.fix
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            return 1
        agent_files = [Path(args.file)]
    else:
        agent_files = find_agent_files()
        if not agent_files:
            print("No agent files found.")
            return 1
    
    print(f"Found {len(agent_files)} agent file(s) to process.")
    
    issues_found = False
    for file_path in agent_files:
        file_has_issues = process_file(file_path, fix_mode)
        issues_found = issues_found or file_has_issues
    
    if issues_found:
        if fix_mode:
            print("\nAll issues have been fixed!")
            return 0
        else:
            print("\nIssues found. Run with --fix to automatically fix them.")
            return 1
    else:
        print("\nNo issues found in any files.")
        return 0

if __name__ == "__main__":
    sys.exit(main())

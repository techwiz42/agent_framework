#!/usr/bin/env python3
"""
Script to fix constructor syntax errors in agent files.
"""
import os
import re
import sys

def fix_file(file_path):
    """Fix constructor syntax in a single file."""
    file_name = os.path.basename(file_path)
    print(f"Processing {file_name}...")
    
    try:
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the constructor pattern
        constructor_pattern = r'super\(\).__init__\((.*?)\s*@property'
        constructor_match = re.search(constructor_pattern, content, re.DOTALL)
        
        if not constructor_match:
            print(f"  No constructor found in {file_name}")
            return False
        
        # Extract constructor code
        constructor_code = constructor_match.group(1)
        
        # Check if it's missing a closing parenthesis
        if constructor_code.count('(') > constructor_code.count(')'):
            # Fix the constructor by adding the missing closing parenthesis
            fixed_constructor = constructor_code.rstrip() + ')\n\n'
            
            # Replace in the content
            fixed_content = content.replace(constructor_code, fixed_constructor)
            
            # Write back to the file
            with open(file_path, 'w') as f:
                f.write(fixed_content)
            
            print(f"  ✅ Fixed missing closing parenthesis in {file_name}")
            return True
        else:
            print(f"  No syntax error found in {file_name}")
            return False
    
    except Exception as e:
        print(f"  ❌ Error processing {file_name}: {str(e)}")
        return False

def main():
    """Process all agent files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Get all agent files
    agent_files = [
        os.path.join(agents_dir, f) for f in os.listdir(agents_dir)
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    fixed_count = 0
    skipped_count = 0
    
    for file_path in agent_files:
        if fix_file(file_path):
            fixed_count += 1
        else:
            skipped_count += 1
    
    print(f"\nFixed {fixed_count} files, skipped {skipped_count} files")

if __name__ == "__main__":
    sys.exit(main())
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
        
        # Look for syntax error signature - super().__init__ that's not properly closed
        init_match = re.search(r'super\(\).__init__\s*\(([^)]*?)(?:\s*@|\s*def|\s*$)', content, re.DOTALL)
        if not init_match:
            print(f"  No constructor issues found in {file_name}")
            return False
        
        # Get the arguments inside super().__init__
        init_args = init_match.group(1)
        
        # Count opening and closing parentheses to check if balanced
        open_parens = init_args.count('(')
        close_parens = init_args.count(')')
        
        if open_parens == close_parens:
            # Check if the constructor is properly closed with a closing parenthesis
            next_char = content[init_match.end():].lstrip()
            if next_char.startswith(')'):
                print(f"  Constructor already properly closed in {file_name}")
                return False
        
        # Fix by adding a closing parenthesis and proper formatting
        # First isolate the entire constructor call
        full_init = content[init_match.start():init_match.end()]
        
        # Clean up any trailing commas and add proper closing
        if 'model_settings=' in full_init:
            # We need to replace model_settings with individual parameters
            new_init = re.sub(
                r'model_settings\s*=\s*ModelSettings\s*\((.*?)\)',
                lambda m: m.group(1),
                full_init
            )
        else:
            new_init = full_init
        
        # Replace any trailing commas with a proper closing
        new_init = re.sub(r',\s*$', '', new_init)
        
        # Add closing parenthesis
        new_init = new_init.rstrip() + '\n        )'
        
        # Replace in the original content
        new_content = content.replace(full_init, new_init)
        
        # Write back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"  ✅ Fixed constructor in {file_name}")
        return True
    
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
        try:
            # Verify if the file has syntax errors by trying to compile it
            compile_result = os.system(f"python3 -m py_compile {file_path} > /dev/null 2>&1")
            if compile_result == 0:
                print(f"  File compiles correctly: {os.path.basename(file_path)}")
                skipped_count += 1
                continue
            
            # Try to fix the file
            if fix_file(file_path):
                fixed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  ❌ Error processing {os.path.basename(file_path)}: {str(e)}")
            skipped_count += 1
    
    print(f"\nFixed {fixed_count} files, skipped {skipped_count} files")

if __name__ == "__main__":
    sys.exit(main())
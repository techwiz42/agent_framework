#!/usr/bin/env python3
"""
Script to fix agent inheritance in the codebase.
Modifies all agent classes to inherit from BaseAgent instead of Agent.
"""
import os
import re
import sys

def fix_file(file_path):
    """Fix a single agent file to inherit from BaseAgent."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if BaseAgent is already imported
    base_agent_import = re.search(r'from\s+app\.services\.agents\.base_agent\s+import\s+BaseAgent', content)
    
    # Pattern to match class definition that inherits from Agent
    class_pattern = r'class\s+(\w+Agent)\(Agent(\[[^\]]*\])?\):'
    
    # Find class that inherits from Agent
    agent_class_match = re.search(class_pattern, content)
    if not agent_class_match:
        print(f"No Agent class found in {file_path}")
        return False
    
    # Add BaseAgent import if missing
    if not base_agent_import:
        # Find where to add the import
        import_section_match = re.search(r'(from\s+[^\n]+\n)+', content)
        if import_section_match:
            import_end = import_section_match.end()
            content = (content[:import_end] + 
                      "from app.services.agents.base_agent import BaseAgent\n" + 
                      content[import_end:])
        else:
            print(f"Could not find import section in {file_path}")
            return False
    
    # Replace Agent inheritance with BaseAgent
    if agent_class_match.group(2):  # Has generic type parameter
        content = re.sub(class_pattern, 
                         r'class \1(BaseAgent\2):', 
                         content)
    else:
        content = re.sub(class_pattern, 
                         r'class \1(BaseAgent):', 
                         content)
    
    # Write changes back to file
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Find and fix all agent files in the project."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    fixed_files = []
    failed_files = []
    
    # Get all agent files
    agent_files = [os.path.join(agents_dir, f) for f in os.listdir(agents_dir) 
                   if f.endswith('_agent.py') and f != 'base_agent.py']
    
    for file_path in agent_files:
        print(f"Processing {os.path.basename(file_path)}...")
        if fix_file(file_path):
            fixed_files.append(os.path.basename(file_path))
        else:
            failed_files.append(os.path.basename(file_path))
    
    # Print results
    print(f"\nFixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")
    
    if failed_files:
        print(f"\nFailed to fix {len(failed_files)} files:")
        for file in failed_files:
            print(f"  - {file}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
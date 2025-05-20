#!/usr/bin/env python3
"""
Script to fix all agent classes to properly inherit from BaseAgent and
modify their constructors to avoid parameter conflicts.
"""
import os
import re
import sys

def fix_agent_file(file_path):
    """Fix an agent file to properly inherit from BaseAgent and fix constructor."""
    print(f"Processing {os.path.basename(file_path)}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip files that are already fixed or don't need fixing
    if 'init_context' in content and 'BaseAgent' in content and 'model_settings=' not in content:
        print(f"  File appears to be already fixed. Skipping.")
        return False
    
    # 1. Add BaseAgent import if missing
    if 'from app.services.agents.base_agent import BaseAgent' not in content:
        if 'from app.core.config import settings' in content:
            content = content.replace(
                'from app.core.config import settings',
                'from app.core.config import settings\nfrom app.services.agents.base_agent import BaseAgent'
            )
        else:
            # Find import section and add import at the end
            import_section = re.search(r'^(from|import).*?\n\n', content, re.DOTALL | re.MULTILINE)
            if import_section:
                end_pos = import_section.end() - 1
                content = content[:end_pos] + 'from app.services.agents.base_agent import BaseAgent\n\n' + content[end_pos:]
            else:
                # Fallback - add at the beginning
                content = 'from app.services.agents.base_agent import BaseAgent\n' + content
    
    # 2. Change inheritance from Agent to BaseAgent
    content = re.sub(
        r'class\s+(\w+Agent)\(Agent(\[[^\]]*\])?\):',
        r'class \1(BaseAgent\2):',
        content
    )
    
    # 3. Fix constructor by modifying super().__init__ calls
    # Look for pattern: model_settings=ModelSettings(...) and extract the parameters
    constructor_pattern = r'super\(\).__init__\((.*?)model_settings\s*=\s*ModelSettings\s*\((.*?)\)(.*?)\)'
    
    # Define a function to replace the constructor pattern
    def fix_constructor(match):
        prefix = match.group(1)  # Everything before model_settings
        settings_params = match.group(2)  # Parameters inside ModelSettings
        suffix = match.group(3)  # Everything after model_settings
        
        # Extract key parameters from ModelSettings
        tool_choice_match = re.search(r'tool_choice\s*=\s*([^,\)]+)', settings_params)
        parallel_tool_calls_match = re.search(r'parallel_tool_calls\s*=\s*([^,\)]+)', settings_params)
        max_tokens_match = re.search(r'max_tokens\s*=\s*([^,\)]+)', settings_params)
        temperature_match = re.search(r'temperature\s*=\s*([^,\)]+)', settings_params)
        
        # Check for 'tools=' pattern and replace with 'functions='
        if 'tools=' in prefix:
            prefix = prefix.replace('tools=', 'functions=')
        
        # Build the new parameter list
        new_params = []
        if tool_choice_match:
            new_params.append(f"tool_choice={tool_choice_match.group(1)}")
        if parallel_tool_calls_match:
            new_params.append(f"parallel_tool_calls={parallel_tool_calls_match.group(1)}")
        if max_tokens_match:
            new_params.append(f"max_tokens={max_tokens_match.group(1)}")
        if temperature_match:
            new_params.append(f"temperature={temperature_match.group(1)}")
        
        # Construct the new super().__init__ call
        new_call = f"super().__init__({prefix}"
        
        # Add the extracted parameters
        if new_params:
            if not prefix.strip().endswith(',') and prefix.strip():
                new_call += ", "
            new_call += ", ".join(new_params)
        
        # Add the suffix (after ModelSettings)
        if suffix.strip().startswith(','):
            new_call += suffix
        elif suffix.strip():
            new_call += ", " + suffix.strip()
        else:
            new_call += ")"
        
        return new_call
    
    # Apply the constructor fix
    content = re.sub(constructor_pattern, fix_constructor, content, flags=re.DOTALL)
    
    # 4. Add init_context method if missing
    if 'async def init_context' not in content:
        # Find a good place to add the method - after the last method
        last_method_pos = content.rfind('def ')
        if last_method_pos > 0:
            # Find the end of the method definition
            next_class = content.find('class ', last_method_pos)
            if next_class > 0:
                method_end = content.rfind('\n\n', last_method_pos, next_class)
            else:
                method_end = content.find('\n\n', last_method_pos)
            
            if method_end < 0:  # If not found, use the end of file
                method_end = len(content)
                
            # Add the method
            new_method = '\n\n    async def init_context(self, context: RunContextWrapper[Any]) -> None:\n        """Initialize context for the agent."""\n        # Call parent implementation\n        await super().init_context(context)\n        \n        # Add any agent-specific context initialization here\n        pass\n'
            
            # Insert the method
            content = content[:method_end] + new_method + content[method_end:]
            
            # Add Any import if needed
            if 'from typing import Any' not in content and 'from typing import' in content:
                content = re.sub(
                    r'from typing import (.*?)\n',
                    r'from typing import Any, \1\n',
                    content
                )
            elif 'from typing' not in content:
                import_pos = content.find('import')
                if import_pos >= 0:
                    content = content[:import_pos] + 'from typing import Any\n' + content[import_pos:]
                    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  Fixed successfully!")
    return True

def main():
    """Find and fix all agent files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    fixed_files = []
    skipped_files = []
    
    # Get all agent files
    agent_files = [
        os.path.join(agents_dir, f) for f in os.listdir(agents_dir)
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    for file_path in agent_files:
        if fix_agent_file(file_path):
            fixed_files.append(os.path.basename(file_path))
        else:
            skipped_files.append(os.path.basename(file_path))
    
    # Print results
    print(f"\nFixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")
    
    print(f"\nSkipped {len(skipped_files)} files:")
    for file in skipped_files:
        print(f"  - {file}")

if __name__ == "__main__":
    sys.exit(main())
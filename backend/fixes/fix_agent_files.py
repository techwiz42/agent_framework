#!/usr/bin/env python3
"""
Simpler script to fix agent files by directly editing each one
with targeted file-by-file changes.
"""
import os
import re
import sys

def fix_agent_file(file_path):
    """Fix a specific agent file."""
    file_name = os.path.basename(file_path)
    print(f"Processing {file_name}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Add BaseAgent import if missing
    if "from app.services.agents.base_agent import BaseAgent" not in content:
        content = content.replace(
            "from app.core.config import settings",
            "from app.core.config import settings\nfrom app.services.agents.base_agent import BaseAgent"
        )
    
    # 2. Change Agent inheritance to BaseAgent
    content = re.sub(
        r'class\s+(\w+Agent)\s*\(Agent(\[[^\]]*\])?\):',
        r'class \1(BaseAgent\2):',
        content
    )
    
    # 3. Add Any to typing imports
    if "from typing import" in content and "Any" not in content[:content.find("class")]:
        content = re.sub(
            r'from typing import(.*?)\n',
            r'from typing import Any, \1\n',
            content,
            count=1
        )
    
    # 4. Add init_context method if missing
    if "async def init_context" not in content:
        # Get agent class name
        class_match = re.search(r'class\s+(\w+Agent)', content)
        agent_name = class_match.group(1) if class_match else "Agent"
        
        # Look for @property
        property_pos = content.find("    @property")
        if property_pos > 0:
            # Add before first @property
            init_method = f"""
    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        \"\"\"
        Initialize context for the {agent_name}.
        
        Args:
            context: The context wrapper object with conversation data
        \"\"\"
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for {agent_name}")
        
"""
            content = content[:property_pos] + init_method + content[property_pos:]
        else:
            # Find end of class definition
            class_end = None
            class_start = content.find(f"class {agent_name}")
            if class_start > 0:
                # Look for the next class definition or end of file
                next_class = content.find("class ", class_start + 10)
                if next_class > 0:
                    class_end = next_class
                else:
                    class_end = len(content)
                
                # Add at the end of the class
                init_method = f"""
    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        \"\"\"
        Initialize context for the {agent_name}.
        
        Args:
            context: The context wrapper object with conversation data
        \"\"\"
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for {agent_name}")
"""
                # Add some detection to insert at appropriate position
                last_method_end = content[:class_end].rfind("    def ")
                if last_method_end > 0:
                    # Find end of last method
                    end_pos = -1
                    for match in re.finditer(r'    def [^:]+:[^#]*?(\n\n|\n[^\s]|$)', content[:class_end], re.DOTALL):
                        end_pos = match.end()
                    
                    if end_pos > 0:
                        content = content[:end_pos] + init_method + content[end_pos:]
                    else:
                        # Fallback to adding before the next class
                        content = content[:class_end] + init_method + "\n\n" + content[class_end:]
                else:
                    # Add after class declaration and docstring
                    class_doc_end = content.find('"""', class_start + 10)
                    if class_doc_end > 0:
                        class_doc_end = content.find('"""', class_doc_end + 3) + 3
                        content = content[:class_doc_end] + "\n" + init_method + content[class_doc_end:]
                    else:
                        # Add right after class declaration
                        class_decl_end = content.find(':', class_start) + 1
                        content = content[:class_decl_end] + "\n" + init_method + content[class_decl_end:]
    
    # 5. Fix super().__init__ call if needed
    if "super().__init__" in content and "model_settings=ModelSettings" in content:
        # Replace model_settings with direct parameters
        # Use a simpler approach with regex pattern
        init_pattern = r'super\(\).__init__\((.*?)model_settings\s*=\s*ModelSettings\s*\((.*?)\)(.*?)\)'
        
        def fix_constructor(match):
            prefix = match.group(1)
            model_settings_args = match.group(2)
            suffix = match.group(3)
            
            # Convert tools to functions
            if 'tools=' in prefix:
                prefix = prefix.replace('tools=', 'functions=')
            
            # Extract model_settings parameters
            tool_choice = "None"
            if 'tool_choice=' in model_settings_args:
                tool_choice_match = re.search(r'tool_choice\s*=\s*([^,\)]+)', model_settings_args)
                if tool_choice_match:
                    tool_choice = tool_choice_match.group(1)
            
            parallel_tool_calls = "True"
            if 'parallel_tool_calls=' in model_settings_args:
                parallel_match = re.search(r'parallel_tool_calls\s*=\s*([^,\)]+)', model_settings_args)
                if parallel_match:
                    parallel_tool_calls = parallel_match.group(1)
            
            max_tokens = None
            if 'max_tokens=' in model_settings_args:
                max_tokens_match = re.search(r'max_tokens\s*=\s*([^,\)]+)', model_settings_args)
                if max_tokens_match:
                    max_tokens = max_tokens_match.group(1)
            
            # Construct new init call
            new_init = f"super().__init__({prefix.rstrip(', ')}"
            
            if not prefix.strip().endswith(',') and prefix.strip():
                new_init += ", "
            
            # Add the parameters
            new_init += f"tool_choice={tool_choice}, parallel_tool_calls={parallel_tool_calls}"
            
            if max_tokens:
                new_init += f", max_tokens={max_tokens}"
            
            # Add the suffix if it exists and handle any comma issues
            if suffix.strip():
                if not suffix.strip().startswith(','):
                    new_init += ", "
                new_init += suffix.lstrip(', ')
            else:
                new_init += ")"
            
            # Make sure it ends with a closing parenthesis
            if not new_init.rstrip().endswith(')'):
                new_init += ")"
            
            return new_init
        
        content = re.sub(init_pattern, fix_constructor, content, flags=re.DOTALL)
    
    # Write content back to file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  ✅ Fixed {file_name}")
    return True

def main():
    """Fix all agent files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Get all agent files
    agent_files = [
        os.path.join(agents_dir, f)
        for f in os.listdir(agents_dir)
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    # Skip already fixed agents
    skip_list = ['business_agent.py', 'monitor_agent.py', 'document_search_agent.py']
    agent_files = [f for f in agent_files if os.path.basename(f) not in skip_list]
    
    fixed_count = 0
    
    for file_path in agent_files:
        try:
            if fix_agent_file(file_path):
                fixed_count += 1
        except Exception as e:
            print(f"  ❌ Error fixing {os.path.basename(file_path)}: {str(e)}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    sys.exit(main())
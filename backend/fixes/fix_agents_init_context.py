#!/usr/bin/env python3
"""
Script to fix agent classes by adding BaseAgent inheritance and init_context method.
"""
import os
import re
import sys

def fix_agent_file(file_path):
    """
    Fix an agent file by adding BaseAgent inheritance and init_context method.
    """
    file_name = os.path.basename(file_path)
    print(f"Processing {file_name}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip base_agent.py and already fixed files
    if file_name == "base_agent.py" or "class" not in content:
        print(f"  Skipping {file_name}")
        return False
    
    # Check if it already inherits from BaseAgent
    if "class" in content and "BaseAgent" in content[:content.index("class")]:
        base_agent_inherit = re.search(r'class\s+\w+Agent\s*\(BaseAgent', content)
        if base_agent_inherit:
            print(f"  Already inherits from BaseAgent: {file_name}")
        else:
            # Fix inheritance
            content = re.sub(
                r'class\s+(\w+Agent)\s*\(Agent(\[.*?\])?\)',
                r'class \1(BaseAgent\2)',
                content
            )
            print(f"  Fixed inheritance in {file_name}")
    else:
        # Add BaseAgent import
        if "from app.services.agents.base_agent import BaseAgent" not in content:
            # Find a good place to add the import
            if "from app.core.config import settings" in content:
                content = content.replace(
                    "from app.core.config import settings",
                    "from app.core.config import settings\nfrom app.services.agents.base_agent import BaseAgent"
                )
            else:
                # Default to adding after the last import
                import_section = re.search(r'^(import|from).*?\n\n', content, re.DOTALL | re.MULTILINE)
                if import_section:
                    pos = import_section.end() - 1
                    content = content[:pos] + "from app.services.agents.base_agent import BaseAgent\n" + content[pos:]
                else:
                    # Add at the beginning
                    content = "from app.services.agents.base_agent import BaseAgent\n" + content
            
            print(f"  Added BaseAgent import to {file_name}")
        
        # Fix inheritance
        content = re.sub(
            r'class\s+(\w+Agent)\s*\(Agent(\[.*?\])?\)',
            r'class \1(BaseAgent\2)',
            content
        )
        print(f"  Fixed inheritance in {file_name}")
    
    # Fix constructor if using model_settings
    if "model_settings=ModelSettings" in content:
        # Find all super().__init__ calls
        init_calls = re.finditer(r'super\(\).__init__\((.*?)model_settings\s*=\s*ModelSettings\s*\((.*?)\)(.*?)\)', content, re.DOTALL)
        
        # Apply fixes to each init call found
        for match in init_calls:
            full_init = match.group(0)
            prefix = match.group(1)
            model_settings_args = match.group(2)
            suffix = match.group(3)
            
            # Extract parameters from ModelSettings
            tool_choice_match = re.search(r'tool_choice\s*=\s*([^,\)]+)', model_settings_args)
            tool_choice = tool_choice_match.group(1) if tool_choice_match else "None"
            
            parallel_match = re.search(r'parallel_tool_calls\s*=\s*([^,\)]+)', model_settings_args)
            parallel = parallel_match.group(1) if parallel_match else "True"
            
            max_tokens_match = re.search(r'max_tokens\s*=\s*([^,\)]+)', model_settings_args)
            max_tokens = max_tokens_match.group(1) if max_tokens_match else "None"
            
            # Construct new init call
            new_init = f"super().__init__("
            
            # Add parameters from prefix
            if "tools=" in prefix:
                new_prefix = prefix.replace("tools=", "functions=")
            else:
                new_prefix = prefix
            
            new_init += new_prefix
            
            # If prefix doesn't end with comma, add one
            if new_prefix.strip() and not new_prefix.rstrip().endswith(","):
                new_init += ", "
            
            # Add extracted parameters
            new_init += f"tool_choice={tool_choice}, parallel_tool_calls={parallel}"
            
            if max_tokens != "None":
                new_init += f", max_tokens={max_tokens}"
            
            # Add suffix and closing parenthesis
            if suffix.strip():
                if not suffix.lstrip().startswith(","):
                    new_init += ","
                new_init += suffix
            
            # Ensure proper closing
            if not new_init.rstrip().endswith(")"):
                new_init += ")"
            
            # Replace in content
            content = content.replace(full_init, new_init)
            
            print(f"  Fixed constructor in {file_name}")
    
    # Add init_context method if missing
    if "async def init_context" not in content:
        # Make sure typing imports include Any
        if "from typing import" in content and "Any" not in content[:content.find("class")]:
            content = re.sub(
                r'from typing import(.*?)(?=\n)',
                r'from typing import Any, \1',
                content
            )
        elif "from typing" not in content:
            # Add typing import
            after_imports = re.search(r'^(import|from).*?\n\n', content, re.DOTALL | re.MULTILINE)
            if after_imports:
                pos = after_imports.end() - 1
                content = content[:pos] + "from typing import Any, Dict, Optional, List\n" + content[pos:]
            else:
                # Add at the beginning
                content = "from typing import Any, Dict, Optional, List\n" + content
        
        # Find a good place to add the method - between the last method and the next class/module level item
        # Look for a position right after a method but before another class definition
        last_method_end = None
        for match in re.finditer(r'(\n    def .*?:.*?)(\n\n)', content, re.DOTALL):
            last_method_end = match.end(1)
        
        # If no last method found, look for the first method
        if last_method_end is None:
            match = re.search(r'(class\s+\w+.*?:.*?)(\n\n)', content, re.DOTALL)
            if match:
                last_method_end = match.end(1)
        
        # If still not found, use the class declaration
        if last_method_end is None:
            match = re.search(r'class\s+\w+.*?:', content)
            if match:
                last_method_end = match.end()
                # Skip to the end of the doc string if present
                doc_match = re.search(r'""".*?"""', content[last_method_end:], re.DOTALL)
                if doc_match:
                    last_method_end += doc_match.end()
                    # Add some room for indentation
                    if content[last_method_end:last_method_end+8].strip() == "":
                        last_method_end += 4
        
        # If we found a place to add the method
        if last_method_end:
            # Get agent class name
            class_match = re.search(r'class\s+(\w+Agent)', content)
            agent_name = class_match.group(1) if class_match else "Agent"
            
            # Create the init_context method
            init_context_method = f"""
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
            # Insert the method at the appropriate position
            content = content[:last_method_end] + init_context_method + content[last_method_end:]
            print(f"  Added init_context method to {file_name}")
        else:
            print(f"  Could not find a good place to add init_context method in {file_name}")
    
    # Save changes
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix agent files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Get all agent files except the ones we know are already fixed
    agent_files = [
        os.path.join(agents_dir, f)
        for f in os.listdir(agents_dir)
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    # Sort by size (smaller files first) to minimize issues
    agent_files.sort(key=lambda f: os.path.getsize(f))
    
    fixed_count = 0
    skipped_count = 0
    
    # Process BusinessAgent first as it's our reference
    business_agent_file = os.path.join(agents_dir, 'business_agent.py')
    agent_files.remove(business_agent_file)
    agent_files.insert(0, business_agent_file)
    
    for file_path in agent_files:
        try:
            # Check if the file compiles before attempting to fix
            compile_cmd = f"python3 -m py_compile {file_path} > /dev/null 2>&1"
            if os.system(compile_cmd) == 0:
                print(f"  File already compiles: {os.path.basename(file_path)}")
                skipped_count += 1
                continue
                
            if fix_agent_file(file_path):
                # Verify if the fix worked
                if os.system(compile_cmd) == 0:
                    print(f"  ✅ Successfully fixed {os.path.basename(file_path)}")
                    fixed_count += 1
                else:
                    print(f"  ❌ Fix failed for {os.path.basename(file_path)}")
                    skipped_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing {os.path.basename(file_path)}: {str(e)}")
            skipped_count += 1
    
    print(f"\nFixed {fixed_count} files, skipped {skipped_count} files")

if __name__ == "__main__":
    sys.exit(main())
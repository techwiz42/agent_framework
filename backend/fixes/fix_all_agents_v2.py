#!/usr/bin/env python3
"""
Script to fix all agent classes:
1. Make them inherit from BaseAgent instead of Agent
2. Add the BaseAgent import
3. Ensure they have the init_context method
4. Fix constructor to use BaseAgent parameters
"""
import os
import re
import sys

def fix_agent_file(file_path):
    """Fix an agent file to properly inherit from BaseAgent."""
    file_name = os.path.basename(file_path)
    print(f"Processing {file_name}...")
    
    try:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 1. Add BaseAgent import if missing
        if "from app.services.agents.base_agent import BaseAgent" not in content:
            content = content.replace(
                "from app.core.config import settings",
                "from app.core.config import settings\nfrom app.services.agents.base_agent import BaseAgent"
            )
            print(f"  Added BaseAgent import")
        
        # 2. Change inheritance from Agent to BaseAgent
        content = re.sub(
            r'class\s+(\w+Agent)\s*\(Agent(\[[^\]]*\])?\):',
            r'class \1(BaseAgent\2):',
            content
        )
        print(f"  Fixed inheritance")
        
        # 3. Ensure typing imports include Any
        if "from typing import " in content and "Any" not in content[:content.find("class")]:
            content = re.sub(
                r'from typing import\s+([^A].*?)\n',
                r'from typing import Any, \1\n',
                content
            )
            print(f"  Added Any to typing imports")
        
        # 4. Fix constructor - convert model_settings to individual parameters
        if "model_settings=" in content:
            # Find the super().__init__ call with model_settings
            init_match = re.search(r'super\(\).__init__\((.*?model_settings.*?)\)', content, re.DOTALL)
            if init_match:
                init_call = init_match.group(0)
                init_args = init_match.group(1)
                
                # Extract parameters
                tools_match = re.search(r'tools\s*=([^,]+)', init_args)
                name_match = re.search(r'name\s*=([^,]+)', init_args)
                model_match = re.search(r'model\s*=([^,]+)', init_args)
                instructions_match = re.search(r'instructions\s*=([^,]+)', init_args)
                
                # Extract ModelSettings parameters
                ms_match = re.search(r'model_settings\s*=\s*ModelSettings\s*\((.*?)\)', init_args, re.DOTALL)
                if ms_match:
                    ms_args = ms_match.group(1)
                    tool_choice_match = re.search(r'tool_choice\s*=([^,]+)', ms_args)
                    parallel_match = re.search(r'parallel_tool_calls\s*=([^,]+)', ms_args)
                    max_tokens_match = re.search(r'max_tokens\s*=([^,]+)', ms_args)
                    temperature_match = re.search(r'temperature\s*=([^,]+)', ms_args)
                
                # Build new constructor
                new_init = "super().__init__(\n"
                if name_match:
                    new_init += f"            name={name_match.group(1)},\n"
                if model_match:
                    new_init += f"            model={model_match.group(1)},\n"
                if instructions_match:
                    new_init += f"            instructions={instructions_match.group(1)},\n"
                if tools_match:
                    new_init += f"            functions={tools_match.group(1)},\n"
                
                # Add ModelSettings parameters directly
                if tool_choice_match:
                    new_init += f"            tool_choice={tool_choice_match.group(1)},\n"
                if parallel_match:
                    new_init += f"            parallel_tool_calls={parallel_match.group(1)},\n"
                if max_tokens_match:
                    new_init += f"            max_tokens={max_tokens_match.group(1)},\n"
                if temperature_match:
                    new_init += f"            temperature={temperature_match.group(1)},\n"
                
                # Add **kwargs if present
                if "**kwargs" in init_args:
                    new_init += "            **kwargs\n"
                else:
                    # Remove trailing comma
                    new_init = new_init.rstrip(",\n") + "\n"
                
                # Close the call
                new_init += "        )"
                
                # Replace in the content
                content = content.replace(init_call, new_init)
                print(f"  Fixed constructor call")
        
        # 5. Add init_context method if missing
        if "async def init_context" not in content:
            # Get agent class name
            class_match = re.search(r'class\s+(\w+Agent)', content)
            agent_name = class_match.group(1) if class_match else "Agent"
            
            # Find where to add the method - before the first method definition
            property_pos = content.find("    @property")
            if property_pos > 0:
                # Add before the first @property
                init_context = f"""
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
                content = content[:property_pos] + init_context + content[property_pos:]
            else:
                # Find another position - after __init__
                init_pos = content.find("    def __init__")
                if init_pos > 0:
                    # Find the end of __init__
                    next_method = content.find("    def ", init_pos + 10)
                    if next_method > 0:
                        init_context = f"""
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
                        content = content[:next_method] + init_context + content[next_method:]
            
            print(f"  Added init_context method")
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"  ✅ Successfully fixed {file_name}")
        return True
    
    except Exception as e:
        print(f"  ❌ Error processing {file_name}: {str(e)}")
        return False

def main():
    """Process all agent files to fix issues."""
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
    failed_count = 0
    
    for file_path in agent_files:
        if fix_agent_file(file_path):
            fixed_count += 1
        else:
            failed_count += 1
    
    print(f"\nFixed {fixed_count} files, failed to fix {failed_count} files")

if __name__ == "__main__":
    sys.exit(main())
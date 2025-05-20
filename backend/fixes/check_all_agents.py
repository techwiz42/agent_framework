#!/usr/bin/env python3
"""
Script to check if all agents have the init_context method and inherit from BaseAgent.
"""
import os
import importlib
import inspect
import re
import sys

def check_agent_file(file_path):
    """Check if an agent file has proper BaseAgent inheritance and init_context method."""
    file_name = os.path.basename(file_path)
    module_name = os.path.splitext(file_name)[0]
    full_module_name = f"app.services.agents.{module_name}"
    print(f"Checking {file_name}...")
    
    try:
        # Try to import the module
        module = importlib.import_module(full_module_name)
        
        # Find agent classes
        agent_classes = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Agent') and name not in ('BaseAgent', 'Agent'):
                agent_classes.append((name, obj))
        
        if not agent_classes:
            print(f"  No agent classes found in {file_name}")
            return
        
        # Check each agent class
        for name, cls in agent_classes:
            # Check inheritance
            inherits_base_agent = False
            for base in cls.__mro__:
                if base.__name__ == 'BaseAgent':
                    inherits_base_agent = True
                    break
            
            if not inherits_base_agent:
                print(f"  ❌ {name} does not inherit from BaseAgent")
                continue
            
            # Check init_context method
            if not hasattr(cls, 'init_context'):
                print(f"  ❌ {name} is missing init_context method")
                continue
            
            # Try to instantiate the agent
            try:
                instance = cls()
                if hasattr(instance, 'init_context'):
                    print(f"  ✅ {name} has init_context method and instantiates successfully")
                else:
                    print(f"  ❌ {name} is missing init_context method after instantiation")
            except Exception as e:
                print(f"  ❌ Error instantiating {name}: {str(e)}")
    except Exception as e:
        print(f"  ❌ Error importing {module_name}: {str(e)}")

def main():
    """Check all agent files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Get all agent files
    agent_files = [
        os.path.join(agents_dir, f)
        for f in os.listdir(agents_dir)
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    for file_path in agent_files:
        check_agent_file(file_path)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify that all agents can be initialized properly.
"""
import os
import importlib
import inspect
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_initialization():
    """Test that all agent classes can be initialized properly."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Track results
    success_count = 0
    failure_count = 0
    initialized_agents = []
    failed_agents = []
    
    # Get all agent files
    agent_files = [
        f for f in os.listdir(agents_dir) 
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    print(f"Found {len(agent_files)} agent files to test")
    
    for file_name in agent_files:
        module_name = file_name[:-3]  # Remove .py extension
        full_module_name = f'app.services.agents.{module_name}'
        
        # Import the module
        try:
            print(f"\nTesting {module_name}...")
            module = importlib.import_module(full_module_name)
            
            # Find agent classes
            agent_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith('Agent') and name not in ('BaseAgent', 'Agent'):
                    agent_classes.append((name, obj))
            
            # Test each agent class
            for name, cls in agent_classes:
                try:
                    print(f"  Initializing {name}...")
                    
                    # Check if it inherits from BaseAgent
                    inherits_base = False
                    for base in cls.__mro__:
                        if base.__name__ == 'BaseAgent':
                            inherits_base = True
                            break
                    
                    if not inherits_base:
                        print(f"  ❌ {name} does not inherit from BaseAgent")
                        failed_agents.append((name, "Does not inherit from BaseAgent"))
                        failure_count += 1
                        continue
                    
                    # Check for init_context method
                    if not hasattr(cls, 'init_context'):
                        print(f"  ❌ {name} is missing init_context method")
                        failed_agents.append((name, "Missing init_context method"))
                        failure_count += 1
                        continue
                    
                    # Try to initialize the agent
                    agent = cls()
                    
                    # If we got here, it worked
                    print(f"  ✅ {name} initialized successfully")
                    initialized_agents.append(name)
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error initializing {name}: {str(e)}")
                    failed_agents.append((name, str(e)))
                    failure_count += 1
        
        except Exception as e:
            print(f"❌ Error importing {module_name}: {str(e)}")
            failed_agents.append((module_name, str(e)))
            failure_count += 1
    
    # Print summary
    print("\n=== INITIALIZATION TEST RESULTS ===")
    print(f"Successfully initialized: {success_count} agents")
    print(f"Failed to initialize: {failure_count} agents")
    
    if initialized_agents:
        print("\n✅ Successfully initialized agents:")
        for agent in initialized_agents:
            print(f"  - {agent}")
    
    if failed_agents:
        print("\n❌ Failed agents:")
        for agent, error in failed_agents:
            print(f"  - {agent}: {error}")
    
    return failure_count == 0

if __name__ == "__main__":
    success = test_agent_initialization()
    sys.exit(0 if success else 1)
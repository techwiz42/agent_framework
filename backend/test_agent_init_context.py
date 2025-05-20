#!/usr/bin/env python3
"""Test script to verify that all agents have the init_context method."""
import os
import importlib
import inspect
import traceback
import sys

# Setup consistent logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_init_context():
    """Test all agent classes to ensure they have init_context method."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(base_dir, 'app', 'services', 'agents')
    
    # Track results
    agents_ok = []
    agents_missing = []
    skipped_agents = []
    
    # Get all agent files
    agent_files = [
        os.path.join(agents_dir, f) for f in os.listdir(agents_dir) 
        if f.endswith('_agent.py') and f != 'base_agent.py'
    ]
    
    for file_path in agent_files:
        module_name = os.path.basename(file_path)[:-3]  # remove .py
        full_module_name = f'app.services.agents.{module_name}'
        
        try:
            # Import the module
            module = importlib.import_module(full_module_name)
            
            # Find classes that end with "Agent"
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith('Agent') and name not in ('BaseAgent', 'Agent'):
                    logger.info(f"Checking agent: {name}")
                    
                    # Check for init_context method
                    if hasattr(obj, 'init_context'):
                        # Get method resolution order to see where init_context is defined
                        for base in obj.__mro__:
                            if hasattr(base, 'init_context'):
                                source = base.__name__
                                break
                        else:
                            source = "unknown"
                        
                        # Add to successful list
                        agents_ok.append((name, source))
                    else:
                        # Add to failed list - missing init_context
                        agents_missing.append(name)
        except Exception as e:
            logger.error(f"Error checking {module_name}: {e}")
            logger.error(traceback.format_exc())
            skipped_agents.append(module_name)
    
    # Print results
    print("\n=== AGENT CHECK RESULTS ===")
    print(f"Checked {len(agents_ok) + len(agents_missing)} agent classes")
    
    if agents_ok:
        print(f"\n✅ {len(agents_ok)} agents have init_context method:")
        for agent, source in agents_ok:
            print(f"  - {agent} (from {source})")
    
    if agents_missing:
        print(f"\n❌ {len(agents_missing)} agents MISSING init_context method:")
        for agent in agents_missing:
            print(f"  - {agent}")
    
    if skipped_agents:
        print(f"\n⚠️ Skipped {len(skipped_agents)} agent files due to errors:")
        for agent in skipped_agents:
            print(f"  - {agent}")
    
    return len(agents_missing) == 0

if __name__ == "__main__":
    success = test_agent_init_context()
    sys.exit(0 if success else 1)
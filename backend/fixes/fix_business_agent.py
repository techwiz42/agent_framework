#!/usr/bin/env python3
"""
Script to fix the BusinessAgent class to properly inherit from BaseAgent.
"""
import os

def fix_business_agent():
    """Fix the BusinessAgent class to properly inherit from BaseAgent."""
    # File path
    file_path = os.path.join('app', 'services', 'agents', 'business_agent.py')
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add BaseAgent import if needed
    if 'from app.services.agents.base_agent import BaseAgent' not in content:
        content = content.replace(
            'from app.core.config import settings',
            'from app.core.config import settings\nfrom app.services.agents.base_agent import BaseAgent'
        )
    
    # Change class to inherit from BaseAgent
    content = content.replace(
        'class BusinessAgent(Agent):',
        'class BusinessAgent(BaseAgent):'
    )
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed BusinessAgent in {file_path}")
    
    # Add an init_context method if missing
    if 'async def init_context' not in content:
        # Find a good place to add the method - after the last method
        last_method_pos = content.rfind('def ')
        if last_method_pos > 0:
            # Find the end of the method definition
            method_end = content.find('\n\n', last_method_pos)
            if method_end < 0:  # If not found, use the end of file
                method_end = len(content)
                
            # Add the method
            new_method = '\n\n    async def init_context(self, context):\n        """Initialize context for the agent."""\n        # Call parent implementation\n        await super().init_context(context)\n        \n        # Add any business agent specific context initialization here\n        pass\n'
            
            # Insert the method
            content = content[:method_end] + new_method + content[method_end:]
            
            # Write the updated file
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("Added init_context method to BusinessAgent")

if __name__ == "__main__":
    fix_business_agent()
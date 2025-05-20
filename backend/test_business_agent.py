#!/usr/bin/env python3
"""Test script to check if the BusinessAgent can be instantiated."""
from app.services.agents.business_agent import BusinessAgent

def main():
    """Test BusinessAgent initialization."""
    try:
        # Create an instance of BusinessAgent
        agent = BusinessAgent()
        print("✅ BusinessAgent initialized successfully!")
        
        # Check for init_context method
        if hasattr(agent, 'init_context'):
            print("✅ BusinessAgent has init_context method")
        else:
            print("❌ BusinessAgent is missing init_context method")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing BusinessAgent: {str(e)}")
        return False

if __name__ == "__main__":
    main()
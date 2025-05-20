#!/usr/bin/env python
"""
This script tests the LegalAgent's function tools for schema validation issues.
"""

import sys
import json
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.agents.legal_agent import LegalAgent
from agents.run import Runner

def test_legal_agent():
    """Test the LegalAgent to make sure its schema is valid."""
    print("Creating LegalAgent instance...")
    agent = LegalAgent()
    
    # Print agent tools
    print("\nAgent Tools:")
    for tool in agent.tools:
        print(f"- {tool.name}")
        schema = getattr(tool, "schema", {})
        if "parameters" in schema:
            params = schema["parameters"]
            if "properties" in params:
                properties = params["properties"]
                print(f"  Properties: {', '.join(properties.keys())}")
            if "required" in params:
                required = params["required"]
                print(f"  Required: {', '.join(required)}")
                
                # Check for mismatches
                if "properties" in params:
                    props = params["properties"].keys()
                    missing = [r for r in required if r not in props]
                    extra = [p for p in props if p not in required]
                    if missing:
                        print(f"  ERROR: Required properties not in properties: {', '.join(missing)}")
                    if extra:
                        print(f"  ERROR: Properties not in required: {', '.join(extra)}")
    
    # Test generate_document function specifically
    print("\nTesting generate_document function...")
    generate_doc = next((tool for tool in agent.tools if tool.name == "generate_document"), None)
    
    if generate_doc:
        print("Found generate_document tool")
        schema = getattr(generate_doc, "schema", {})
        
        # Print the full schema for inspection
        print(f"Schema full details:")
        print(json.dumps(schema, indent=2))
        
        # Check if parameters.properties and parameters.required match
        if "parameters" in schema:
            params = schema["parameters"]
            if "properties" in params and "required" in params:
                properties = list(params["properties"].keys())
                required = params["required"]
                print(f"Properties: {properties}")
                print(f"Required: {required}")
                
                # Check for any mismatches
                missing = [r for r in required if r not in properties]
                extra = [p for p in properties if p not in required]
                
                if missing:
                    print(f"ERROR: Required contains items not in properties: {missing}")
                if extra:
                    print(f"ERROR: Properties contains items not in required: {extra}")
                if not missing and not extra:
                    print("PASS: Properties and required match exactly!")
            else:
                print("ERROR: Missing properties or required in parameters")
    else:
        print("ERROR: Could not find generate_document tool")
    
    # Skip the actual run to just check the schema
    print("\nSchema check completed.")

if __name__ == "__main__":
    test_legal_agent()
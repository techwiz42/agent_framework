"""
This script tests the voice endpoint to help diagnose routing issues.
"""

import requests
import sys

def test_voice_endpoint():
    """Test the speech-to-text endpoint"""
    base_url = "http://localhost:8000"  # Adjust if running on different port
    
    # Test voice endpoint
    test_routes = [
        "/api/voice/speech-to-text",  # Current expected route with prefix
        "/voice/speech-to-text",      # Route without API prefix
        "/api/voice/status",          # Status endpoint
    ]
    
    for route in test_routes:
        try:
            resp = requests.get(f"{base_url}{route}")
            print(f"Testing {route}: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Success! Response: {resp.json()}")
            else:
                print(f"Failed with status {resp.status_code}")
        except Exception as e:
            print(f"Error accessing {route}: {str(e)}")
    
    # Print available routes
    try:
        resp = requests.get(f"{base_url}/api/debug/routes")
        if resp.status_code == 200:
            print("\nAvailable routes:")
            for route in resp.json().get("routes", []):
                print(f"{route.get('path')} - {','.join(route.get('methods', []))}")
    except Exception as e:
        print(f"Could not get available routes: {str(e)}")

if __name__ == "__main__":
    test_voice_endpoint()
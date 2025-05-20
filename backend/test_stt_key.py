#!/usr/bin/env python3
"""
Test script to verify that the Google API key works with Speech-to-Text API.
This script creates a simple test audio file with a sine wave and tries to 
transcribe it using the Google Speech-to-Text API.
"""

import os
import base64
import requests
import wave
import numpy as np
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
if os.path.exists('/home/peter/agent_framework/backend/.env'):
    load_dotenv('/home/peter/agent_framework/backend/.env')

# Get API key
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: No Google API key found in environment variables")
    sys.exit(1)

print(f"Found API key: {api_key[:5]}...{api_key[-5:]}")

# Create a simple test audio file
def create_test_audio(filename, duration=1, frequency=440, sample_rate=16000):
    """Create a simple sine wave audio file for testing."""
    # Generate a sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio_data = (32767 * 0.5 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
    
    # Write the audio data to a WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16 bits)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return audio_data

# Create test file
test_file = "test_audio.wav"
create_test_audio(test_file, duration=2)
print(f"Created test audio file: {test_file}")

# Read the audio file
with open(test_file, 'rb') as f:
    audio_content = f.read()

# Encode as base64
audio_base64 = base64.b64encode(audio_content).decode('utf-8')

# Prepare API request
url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
payload = {
    "config": {
        "encoding": "LINEAR16",
        "sampleRateHertz": 16000,
        "languageCode": "en-US",
        "model": "default"
    },
    "audio": {
        "content": audio_base64
    }
}

print("Sending request to Google Speech-to-Text API...")
try:
    # Send request
    response = requests.post(url, json=payload)
    
    # Check response
    if response.status_code == 200:
        print("API request successful!")
        json_response = response.json()
        print("Response:", json_response)
        
        # Check if there are results
        if "results" in json_response and json_response["results"]:
            print("Speech detected!")
            for result in json_response["results"]:
                for alt in result.get("alternatives", []):
                    print(f"Transcript: {alt.get('transcript')}")
                    print(f"Confidence: {alt.get('confidence')}")
        else:
            print("No speech detected in test audio (this is expected for a sine wave)")
            print("The API key and permissions are working correctly!")
    else:
        print(f"API request failed: {response.status_code}")
        print(f"Error details: {response.text}")
        
        # Check for common errors
        if response.status_code == 400:
            print("ERROR: Bad request - check audio format")
        elif response.status_code == 403:
            print("ERROR: Forbidden - API key may not have permission for Speech-to-Text")
        elif response.status_code == 404:
            print("ERROR: Not found - check API endpoint URL")
        
except Exception as e:
    print(f"Exception: {e}")

# Clean up
os.remove(test_file)
print(f"Removed test file: {test_file}")
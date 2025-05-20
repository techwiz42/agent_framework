#!/usr/bin/env python3
"""
Test script for the speech-to-text endpoint.
Creates a test audio file and sends it to the endpoint to verify functionality.
"""

import requests
import os
import wave
import numpy as np
import time
import subprocess
import sys

def create_test_audio(filename, duration=2, sample_rate=16000):
    """Create a test audio file with a synthesized 'hello' sound."""
    # This is just a simplistic approximation - not real speech
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Create a more complex waveform that might trigger speech detection
    # (This is still unlikely to be detected as speech, but it's more complex than a pure sine wave)
    audio_data = np.zeros_like(t)
    
    # Add some frequency components that might resemble speech formants
    for freq in [300, 500, 1000, 2000]:
        audio_data += 0.2 * np.sin(2 * np.pi * freq * t)
    
    # Add some amplitude modulation
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t / duration)
    audio_data = audio_data * envelope
    
    # Normalize and convert to int16
    audio_data = (32767 * 0.9 * audio_data / np.max(np.abs(audio_data))).astype(np.int16)
    
    # Write to WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16 bits)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Created test audio file: {filename}")
    return filename

def record_real_speech(filename, duration=5):
    """Record actual speech using arecord (Linux only)."""
    try:
        print(f"Recording {duration} seconds of speech. Please speak clearly...")
        subprocess.run(
            ["arecord", "-f", "S16_LE", "-c1", "-r16000", "-d", str(duration), filename],
            check=True
        )
        print(f"Recorded speech to {filename}")
        return filename
    except Exception as e:
        print(f"Error recording speech: {e}")
        return None

def test_stt_endpoint(audio_file, url="http://localhost:8001/api/voice/speech-to-text"):
    """Test the speech-to-text endpoint with the given audio file."""
    print(f"Testing STT endpoint: {url}")
    print(f"Using audio file: {audio_file}")
    
    with open(audio_file, 'rb') as f:
        files = {'audio_file': (os.path.basename(audio_file), f, 'audio/wav')}
        data = {'language_code': 'en-US'}
        
        try:
            print("Sending request...")
            response = requests.post(url, files=files, data=data)
            
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("Response JSON:")
                for key, value in result.items():
                    if key == "full_response":
                        print(f"  {key}: [Full response omitted for brevity]")
                    else:
                        print(f"  {key}: {value}")
                
                if result.get("success", False) and result.get("transcript"):
                    print(f"\nSpeech detected! Transcript: '{result['transcript']}'")
                else:
                    print("\nNo speech detected in the audio file.")
                    
                # Debugging suggestions
                if not result.get("success", False) and result.get("error") == "No speech detected":
                    print("\nTroubleshooting suggestions:")
                    print("1. Ensure your microphone is working properly")
                    print("2. Speak clearly and loudly when recording")
                    print("3. Reduce background noise")
                    print("4. Try a longer recording (3-5 seconds)")
                    print("5. Check that your browser has microphone permissions")
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    # Check if port is provided as argument
    port = 8001  # Default port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}. Using default port 8001.")
    
    stt_url = f"http://localhost:{port}/api/voice/speech-to-text"
    
    # First check if the service is available
    try:
        status_response = requests.get(f"http://localhost:{port}/api/voice/speech-to-text/status")
        if status_response.status_code == 200:
            print(f"Speech-to-text service status: {status_response.json()}")
        else:
            print(f"Error checking service status: {status_response.status_code} - {status_response.text}")
    except Exception as e:
        print(f"Failed to connect to speech-to-text service: {e}")
        print(f"Is the server running on port {port}?")
        sys.exit(1)
    
    # First test with synthetic audio
    test_file = "test_speech.wav"
    create_test_audio(test_file)
    test_stt_endpoint(test_file, stt_url)
    
    # Now try to record and test with real speech if available
    print("\n" + "="*50 + "\n")
    try:
        real_speech_file = "real_speech.wav"
        if record_real_speech(real_speech_file):
            print("\nTesting with real recorded speech:")
            test_stt_endpoint(real_speech_file, stt_url)
            os.remove(real_speech_file)
    except Exception as e:
        print(f"Could not record real speech: {e}")
    
    # Clean up
    os.remove(test_file)
    print(f"Removed test file: {test_file}")
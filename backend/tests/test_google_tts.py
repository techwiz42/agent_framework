import os
import pytest
import requests
import tempfile
import json

def test_google_text_to_speech():
    """Test that we can access Google's Text-to-Speech API."""
    # Load API key from env file
    with open('/etc/cyberiad/.env') as f:
        for line in f:
            if 'GOOGLE_API_KEY' in line:
                api_key = line.strip().split('=')[1].strip('"')
                break
    
    # Define the API endpoint
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    # Prepare the request payload
    payload = {
        "input": {
            "text": "Hello, this is a test of the Google Text-to-Speech API"
        },
        "voice": {
            "languageCode": "en-US",
            "ssmlGender": "NEUTRAL"
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }
    
    # Make the API request
    response = requests.post(url, json=payload)
    
    # Check if the request was successful
    assert response.status_code == 200, f"API request failed: {response.text}"
    
    # Parse the response
    response_json = response.json()
    
    # The response contains audio content in base64
    assert "audioContent" in response_json, "No audio content in response"
    
    # Convert base64 to binary
    import base64
    audio_content = base64.b64decode(response_json["audioContent"])
    
    # Write the response to a temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(audio_content)
        temp_path = temp_file.name
    
    # Verify that we got audio data
    assert len(audio_content) > 0, "Audio content is empty"
    
    # Clean up
    os.unlink(temp_path)
import os
import pytest
import tempfile
import base64
import wave
import struct
import numpy as np
from unittest.mock import patch, MagicMock
import io

from app.services.voice.google_stt_service import GoogleSTTService

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
    
    # Return the audio data array
    return audio_data

def test_google_stt_service_init():
    """Test GoogleSTTService initialization."""
    # Test initialization with env var
    with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}):
        service = GoogleSTTService()
        assert service.api_key == 'test_key'
    
    # Test initialization without env var but with .env file
    with patch.dict(os.environ, {}, clear=True):
        # Mock file read for .env
        with patch('builtins.open', MagicMock()):
            with patch('os.path.exists', return_value=True):
                with patch('app.services.voice.google_stt_service.GoogleSTTService._load_api_key', return_value='file_key'):
                    service = GoogleSTTService()
                    assert service.api_key == 'file_key'

@patch('requests.post')
def test_transcribe_audio(mock_post):
    """Test transcribing audio with the Google STT service."""
    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "alternatives": [
                    {
                        "transcript": "hello world",
                        "confidence": 0.95
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_response
    
    # Create test audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        create_test_audio(temp_file.name)
        temp_filename = temp_file.name
    
    try:
        # Read audio file
        with open(temp_filename, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        # Initialize service with a test API key
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}):
            service = GoogleSTTService()
            
            # Test transcription
            result = service.transcribe_audio(audio_content)
            
            # Verify mock was called correctly
            mock_post.assert_called_once()
            assert 'test_key' in mock_post.call_args[0][0]
            
            # Verify result
            assert result['success'] is True
            assert result['transcript'] == 'hello world'
            assert result['confidence'] == 0.95
    
    finally:
        # Clean up
        os.unlink(temp_filename)

@patch('requests.post')
def test_transcribe_audio_error(mock_post):
    """Test error handling in transcribe_audio method."""
    # Create a mock error response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid request"
    mock_post.return_value = mock_response
    
    # Initialize service with a test API key
    with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}):
        service = GoogleSTTService()
        
        # Test with empty audio content
        result = service.transcribe_audio(b'')
        
        # Verify error is handled
        assert result['success'] is False
        assert 'error' in result
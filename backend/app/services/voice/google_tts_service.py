import base64
import logging
import os
import requests
import traceback
import json
from typing import Optional, Dict, Any, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleTTSService:
    """Service for Google Text-to-Speech API integration."""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.base_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        logger.info(f"GoogleTTSService initialized. API key available: {bool(self.api_key)}")
        
        # Define available voices
        self.voices = {
            "en-US-Neural2-A": {"gender": "MALE", "name": "en-US-Neural2-A"},
            "en-US-Neural2-C": {"gender": "FEMALE", "name": "en-US-Neural2-C"},
            "en-US-Neural2-D": {"gender": "MALE", "name": "en-US-Neural2-D"},
            "en-US-Neural2-F": {"gender": "FEMALE", "name": "en-US-Neural2-F"},
            "en-US-Studio-O": {"gender": "FEMALE", "name": "en-US-Studio-O"},
            "en-US-Standard-E": {"gender": "FEMALE", "name": "en-US-Standard-E"},
            "en-GB-Neural2-B": {"gender": "MALE", "name": "en-GB-Neural2-B"},
        }
        
        # Default voice
        self.default_voice = "en-US-Neural2-C"
        
    def _load_api_key(self) -> Optional[str]:
        """Load Google API key from environment."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        logger.info(f"Checking env vars for GOOGLE_API_KEY: {'Found' if api_key else 'Not found'}")
        
        # If not in env vars, try to load from .env file in the project root
        if not api_key and os.path.exists('/home/peter/agent_framework/backend/.env'):
            logger.info("Checking local .env file in project root")
            try:
                with open('/home/peter/agent_framework/backend/.env') as f:
                    for line in f:
                        if 'GOOGLE_API_KEY' in line:
                            api_key = line.strip().split('=')[1].strip('"')
                            logger.info("Found GOOGLE_API_KEY in project root .env file")
                            break
            except Exception as e:
                logger.error(f"Error loading Google API key from project .env file: {e}")
        
        # If not in project root, try to load from /etc/cyberiad/.env
        if not api_key and os.path.exists('/etc/cyberiad/.env'):
            logger.info("Checking /etc/cyberiad/.env file")
            try:
                with open('/etc/cyberiad/.env') as f:
                    for line in f:
                        if 'GOOGLE_API_KEY' in line:
                            api_key = line.strip().split('=')[1].strip('"')
                            logger.info("Found GOOGLE_API_KEY in /etc/cyberiad/.env file")
                            break
            except Exception as e:
                logger.error(f"Error loading Google API key from /etc/cyberiad/.env file: {e}")
        
        if not api_key:
            logger.error("Google API key not found in environment variables or .env files")
            return None
            
        # Mask the API key for logging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.info(f"Google API key successfully loaded: {masked_key}")
        return api_key
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get a list of available voices."""
        return [
            {"id": voice_id, "name": voice_id, "gender": details["gender"]} 
            for voice_id, details in self.voices.items()
        ]
    
    def synthesize_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language_code: str = "en-US",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
        audio_encoding: str = "MP3"
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using Google's Text-to-Speech API.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (from available voices)
            language_code: Language code (default: en-US)
            speaking_rate: Speaking rate/speed, 0.25 to 4.0 (default: 1.0)
            pitch: Voice pitch, -20.0 to 20.0 (default: 0.0)
            volume_gain_db: Volume gain in dB, -96.0 to 16.0 (default: 0.0)
            audio_encoding: Output audio encoding (MP3, LINEAR16, OGG_OPUS, etc.)
            
        Returns:
            Dictionary containing audio data or error
        """
        if not self.api_key:
            logger.error("Cannot synthesize: Google API key not configured")
            return {"success": False, "error": "Google API key not configured"}
        
        # Validate and select voice
        selected_voice = voice_id if voice_id and voice_id in self.voices else self.default_voice
        
        try:
            # Prepare request payload
            payload = {
                "input": {
                    "text": text
                },
                "voice": {
                    "languageCode": language_code,
                    "name": selected_voice
                },
                "audioConfig": {
                    "audioEncoding": audio_encoding,
                    "speakingRate": speaking_rate,
                    "pitch": pitch,
                    "volumeGainDb": volume_gain_db
                }
            }
            
            # Construct API URL with key
            url = f"{self.base_url}?key={self.api_key}"
            
            logger.info(f"Sending TTS request: Text length: {len(text)}, Voice: {selected_voice}")
            logger.debug(f"TTS configuration: {json.dumps(payload, indent=2)}")
            
            try:
                # Make API request
                response = requests.post(url, json=payload)
                
                # Log the response details
                logger.debug(f"Google TTS response code: {response.status_code}")
                
                # Check for successful response
                if response.status_code == 200:
                    response_json = response.json()
                    
                    # Extract audio content
                    if "audioContent" in response_json:
                        audio_content_base64 = response_json["audioContent"]
                        
                        # Decode base64 to get audio bytes
                        audio_bytes = base64.b64decode(audio_content_base64)
                        
                        return {
                            "success": True,
                            "audio": audio_bytes,
                            "encoding": audio_encoding.lower(),
                            "voice_id": selected_voice
                        }
                    else:
                        logger.warning("Google TTS response missing audioContent")
                        return {
                            "success": False,
                            "error": "Missing audio content in response",
                            "details": "The API response did not contain audio content"
                        }
                else:
                    error_message = "Unknown error"
                    try:
                        error_data = response.json()
                        if "error" in error_data and "message" in error_data["error"]:
                            error_message = error_data["error"]["message"]
                    except:
                        error_message = response.text
                        
                    logger.error(f"Google TTS API error: {response.status_code} - {error_message}")
                    return {
                        "success": False,
                        "error": f"API request failed with status {response.status_code}",
                        "details": error_message
                    }
                    
            except Exception as e:
                logger.error(f"Exception in Google TTS API request: {str(e)}")
                stack_trace = traceback.format_exc()
                logger.error(f"Stack trace:\n{stack_trace}")
                
                return {
                    "success": False,
                    "error": f"Exception in API request: {str(e)}",
                    "details": traceback.format_exc()
                }
                
        except Exception as e:
            logger.error(f"Exception in Google TTS service: {str(e)}")
            stack_trace = traceback.format_exc()
            logger.error(f"Stack trace:\n{stack_trace}")
            
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "details": traceback.format_exc()
            }
            
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text to improve TTS quality.
        
        Args:
            text: Original text
            
        Returns:
            Preprocessed text
        """
        # Convert URLs to "link" to avoid reading out long URLs
        import re
        text = re.sub(r'https?://\S+', ' link ', text)
        
        # Add pauses after sentences
        text = re.sub(r'([.!?])\s+', r'\1 <break time="500ms"/> ', text)
        
        # Add SSML markers for pause at commas
        text = re.sub(r',\s+', ', <break time="200ms"/> ', text)
        
        # Add SSML for numbers, dates, etc (if needed)
        
        return text
    
    def get_audio_mime_type(self, encoding: str) -> str:
        """Get the MIME type for an audio encoding."""
        mapping = {
            "mp3": "audio/mpeg",
            "linear16": "audio/wav",
            "ogg_opus": "audio/ogg",
            "mulaw": "audio/basic",
            "alaw": "audio/alaw"
        }
        return mapping.get(encoding.lower(), "audio/mpeg")

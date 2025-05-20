import base64
import logging
import os
import requests
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleSTTService:
    """Service for Google Speech-to-Text API integration."""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.base_url = "https://speech.googleapis.com/v1/speech:recognize"
        
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
            
        logger.info("Google API key successfully loaded")
        return api_key
    
    def transcribe_audio(self, audio_content: bytes, sample_rate_hertz: Optional[int] = 16000, 
                         language_code: str = "en-US", model: str = "default") -> dict:
        """
        Transcribe audio using Google's Speech-to-Text API.
        
        Args:
            audio_content: Raw audio bytes
            sample_rate_hertz: Audio sample rate in Hertz
            language_code: Language of the audio
            model: Model to use (default, command_and_search, phone_call, etc.)
            
        Returns:
            Dictionary containing transcription results or error
        """
        if not self.api_key:
            return {"error": "Google API key not configured"}
        
        # Encode audio content to base64
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Construct API URL with key
        url = f"{self.base_url}?key={self.api_key}"
        
        # Prepare request payload
        config = {
            "encoding": "LINEAR16",
            "languageCode": language_code,
            "model": model
        }
        
        # Only include sampleRateHertz if it's provided
        # This allows Google to auto-detect the rate from the audio header for WEBM files
        if sample_rate_hertz is not None:
            config["sampleRateHertz"] = sample_rate_hertz
            
        payload = {
            "config": config,
            "audio": {
                "content": audio_base64
            }
        }
        
        try:
            # Make API request
            response = requests.post(url, json=payload)
            
            # Check for successful response
            if response.status_code == 200:
                response_json = response.json()
                
                # Extract transcript text if available
                result = {"success": True}
                
                if ("results" in response_json and 
                    response_json["results"] and 
                    response_json["results"][0].get("alternatives") and 
                    response_json["results"][0]["alternatives"][0].get("transcript")):
                    
                    transcript = response_json["results"][0]["alternatives"][0]["transcript"]
                    confidence = response_json["results"][0]["alternatives"][0].get("confidence", 0)
                    
                    result["transcript"] = transcript
                    result["confidence"] = confidence
                    result["full_response"] = response_json
                else:
                    # Check if the response contains an empty results array
                    if "results" in response_json and not response_json["results"]:
                        logger.warning("Google STT returned empty results - no speech detected")
                        result["success"] = False
                        result["error"] = "No speech detected" 
                        result["details"] = "The audio file didn't contain any recognizable speech"
                    else:
                        logger.warning(f"Google STT returned unexpected response structure: {response_json}")
                        result["success"] = False
                        result["error"] = "Unexpected API response"
                        
                    result["transcript"] = ""
                    result["confidence"] = 0
                    result["full_response"] = response_json
                    
                return result
            else:
                logger.error(f"Google STT API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API request failed with status {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Exception in Google STT service: {str(e)}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
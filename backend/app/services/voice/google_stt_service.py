import base64
import logging
import os
import requests
import traceback
import json
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleSTTService:
    """Service for Google Speech-to-Text API integration."""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.base_url = "https://speech.googleapis.com/v1/speech:recognize"
        logger.info(f"GoogleSTTService initialized. API key available: {bool(self.api_key)}")
        
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
            logger.error("Cannot transcribe: Google API key not configured")
            return {"success": False, "error": "Google API key not configured"}
        
        try:
            # Encode audio content to base64
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            
            # Construct API URL with key
            url = f"{self.base_url}?key={self.api_key}"
            
            # Detect if this is WebM audio (usually has a specific header)
            is_webm = False
            if len(audio_content) > 4:
                # Check for WebM header (which typically starts with bytes [0x1A, 0x45, 0xDF, 0xA3])
                if audio_content[0:4] == b'\x1a\x45\xdf\xa3':
                    is_webm = True
                    logger.info("Detected WebM file header")
                
            # Choose appropriate encoding based on whether the file appears to be WebM
            encoding = "WEBM_OPUS" if is_webm else "LINEAR16"
            
            # Prepare request payload with optimized settings
            config = {
                "encoding": encoding,
                "languageCode": language_code,
                "model": model,
                "enableAutomaticPunctuation": True,
                "maxAlternatives": 1,
                # Add some enhancement features
                "useEnhanced": True,
                "metadata": {
                    "interactionType": "DICTATION",
                    "microphoneDistance": "NEARFIELD",
                    "recordingDeviceType": "SMARTPHONE"
                }
            }
            
            # Only include sampleRateHertz if it's provided AND this is not a WebM file
            # WebM files should use auto-detection
            if sample_rate_hertz is not None and not is_webm:
                config["sampleRateHertz"] = sample_rate_hertz
                
            payload = {
                "config": config,
                "audio": {
                    "content": audio_base64
                }
            }
            
            logger.info(f"Sending audio to Google STT: {len(audio_content)} bytes, format={encoding}")
            logger.info(f"STT configuration: {json.dumps(config, indent=2)}")
            
            try:
                # Make API request
                response = requests.post(url, json=payload)
                
                # Log the full response for debugging
                logger.debug(f"Google STT response code: {response.status_code}")
                logger.debug(f"Google STT response headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    logger.debug(f"Google STT response JSON: {json.dumps(response_json, indent=2)}")
                except:
                    logger.warning(f"Google STT response is not JSON: {response.text[:1000]}")
                
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
                        logger.info(f"Speech recognition successful: '{transcript}' (confidence: {confidence})")
                    else:
                        # Check for the "no speech detected" case
                        # This happens when Google receives valid audio but doesn't detect speech
                        if "results" in response_json and not response_json["results"]:
                            logger.warning("Google STT returned empty results - no speech detected")
                            result["success"] = False
                            result["error"] = "No speech detected" 
                            result["details"] = "The audio file didn't contain any recognizable speech"
                        # Check for the special case with just totalBilledTime and requestId
                        elif "totalBilledTime" in response_json and "requestId" in response_json:
                            logger.warning(f"No speech detected response: {json.dumps(response_json, indent=2)}")
                            result["success"] = False
                            result["error"] = "No speech detected"
                            result["details"] = "The audio was processed but no speech was recognized"
                        else:
                            # Some other unexpected response structure
                            logger.warning(f"Google STT returned unexpected response structure: {json.dumps(response_json, indent=2)}")
                            stack_trace = traceback.format_stack()
                            logger.warning(f"Stack trace:\n{''.join(stack_trace)}")
                            
                            result["success"] = False
                            result["error"] = "Unexpected API response"
                            result["details"] = f"Response structure: {json.dumps(response_json, indent=2)}"
                        
                        result["transcript"] = ""
                        result["confidence"] = 0
                        result["full_response"] = response_json
                        
                    return result
                else:
                    logger.error(f"Google STT API error: {response.status_code} - {response.text}")
                    stack_trace = traceback.format_stack()
                    logger.error(f"Stack trace:\n{''.join(stack_trace)}")
                    
                    return {
                        "success": False,
                        "error": f"API request failed with status {response.status_code}",
                        "details": response.text
                    }
                    
            except Exception as e:
                logger.error(f"Exception in Google STT API request: {str(e)}")
                stack_trace = traceback.format_exc()
                logger.error(f"Stack trace:\n{stack_trace}")
                
                return {
                    "success": False,
                    "error": f"Exception in API request: {str(e)}",
                    "details": traceback.format_exc()
                }
                
        except Exception as e:
            logger.error(f"Exception in Google STT service: {str(e)}")
            stack_trace = traceback.format_exc()
            logger.error(f"Stack trace:\n{stack_trace}")
            
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "details": traceback.format_exc()
            }

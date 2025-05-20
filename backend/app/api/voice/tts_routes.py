from fastapi import APIRouter, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse, Response
import logging
import traceback
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.services.voice.google_tts_service import GoogleTTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize TTS service
tts_service = GoogleTTSService()

class TTSRequest(BaseModel):
    """Model for TTS request body."""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: Optional[str] = Field(None, description="Voice ID to use")
    language_code: Optional[str] = Field("en-US", description="Language code")
    speaking_rate: Optional[float] = Field(1.0, description="Speaking rate/speed, 0.25 to 4.0", ge=0.25, le=4.0)
    pitch: Optional[float] = Field(0.0, description="Voice pitch, -20.0 to 20.0", ge=-20.0, le=20.0)
    volume_gain_db: Optional[float] = Field(0.0, description="Volume gain in dB, -96.0 to 16.0", ge=-96.0, le=16.0)
    audio_encoding: Optional[str] = Field("MP3", description="Output audio encoding (MP3, LINEAR16, OGG_OPUS)")
    return_base64: Optional[bool] = Field(False, description="Return audio as base64 string instead of binary")
    preprocess_text: Optional[bool] = Field(True, description="Preprocess text for better TTS quality")

@router.post("/text-to-speech")
async def text_to_speech(
    request: Request,
    tts_request: TTSRequest
):
    """
    Convert text to speech using Google's Text-to-Speech API.
    
    Returns either binary audio data or a JSON with base64 encoded audio.
    """
    client_ip = request.client.host
    logger.info(f"Text-to-speech request from IP: {client_ip}")
    
    try:
        text = tts_request.text
        
        # Optional text preprocessing
        if tts_request.preprocess_text:
            text = tts_service.preprocess_text(text)
            logger.info(f"Preprocessed text (length: {len(text)})")
        
        # Synthesize speech
        result = tts_service.synthesize_speech(
            text=text,
            voice_id=tts_request.voice_id,
            language_code=tts_request.language_code,
            speaking_rate=tts_request.speaking_rate,
            pitch=tts_request.pitch,
            volume_gain_db=tts_request.volume_gain_db,
            audio_encoding=tts_request.audio_encoding
        )
        
        if not result.get("success", False):
            error_message = result.get("error", "Unknown error")
            details = result.get("details", "")
            
            logger.error(f"TTS error: {error_message}")
            if details:
                logger.error(f"TTS error details: {details}")
                
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": error_message,
                    "details": details
                }
            )
        
        # If requested, return JSON with base64 encoded audio
        if tts_request.return_base64:
            import base64
            audio_base64 = base64.b64encode(result["audio"]).decode("utf-8")
            
            return JSONResponse(
                content={
                    "success": True,
                    "audio_base64": audio_base64,
                    "mime_type": tts_service.get_audio_mime_type(result["encoding"]),
                    "encoding": result["encoding"],
                    "voice_id": result["voice_id"]
                }
            )
        
        # Otherwise, return binary audio data
        mime_type = tts_service.get_audio_mime_type(result["encoding"])
        return Response(
            content=result["audio"],
            media_type=mime_type
        )
            
    except Exception as e:
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        logger.error(f"Error in text-to-speech processing: {str(e)}")
        logger.error(f"Stack trace:\n{stack_trace}")
        
        # Return a more detailed error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error processing text-to-speech: {str(e)}",
                "details": stack_trace
            }
        )

@router.get("/text-to-speech/voices")
async def tts_voices():
    """
    Get available TTS voices.
    
    Returns a list of available voices.
    """
    try:
        voices = tts_service.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting TTS voices: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting voices: {str(e)}"}
        )

@router.get("/text-to-speech/status")
async def tts_status():
    """
    Check if the Text-to-Speech service is configured and available.
    
    Returns:
        Status of the TTS service
    """
    if not tts_service.api_key:
        return {"available": False, "reason": "API key not configured"}
    
    # Add additional diagnostics
    return {
        "available": True,
        "api_key_masked": f"{tts_service.api_key[:4]}...{tts_service.api_key[-4:]}" if tts_service.api_key else None,
        "service_url": tts_service.base_url,
        "voices_available": len(tts_service.voices)
    }

@router.post("/text-to-speech/test")
async def test_tts():
    """
    Test the Text-to-Speech service with a simple text.
    
    Returns the test audio in base64 format.
    """
    try:
        test_text = "Hello! This is a test of the Google Text-to-Speech API. Is my voice clear?"
        
        result = tts_service.synthesize_speech(
            text=test_text,
            voice_id=tts_service.default_voice
        )
        
        if not result.get("success", False):
            return {
                "test_successful": False,
                "error": result.get("error", "Unknown error"),
                "details": result.get("details", "")
            }
        
        # Convert audio to base64 for the response
        import base64
        audio_base64 = base64.b64encode(result["audio"]).decode("utf-8")
        
        return {
            "test_successful": True,
            "audio_base64": audio_base64,
            "mime_type": tts_service.get_audio_mime_type(result["encoding"]),
            "encoding": result["encoding"],
            "voice_id": result["voice_id"],
            "text": test_text
        }
        
    except Exception as e:
        logger.error(f"TTS test failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "test_successful": False,
            "error": str(e),
            "stack_trace": traceback.format_exc()
        }

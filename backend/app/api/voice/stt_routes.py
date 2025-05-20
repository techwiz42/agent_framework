from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.responses import JSONResponse
import logging
import traceback
import json
from typing import Optional
import io

from app.services.voice.google_stt_service import GoogleSTTService
from app.core.input_sanitizer import sanitize_text

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize STT service
stt_service = GoogleSTTService()

@router.post("/speech-to-text")
async def speech_to_text(
    request: Request,
    audio_file: UploadFile = File(...),
    language_code: Optional[str] = Form("en-US"),
    sample_rate: Optional[int] = Form(16000)
):
    """
    Convert speech audio to text using Google's Speech-to-Text API.
    
    Args:
        audio_file: Audio file in WAV, FLAC, or other supported format
        language_code: Language code (default: en-US)
        sample_rate: Audio sample rate in Hz (default: 16000)
        
    Returns:
        Transcription result
    """
    client_ip = request.client.host
    logger.info(f"Speech-to-text request from IP: {client_ip}")
    logger.info(f"Audio file: {audio_file.filename}, content_type: {audio_file.content_type}, size: Unknown")
    
    try:
        # Read file content
        audio_content = await audio_file.read()
        
        logger.info(f"Audio content size: {len(audio_content)} bytes")
        
        if not audio_content:
            logger.error("Empty audio file received")
            raise HTTPException(status_code=400, detail="Empty audio file")
            
        # Check file size (limit to 10 MB)
        if len(audio_content) > 10 * 1024 * 1024:
            logger.error(f"Audio file too large: {len(audio_content)} bytes")
            raise HTTPException(status_code=400, detail="Audio file too large. Maximum size is 10MB")
            
        # Check file extension/type to detect if it's a WEBM file
        file_extension = audio_file.filename.lower().split('.')[-1] if audio_file.filename else ""
        content_type = audio_file.content_type.lower() if audio_file.content_type else ""
        
        logger.info(f"File extension: {file_extension}, Content-Type: {content_type}")
       
        '''
        # Debug: Save a copy of the audio file for debugging
        try:
            debug_filename = f"debug_audio_{client_ip.replace('.', '_')}_{len(audio_content)}.{file_extension or 'bin'}"
            with open(debug_filename, "wb") as f:
                f.write(audio_content)
            logger.info(f"Debug: Saved audio file to {debug_filename}")
        except Exception as e:
            logger.warning(f"Could not save debug audio file: {e}")
        '''

        # For WEBM files, don't specify sample_rate to let Google auto-detect it
        use_auto_detect = "webm" in file_extension or "webm" in content_type
        
        if use_auto_detect:
            logger.info("WebM audio detected, using auto-detection for sample rate")
            
            # For debugging, log the first few bytes of the file
            if len(audio_content) > 20:
                header_bytes = " ".join([f"{b:02x}" for b in audio_content[:20]])
                logger.info(f"WebM file header bytes: {header_bytes}")
            
            result = stt_service.transcribe_audio(
                audio_content=audio_content,
                sample_rate_hertz=None,  # Let Google auto-detect for WEBM files
                language_code=language_code
            )
        else:
            # For other formats, use the provided sample rate
            logger.info(f"Non-WebM audio detected, using specified sample rate: {sample_rate}")
            result = stt_service.transcribe_audio(
                audio_content=audio_content,
                sample_rate_hertz=sample_rate,
                language_code=language_code
            )
        
        logger.info(f"STT service result: {json.dumps(result, indent=2)}")
        
        if not result.get("success", False) and "error" in result:
            # Check for sample rate mismatch error
            error_message = result.get("details", "")
            status_code = 500
            
            if isinstance(error_message, str) and "sample_rate_hertz" in error_message and "match the value in the" in error_message:
                status_code = 400
                result["error"] = "Audio sample rate mismatch. Please try again without specifying sample rate."
                
            logger.error(f"STT error (code {status_code}): {result['error']}")
            logger.error(f"STT error details: {error_message}")
                
            return JSONResponse(
                status_code=status_code,
                content={"error": result["error"], "details": error_message}
            )
            
        # Sanitize the transcribed text
        if "transcript" in result:
            original = result["transcript"]
            result["transcript"] = sanitize_text(result["transcript"])
            logger.info(f"Transcript (sanitized): '{result['transcript']}'")
            if original != result["transcript"]:
                logger.info(f"Original text was sanitized from: '{original}'")
            
        return result
        
    except Exception as e:
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        logger.error(f"Error in speech-to-text processing: {str(e)}")
        logger.error(f"Stack trace:\n{stack_trace}")
        
        # Return a more detailed error response
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error processing audio: {str(e)}",
                "details": stack_trace
            }
        )

@router.get("/speech-to-text/status")
async def stt_status():
    """
    Check if the Speech-to-Text service is configured and available.
    
    Returns:
        Status of the STT service
    """
    if not stt_service.api_key:
        return {"available": False, "reason": "API key not configured"}
    
    # Add additional diagnostics
    return {
        "available": True,
        "api_key_masked": f"{stt_service.api_key[:4]}...{stt_service.api_key[-4:]}" if stt_service.api_key else None,
        "service_url": stt_service.base_url
    }

@router.post("/speech-to-text/test")
async def test_stt():
    """
    Test the Speech-to-Text service with a simple audio file.
    
    Returns:
        Test result
    """
    try:
        # Create a simple test audio file with a beep tone
        # This is a minimal WAV file containing a sine wave
        logger.info("Creating test audio file")
        
        from scipy.io import wavfile
        import numpy as np
        import tempfile
        
        # Create a simple sine wave
        sample_rate = 16000
        duration = 1  # seconds
        frequency = 440  # Hz (A4 note)
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
            wavfile.write(temp_filename, sample_rate, audio_data)
        
        logger.info(f"Test audio file created at {temp_filename}")
        
        # Read the file
        with open(temp_filename, 'rb') as f:
            audio_content = f.read()
        
        # Send to STT service
        result = stt_service.transcribe_audio(
            audio_content=audio_content,
            sample_rate_hertz=sample_rate,
            language_code="en-US"
        )
        
        logger.info(f"STT test result: {json.dumps(result, indent=2)}")
        
        # Clean up
        import os
        os.unlink(temp_filename)
        
        return {
            "test_successful": True,
            "result": result,
            "audio_details": {
                "format": "WAV",
                "sample_rate": sample_rate,
                "duration": duration,
                "frequency": frequency,
                "file_size": len(audio_content)
            }
        }
        
    except Exception as e:
        logger.error(f"STT test failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "test_successful": False,
            "error": str(e),
            "stack_trace": traceback.format_exc()
        }

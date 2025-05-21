# app/api/voice/stt_routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import JSONResponse
import logging
import traceback
from typing import Optional

from app.services.voice.google_stt_service import stt_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/speech-to-text")
async def speech_to_text(
    request: Request,
    audio_file: UploadFile = File(...),
    language_code: str = Form("en-US"),
    sample_rate: Optional[str] = Form(None),
    content_type: Optional[str] = Form(None),
    is_webm: Optional[str] = Form(None),
    model: Optional[str] = Form("default")
):
    """
    Convert speech to text using Google's Speech-to-Text API.
    
    Args:
        request: The HTTP request
        audio_file: The audio file to transcribe
        language_code: The language code to use for transcription
        sample_rate: Sample rate in Hz (optional)
        content_type: Content type of the audio (for debugging)
        is_webm: Flag indicating if the audio is webm format (for debugging)
    
    Returns:
        JSON response with transcription result
    """
    client_ip = request.client.host
    logger.info(f"STT request from IP: {client_ip}")
    
    try:
        # Log debugging info
        logger.info(f"Audio file: {audio_file.filename}, size: {audio_file.size}, content_type: {audio_file.content_type}")
        logger.info(f"Form params - language_code: {language_code}, sample_rate: {sample_rate}")
        logger.info(f"Additional info - content_type: {content_type}, is_webm: {is_webm}")
        
        # Read the audio file content
        audio_content = await audio_file.read()
        
        # Convert sample_rate to int if provided
        sample_rate_hz = None
        if sample_rate:
            try:
                # FIXED: Properly parse sample_rate as int
                sample_rate_hz = int(sample_rate)
                logger.info(f"Using provided sample rate: {sample_rate_hz} Hz")
            except (ValueError, TypeError):
                logger.warning(f"Invalid sample_rate value: {sample_rate}, defaulting to None for WebM")
                sample_rate_hz = None
        
        # Get content type, if not provided in form use the file's content_type
        audio_content_type = content_type or audio_file.content_type
        logger.info(f"Using content type: {audio_content_type}")
        is_webm = is_webm == 'true' or (audio_content_type and 'webm' in audio_content_type.lower())
        
        # FIXED: Don't set sample rate for WebM - let the backend extract it from the header
        if is_webm:
            logger.info("WebM audio detected, sample rate will be extracted from header")
            sample_rate_hz = None  # Let the Google API extract it from the WebM header
        elif not sample_rate_hz:
            # If not WebM and no sample rate provided, use 16000 Hz as default
            logger.info("Non-WebM audio with no sample rate, defaulting to 16000 Hz")
            sample_rate_hz = 16000
        
        # Validate sample rate only if it's provided (not for WebM files)
        if sample_rate_hz is not None:
            # Validate sample rate - Google STT requires specific values
            # https://cloud.google.com/speech-to-text/docs/reference/rest/v1/RecognitionConfig
            valid_sample_rates = [8000, 12000, 16000, 22050, 24000, 32000, 44100, 48000]
            if sample_rate_hz not in valid_sample_rates:
                logger.warning(f"Sample rate {sample_rate_hz} not in Google STT supported rates: {valid_sample_rates}")
                # Use closest valid rate
                sample_rate_hz = min(valid_sample_rates, key=lambda x: abs(x - sample_rate_hz))
                logger.info(f"Using closest valid sample rate: {sample_rate_hz} Hz")
        else:
            logger.info("No sample rate provided - will be extracted from audio header")
        
        # IMPORTANT: For WebM/Opus files, always force 48000 Hz as that's the standard for WebM/Opus
        encoding = None
        if audio_content_type:
            if "webm" in audio_content_type.lower():
                encoding = "WEBM_OPUS"
                # For WebM with OPUS, always use 48000 Hz (the standard)
                logger.info("WebM OPUS detected, forcing 48000 Hz as the sample rate")
                sample_rate_hz = 48000
            elif "wav" in audio_content_type.lower() or "x-wav" in audio_content_type.lower():
                encoding = "LINEAR16"
            elif "ogg" in audio_content_type.lower():
                encoding = "OGG_OPUS"
                # For OGG with OPUS, always use 48000 Hz (the standard)
                logger.info("OGG OPUS detected, forcing 48000 Hz as the sample rate")
                sample_rate_hz = 48000
            elif "mp3" in audio_content_type.lower():
                encoding = "MP3"
            elif "flac" in audio_content_type.lower():
                encoding = "FLAC"
            elif "mulaw" in audio_content_type.lower():
                encoding = "MULAW"
        
        # If encoding still not determined, use the file extension
        if not encoding and audio_file.filename:
            ext = audio_file.filename.split('.')[-1].lower()
            if ext == "webm":
                encoding = "WEBM_OPUS"
            elif ext == "wav":
                encoding = "LINEAR16"
            elif ext == "ogg":
                encoding = "OGG_OPUS"
            elif ext == "mp3":
                encoding = "MP3"
            elif ext == "flac":
                encoding = "FLAC"
        
        # If still no encoding determined, use LINEAR16 as fallback
        if not encoding:
            logger.warning(f"Could not determine encoding from content type: {audio_content_type}, defaulting to LINEAR16")
            encoding = "LINEAR16"
        
        logger.info(f"Using audio encoding: {encoding}, sample rate: {sample_rate_hz} Hz")
        
        # Add stack trace before processing
        stack_trace = traceback.format_stack()
        logger.info(f"Pre-processing stack trace:\n{''.join(stack_trace)}")
        
        # Process the audio
        result = stt_service.transcribe_audio(
            audio_content=audio_content,
            language_code=language_code,
            sample_rate_hertz=sample_rate_hz,  # FIXED: Pass proper sample rate
            encoding=encoding,
            model=model,
            enhanced=True  # Use enhanced model for better accuracy
        )
        
        # Check for success
        if result.get("success", False):
            logger.info(f"STT success: {result.get('transcript', '')[:30]}...")
            return {
                "success": True,
                "transcript": result.get("transcript", ""),
                "confidence": result.get("confidence", 0)
            }
        else:
            error_msg = result.get("error", "Unknown error")
            details = result.get("details", "")
            
            # Special case: "No speech detected" should not be a 500 error
            # Instead, return a successful response with an empty transcript
            if error_msg == "No speech detected":
                logger.info("No speech detected, returning empty transcript with success=true")
                # Process any audio chunks that were sent before this one
                if 'audio_content' in locals() and len(audio_content) > 0:
                    first_few_bytes = ', '.join([f'{b:02x}' for b in audio_content[:20]])
                    logger.info(f"Audio that triggered 'No speech detected': size={len(audio_content)} bytes, first bytes: {first_few_bytes}")
                return {
                    "success": True,
                    "transcript": "",
                    "confidence": 0,
                    "message": "No speech detected"
                }
            
            logger.error(f"STT error (code 500): {error_msg}")
            if details:
                logger.error(f"STT error details: {details}")
                
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": error_msg,
                    "details": details
                }
            )
            
    except Exception as e:
        logger.error(f"Error in speech-to-text processing: {str(e)}")
        traceback.print_exc()
        logger.error(traceback.format_exc())
        
        # Log audio details for debugging
        audio_size = len(audio_content) if 'audio_content' in locals() else 0
        logger.error(f"Audio that caused the error - size: {audio_size} bytes")
        
        if audio_content and len(audio_content) > 0:
            first_few_bytes = ', '.join([f'{b:02x}' for b in audio_content[:20]])
            logger.error(f"First few bytes of problematic audio: {first_few_bytes}")
            
        # For security, don't return full traceback to client
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error processing speech-to-text: {str(e)}",
                "details": "Server encountered an error processing the audio. Please check logs."
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
        "service_url": stt_service.base_url,
        "supported_languages": len(stt_service.supported_languages),
        "supported_encodings": stt_service.supported_encodings,
        "supported_sample_rates": [8000, 12000, 16000, 22050, 24000, 32000, 44100, 48000]
    }

@router.get("/speech-to-text/languages")
async def stt_languages():
    """
    Get available STT languages.
    
    Returns:
        List of available languages and their codes
    """
    return {"languages": stt_service.supported_languages}

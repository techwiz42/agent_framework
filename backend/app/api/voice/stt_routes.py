from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.responses import JSONResponse
import logging
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
    
    try:
        # Read file content
        audio_content = await audio_file.read()
        
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file")
            
        # Check file size (limit to 10 MB)
        if len(audio_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large. Maximum size is 10MB")
            
        # Check file extension/type to detect if it's a WEBM file
        file_extension = audio_file.filename.lower().split('.')[-1] if audio_file.filename else ""
        content_type = audio_file.content_type.lower() if audio_file.content_type else ""
        
        # For WEBM files, don't specify sample_rate to let Google auto-detect it
        if "webm" in file_extension or "webm" in content_type:
            result = stt_service.transcribe_audio(
                audio_content=audio_content,
                sample_rate_hertz=None,  # Let Google auto-detect for WEBM files
                language_code=language_code
            )
        else:
            # For other formats, use the provided sample rate
            result = stt_service.transcribe_audio(
                audio_content=audio_content,
                sample_rate_hertz=sample_rate,
                language_code=language_code
            )
        
        if not result.get("success", False) and "error" in result:
            # Check for sample rate mismatch error
            error_message = result.get("details", "")
            status_code = 500
            
            if "sample_rate_hertz" in error_message and "match the value in the" in error_message:
                status_code = 400
                result["error"] = "Audio sample rate mismatch. Please try again without specifying sample rate."
                
            return JSONResponse(
                status_code=status_code,
                content={"error": result["error"], "details": error_message}
            )
            
        # Sanitize the transcribed text
        if "transcript" in result:
            result["transcript"] = sanitize_text(result["transcript"])
            
        return result
        
    except Exception as e:
        logger.error(f"Error in speech-to-text processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
        
@router.get("/speech-to-text/status")
async def stt_status():
    """
    Check if the Speech-to-Text service is configured and available.
    
    Returns:
        Status of the STT service
    """
    if not stt_service.api_key:
        return {"available": False, "reason": "API key not configured"}
    
    return {"available": True}
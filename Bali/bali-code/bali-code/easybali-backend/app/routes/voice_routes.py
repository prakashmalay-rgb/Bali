from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import datetime

from app.services.voice_transcription import transcribe_voice_note
from app.db.session import db

router = APIRouter(prefix="/voice", tags=["Voice Transcription"])
logger = logging.getLogger(__name__)

@router.post("/transcribe")
async def transcribe_audio_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = None
):
    """
    Transcribe uploaded audio file using OpenAI Whisper
    
    Args:
        file: Audio file (MP3, WAV, M4A, OGG)
        user_id: Optional user ID for logging
        
    Returns:
        Transcribed text
    """
    try:
        # Validate file type
        allowed_types = [
            "audio/mpeg", "audio/mp3", "audio/wav", "audio/wave",
            "audio/x-wav", "audio/m4a", "audio/mp4", "audio/ogg"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: MP3, WAV, M4A, OGG"
            )
        
        # Check file size (max 25MB for Whisper API)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 25MB"
            )
        
        # Transcribe audio
        transcript = await transcribe_voice_note(content, file.filename)
        
        if transcript is None:
            raise HTTPException(
                status_code=500,
                detail="Transcription failed. Please try again."
            )
        
        # Log transcription for compliance
        background_tasks.add_task(
            log_voice_transcription,
            user_id=user_id,
            filename=file.filename,
            file_size=file_size,
            transcript_length=len(transcript)
        )
        
        return {
            "success": True,
            "transcript": transcript,
            "filename": file.filename,
            "duration": None  # Could be added if needed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice transcription error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during transcription"
        )

@router.post("/transcribe-whatsapp")
async def transcribe_whatsapp_voice(
    background_tasks: BackgroundTasks,
    media_url: str,
    user_id: Optional[str] = None
):
    """
    Transcribe WhatsApp voice note from media URL
    
    Args:
        media_url: WhatsApp media URL
        user_id: Optional user ID for logging
        
    Returns:
        Transcribed text
    """
    try:
        from app.services.voice_transcription import transcribe_whatsapp_voice_note
        
        transcript = await transcribe_whatsapp_voice_note(media_url)
        
        if transcript is None:
            raise HTTPException(
                status_code=500,
                detail="WhatsApp voice transcription failed"
            )
        
        # Log transcription for compliance
        background_tasks.add_task(
            log_voice_transcription,
            user_id=user_id,
            media_url=media_url,
            transcript_length=len(transcript)
        )
        
        return {
            "success": True,
            "transcript": transcript,
            "source": "whatsapp"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp voice transcription error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during WhatsApp transcription"
        )

async def log_voice_transcription(
    user_id: Optional[str],
    transcript_length: int,
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    media_url: Optional[str] = None
):
    """Log voice transcription for compliance and analytics"""
    try:
        log_entry = {
            "user_id": user_id,
            "action": "voice_transcription",
            "timestamp": datetime.datetime.utcnow(),
            "transcript_length": transcript_length,
            "filename": filename,
            "file_size": file_size,
            "media_url": media_url
        }
        
        # Store in compliance logs collection
        await db["compliance_logs"].insert_one(log_entry)
        logger.info(f"Voice transcription logged for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to log voice transcription: {str(e)}")

@router.get("/health")
async def voice_service_health():
    """Health check for voice transcription service"""
    try:
        # Check OpenAI API access
        from app.settings.config import settings
        if not settings.OPENAI_API_KEY:
            return {
                "status": "unhealthy",
                "error": "OpenAI API key not configured"
            }
        
        return {
            "status": "healthy",
            "service": "voice_transcription",
            "whisper_model": "whisper-1"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

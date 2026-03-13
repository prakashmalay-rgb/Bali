import logging
import uuid
import httpx
import boto3
from botocore.config import Config
from app.settings.config import settings
from app.db.session import db
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
passport_collection = db["passports"]
issue_collection = db.get_collection("issues")

_s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION,
    config=Config(signature_version='s3v4')
)

async def download_whatsapp_media(media_id: str):
    """Downloads media from WhatsApp given its Media ID."""
    # Use v22.0 to match the current app configuration set in .env
    url = f"https://graph.facebook.com/v22.0/{media_id}"
    headers = {"Authorization": f"Bearer {settings.access_token}"}
    
    logger.info(f"Downloading WhatsApp media info for ID: {media_id}")
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            logger.error(f"Failed to get media URL for {media_id}: {res.text}")
            res.raise_for_status()
            
        media_url = res.json().get("url")
        if not media_url:
            logger.error(f"No media URL found in response for {media_id}: {res.json()}")
            raise ValueError("Media URL not found")
            
        logger.info(f"Fetching actual media content from {media_url[:50]}...")
        media_res = await client.get(media_url, headers=headers)
        if media_res.status_code != 200:
            logger.error(f"Failed to download media content from {media_url[:50]}: {media_res.text}")
            media_res.raise_for_status()
        
        content_type = media_res.headers.get("content-type", "image/jpeg")
        logger.info(f"Successfully downloaded {len(media_res.content)} bytes of type {content_type}")
        return media_res.content, content_type

def upload_bytes_to_s3(file_bytes: bytes, content_type: str, folder: str = "passports") -> tuple:
    """Uploads file bytes directly to S3 without ACLs."""
    ext = ".jpg"
    if "image/png" in content_type: ext = ".png"
    elif "image/webp" in content_type: ext = ".webp"
    elif "application/pdf" in content_type: ext = ".pdf"
    elif "audio/" in content_type:
        ext = ".ogg"
        if "mpeg" in content_type: ext = ".mp3"
        elif "wav" in content_type: ext = ".wav"
        
    key = f"{folder}/{uuid.uuid4()}{ext}"
    
    _s3.put_object(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type
    )
    url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    return key, url

async def process_whatsapp_passport(sender_id: str, media_id: str, villa_code: str = "UNKNOWN", guest_name: str = None):
    """Downloads WA media, uploads to S3, and saves as a pending passport."""
    try:
        file_bytes, content_type = await download_whatsapp_media(media_id)
        s3_key, s3_url = upload_bytes_to_s3(file_bytes, content_type, folder="passports")
        
        final_guest_name = guest_name or f"WhatsApp Guest {sender_id[-4:]}"
        
        passport_data = {
            "user_id": sender_id,
            "villa_code": villa_code,
            "guest_name": final_guest_name,
            "passport_url": s3_url,
            "s3_key": s3_key,
            "status": "pending_verification",
            "uploaded_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=90),
            "source": "whatsapp"
        }
        await passport_collection.insert_one(passport_data)
        logger.info(f"Passport for {sender_id} saved from WhatsApp. URL: {s3_url}")
        return True, "Your passport has been submitted successfully and is pending verification. Welcome!"
    except Exception as e:
        logger.error(f"Failed to process WhatsApp passport {media_id}: {e}")
        return False, "Sorry, there was an issue processing your document. Please try again later."

async def process_whatsapp_issue(sender_id: str, media_id: str, villa_code: str, description: str, media_type: str = "image"):
    """Handles issue reporting with media attachments. Transcribes if voice note."""
    try:
        file_bytes, content_type = await download_whatsapp_media(media_id)
        
        # New: Transcription for Voice Notes
        transcript = None
        if media_type == "voice_note":
            try:
                from app.services.openai_client import client
                import io
                
                logger.info(f"Transcribing voice note for {sender_id}...")
                audio_file = io.BytesIO(file_bytes)
                audio_file.name = "voice_note.ogg"
                
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcript = f"🎙️ (Voice Note): {response.text}"
                description = transcript
                logger.info(f"Transcription complete: {transcript[:50]}...")
            except Exception as te:
                logger.error(f"Transcription failed for {sender_id}: {te}")

        s3_key, s3_url = upload_bytes_to_s3(file_bytes, content_type, folder="issues")
        
        issue_data = {
            "sender_id": sender_id,
            "villa_code": villa_code,
            "description": description,
            "media_url": s3_url,
            "s3_key": s3_key,
            "media_type": media_type,
            "status": "open",
            "source": "whatsapp",
            "timestamp": datetime.utcnow()
        }
        await issue_collection.insert_one(issue_data)
        logger.info(f"Issue for villa {villa_code} reported with {media_type}. Source: whatsapp. URL: {s3_url}")
        return True, s3_url, transcript
    except Exception as e:
        logger.error(f"Failed to process WhatsApp issue {media_id}: {e}")
        return False, None, None

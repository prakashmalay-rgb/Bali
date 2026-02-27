from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.db.session import db
from app.settings.config import settings
from datetime import datetime, timedelta
from uuid import uuid4
import boto3
import logging
import os

router = APIRouter(prefix="/passports", tags=["Secure Documents"])
logger = logging.getLogger(__name__)

passport_collection = db["passports"]

# Passport-specific S3 client (no ACL usage)
_s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def _upload_passport_to_s3(file: UploadFile) -> str:
    """Upload passport file to S3 WITHOUT ACL (bucket has ACLs disabled)."""
    ext = os.path.splitext(file.filename)[1].lower()
    key = f"passports/{uuid4()}{ext}"
    
    _s3.upload_fileobj(
        file.file,
        settings.AWS_BUCKET_NAME,
        key,
        ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
    )
    return key, f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

def get_presigned_url(s3_key: str, expiration=3600) -> str:
    """Generate a temporary pre-signed URL to securely display a passport file."""
    try:
        url = _s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned url for {s3_key}: {e}")
        return ""


@router.post("/upload")
async def upload_passport(
    user_id: str = Form(...),
    villa_code: str = Form(...),
    full_name: str = Form(...),
    file: UploadFile = File(...)
):
    """Uploads a guest passport to S3 and stores metadata in MongoDB."""
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Allowed: JPG, PNG, PDF, WEBP."
        )
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB.")
    
    await file.seek(0)
    try:
        file_key, file_url = await _upload_passport_to_s3(file)
        
        passport_data = {
            "user_id": user_id,
            "villa_code": villa_code,
            "guest_name": full_name,
            "passport_url": file_url,
            "s3_key": file_key,
            "status": "pending_verification",
            "uploaded_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=90)
        }
        
        await passport_collection.insert_one(passport_data)
        logger.info(f"Passport uploaded for {full_name} at {villa_code}: {file_url}")
        
        return {
            "status": "success",
            "message": "Passport uploaded successfully",
            "submission_id": str(user_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Passport upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.get("/list/{villa_code}")
async def list_villa_passports(villa_code: str):
    """Admin route to list passport submissions for a specific villa."""
    submissions = []
    async for entry in passport_collection.find({"villa_code": villa_code}, {"_id": 0}):
        if "uploaded_at" in entry and hasattr(entry["uploaded_at"], "strftime"):
            entry["uploaded_at"] = entry["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S")
        if "expires_at" in entry and hasattr(entry["expires_at"], "strftime"):
            entry["expires_at"] = entry["expires_at"].strftime("%Y-%m-%d %H:%M:%S")
        submissions.append(entry)
    return {"submissions": submissions}

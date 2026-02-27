from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.utils.bucket import upload_to_s3
from app.db.session import db
from datetime import datetime, timedelta
import logging
import os

router = APIRouter(prefix="/passports", tags=["Secure Documents"])
logger = logging.getLogger(__name__)

passport_collection = db["passports"]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload")
async def upload_passport(
    user_id: str = Form(...),
    villa_code: str = Form(...),
    full_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Uploads a guest passport to S3 and stores metadata in MongoDB.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # 1. Validate file extension
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Allowed: JPG, PNG, PDF, WEBP."
        )
    
    # 2. Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB.")
    
    # Reset file cursor for S3 upload
    await file.seek(0)
    
    try:
        # 3. Upload to S3 (uses the proven public upload function)
        file_url = await upload_to_s3(file)
        
        # 4. Store metadata in MongoDB
        passport_data = {
            "user_id": user_id,
            "villa_code": villa_code,
            "guest_name": full_name,
            "passport_url": file_url,
            "s3_key": file_url,  # Keep both for backward compat
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
        raise  # Re-raise HTTP exceptions directly
    except Exception as e:
        logger.error(f"Passport upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload processing error: {str(e)}")

@router.get("/list/{villa_code}")
async def list_villa_passports(villa_code: str):
    """Admin route to list passport submissions for a specific villa."""
    submissions = []
    async for entry in passport_collection.find({"villa_code": villa_code}, {"_id": 0}):
        # Convert datetime to string for JSON serialization
        if "uploaded_at" in entry and hasattr(entry["uploaded_at"], "strftime"):
            entry["uploaded_at"] = entry["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S")
        if "expires_at" in entry and hasattr(entry["expires_at"], "strftime"):
            entry["expires_at"] = entry["expires_at"].strftime("%Y-%m-%d %H:%M:%S")
        submissions.append(entry)
    return {"submissions": submissions}

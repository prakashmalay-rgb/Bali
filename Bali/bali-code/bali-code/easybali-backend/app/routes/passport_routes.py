from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.utils.bucket import upload_secure_file
from app.db.session import db
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/passports", tags=["Secure Documents"])
logger = logging.getLogger(__name__)

passport_collection = db["passports"]
compliance_logs = db["compliance_logs"]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload")
async def upload_passport(
    user_id: str = Form(...),
    villa_code: str = Form(...),
    full_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Securely uploads a guest passport.
    Validates file type/size and stores with encryption on S3.
    """
    import os
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # 1. Validation
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}. Use Images or PDF.")
    
    # Check file size (Read first chunk to see if it's already over or check spool)
    # Note: SpooledTemporaryFile might not represent total size easily without reading
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    
    # Seek back to start for S3 upload
    await file.seek(0)
    
    try:
        # 2. Secure Upload
        file_key = await upload_secure_file(file, folder=f"passports/{villa_code}")
        
        # 3. Store Metadata
        passport_data = {
            "user_id": user_id,
            "villa_code": villa_code,
            "guest_name": full_name,
            "s3_key": file_key,
            "status": "pending_verification",
            "uploaded_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=90) # GDPR/Compliance: Auto-purge indicator
        }
        
        await passport_collection.insert_one(passport_data)
        
        # 4. Compliance Log
        await compliance_logs.insert_one({
            "action": "UPLOAD",
            "actor": user_id,
            "resource": file_key,
            "villa_code": villa_code,
            "timestamp": datetime.utcnow(),
            "status": "SUCCESS"
        })
        
        return {
            "status": "success",
            "message": "Passport uploaded securely",
            "submission_id": str(user_id)
        }
        
    except Exception as e:
        logger.error(f"Passport upload logic failed: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@router.get("/list/{villa_code}")
async def list_villa_passports(villa_code: str):
    """Admin route to list submissions for a specific villa."""
    # TODO: Add Admin Authentication Guard
    submissions = []
    async for entry in passport_collection.find({"villa_code": villa_code}, {"_id": 0}):
        submissions.append(entry)
    return {"submissions": submissions}

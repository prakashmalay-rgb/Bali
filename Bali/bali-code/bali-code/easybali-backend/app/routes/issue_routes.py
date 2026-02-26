from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from app.services import issue_service
from app.utils.bucket import upload_to_s3
from typing import Optional
import logging

router = APIRouter(prefix="/issues", tags=["Maintenance Tracker"])
logger = logging.getLogger(__name__)

@router.post("/submit")
async def submit_issue(
    user_id: str = Form(...),
    villa_code: str = Form(...),
    description: str = Form(...),
    priority: str = Form("medium"),
    image: Optional[UploadFile] = File(None)
):
    """
    Submit a maintenance issue from a guest.
    Optional image attachment is uploaded to public S3.
    """
    try:
        image_url = None
        if image:
            image_url = await upload_to_s3(image)
        
        issue = await issue_service.create_issue(
            user_id=user_id,
            villa_code=villa_code,
            issue_text=description,
            priority=priority,
            image_url=image_url
        )
        
        return {
            "status": "success",
            "message": "Maintenance request submitted successfully",
            "issue_id": issue["_id"]
        }
    except Exception as e:
        logger.error(f"Failed to submit issue: {e}")
        raise HTTPException(status_code=500, detail="Could not submit maintenance request")

@router.get("/list/{villa_code}")
async def list_issues(villa_code: str, status: Optional[str] = None):
    """Admin route to list issues for a villa."""
    try:
        issues = await issue_service.get_villa_issues(villa_code, status)
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{issue_id}/status")
async def update_issue_status(issue_id: str, status: str = Form(...), note: Optional[str] = Form(None)):
    """Admin route to update issue status (e.g., in-progress, resolved)."""
    from app.services.issue_service import issue_collection
    from bson import ObjectId
    from datetime import datetime
    
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        history_entry = {
            "status": status,
            "timestamp": datetime.utcnow(),
            "note": note or f"Status updated to {status}"
        }
        
        result = await issue_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {
                "$set": update_data,
                "$push": {"history": history_entry}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Issue not found")
            
        return {"status": "success", "message": f"Issue updated to {status}"}
    except Exception as e:
        logger.error(f"Failed to update issue: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

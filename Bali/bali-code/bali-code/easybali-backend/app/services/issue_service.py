from app.db.session import db
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
issue_collection = db["maintenance_issues"]

async def create_issue(
    user_id: str,
    villa_code: str,
    issue_text: str,
    priority: str = "medium",
    image_url: Optional[str] = None
) -> dict:
    """
    Creates a new maintenance issue and returns the saved document.
    """
    issue_data = {
        "user_id": user_id,
        "villa_code": villa_code,
        "description": issue_text,
        "priority": priority, # low, medium, high, urgent
        "status": "open", # open, in-progress, resolved, closed
        "image_url": image_url,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "history": [
            {
                "status": "open",
                "timestamp": datetime.utcnow(),
                "note": "Issue submitted by guest"
            }
        ]
    }
    
    result = await issue_collection.insert_one(issue_data)
    issue_data["_id"] = str(result.inserted_id)
    
    # 🔔 Trigger Notifications
    # await notify_villa_staff(villa_code, issue_data)
    
    return issue_data

async def get_villa_issues(villa_code: str, status: Optional[str] = None) -> List[dict]:
    query = {"villa_code": villa_code}
    if status:
        query["status"] = status
    
    issues = []
    async for issue in issue_collection.find(query).sort("created_at", -1):
        issue["_id"] = str(issue["_id"])
        issues.append(issue)
    return issues

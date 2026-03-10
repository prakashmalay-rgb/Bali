from app.db.session import db, issue_collection
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# issue_collection is db["issues"] from session.py — single source of truth
# Both WhatsApp and web submissions write to this collection.

async def create_issue(
    user_id: str,
    villa_code: str,
    issue_text: str,
    priority: str = "medium",
    image_url: Optional[str] = None,
    source: str = "web"
) -> dict:
    """
    Creates a new maintenance issue from a web submission and returns the saved document.
    Field names are normalized to match WhatsApp schema so the dashboard reads both uniformly.
    """
    issue_data = {
        "sender_id": user_id,        # normalized: was "user_id" — dashboard expects sender_id
        "villa_code": villa_code,
        "description": issue_text,
        "priority": priority,        # low, medium, high, urgent
        "status": "open",            # open, in_progress, resolved, closed
        "media_url": image_url,      # normalized: was "image_url" — dashboard expects media_url
        "media_type": "image" if image_url else "text",
        "source": source,
        "timestamp": datetime.utcnow(),  # normalized: was "created_at"
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

    return issue_data


async def get_villa_issues(villa_code: str, status: Optional[str] = None) -> List[dict]:
    query = {"villa_code": villa_code}
    if status:
        query["status"] = status

    issues = []
    async for issue in issue_collection.find(query).sort("timestamp", -1):
        issue["_id"] = str(issue["_id"])
        issues.append(issue)
    return issues

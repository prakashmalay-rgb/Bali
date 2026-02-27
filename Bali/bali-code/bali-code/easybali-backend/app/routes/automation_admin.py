from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.db.session import db
from app.utils.auth import requires_role

router = APIRouter(prefix="/automation-admin", tags=["Automation Admin"])
template_collection = db["message_templates"]

class TemplateUpdate(BaseModel):
    content: str
    is_active: bool

DEFAULT_TEMPLATES = {
    "welcome": "Hi {name}! Welcome to Bali. Our AI concierge is ready to help you with everything you need.",
    "pre_checkout": "Hi {name}, we hope you enjoyed your stay. Your check-out is tomorrow. Need a transfer to the airport?",
    "post_checkout": "Hi {name}, thank you for staying with us! Please rate your experience: https://bali.com/feedback"
}

@router.get("/list/{villa_code}", dependencies=[Depends(requires_role("staff"))])
async def list_templates(villa_code: str, user: dict = Depends(requires_role("staff"))):
    """
    Staff/Admin: List all automation templates for the specific villa.
    If none exist yet, it seeds the DB with defaults.
    """
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="You can only manage your own villa automations.")
        
    cursor = template_collection.find({"villa_code": villa_code})
    existing_templates = await cursor.to_list(length=10)
    
    # Check if we need to seed
    existing_types = {t["type"] for t in existing_templates}
    new_inserts = []
    
    for t_type, default_content in DEFAULT_TEMPLATES.items():
        if t_type not in existing_types:
            doc = {
                "villa_code": villa_code,
                "type": t_type,
                "content": default_content,
                "is_active": False, # Disabled by default
                "created_at": datetime.utcnow()
            }
            new_inserts.append(doc)
            
    if new_inserts:
        await template_collection.insert_many(new_inserts)
        # Re-fetch
        cursor = template_collection.find({"villa_code": villa_code})
        existing_templates = await cursor.to_list(length=10)
        
    results = []
    for t in existing_templates:
        t["id"] = str(t["_id"])
        t.pop("_id", None)
        results.append(t)
        
    return {"templates": results}

@router.put("/update/{villa_code}/{trigger_type}", dependencies=[Depends(requires_role("staff"))])
async def update_template(villa_code: str, trigger_type: str, data: TemplateUpdate, user: dict = Depends(requires_role("staff"))):
    """Staff/Admin: Update template content or toggle its active status."""
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="Forbidden")

    if trigger_type not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=400, detail="Invalid trigger type.")

    res = await template_collection.update_one(
        {"villa_code": villa_code, "type": trigger_type},
        {"$set": {
            "content": data.content,
            "is_active": data.is_active,
            "updated_at": datetime.utcnow()
        }}
    )

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found. Please list templates first to seed.")
        
    return {"message": f"Automation '{trigger_type}' updated successfully."}

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

# All 6 automation trigger templates — editable per villa
DEFAULT_TEMPLATES = {
    "passport_reminder": (
        "👋 *A Friendly Reminder*\n\n"
        "We noticed you haven't submitted your passport yet. It's required for local registration.\n\n"
        "Please upload a clear photo of your passport here on WhatsApp. 📄"
    ),
    "day_1_welcome": (
        "🌴 *Welcome to your first full day!*\n\n"
        "We hope you're settling in perfectly. If you need fresh towels, pool cleaning, or local tips, just let me know!\n\n"
        "Have a wonderful day in Bali. ✨"
    ),
    "mid_stay_concierge": (
        "☀️ *Time for an adventure?*\n\n"
        "You've been with us for a few days now! If you'd like to book a private tour, a spa treatment, or a driver for dinner, I'm here to help.\n\n"
        "Just type *Order Services* to explore our curated Bali experiences. 🥥"
    ),
    "pre_checkout_remind": (
        "👋 *Planning your departure?*\n\n"
        "We hope you've enjoyed your stay! Your checkout is coming up soon. 🕑\n\n"
        "Would you like us to arrange an *Airport Transfer* or a driver for your next stop?\n"
        "Type *Order Services* to book your ride now."
    ),
    "feedback_request": (
        "⭐ *We'd love your feedback!*\n\n"
        "Thank you for choosing Easy-Bali. On a scale of *1–5*, how was your experience at the villa and with our concierge service?\n\n"
        "Your feedback helps us provide a better experience for future guests! 🙏"
    ),
    "pre_arrival": (
        "🌺 *Your Bali stay begins soon!*\n\n"
        "Hi {name}, we are getting your villa ready for your arrival!\n\n"
        "Here's what to expect:\n"
        "• Scan the QR code at the villa entrance to check in\n"
        "• WiFi details and orientation guide will be shared on arrival\n"
        "• Your AI concierge activates the moment you check in\n\n"
        "What time do you expect to arrive? Reply with your ETA (e.g., *3 PM*). See you soon! 🥥"
    ),
}

ALLOWED_TRIGGER_TYPES = set(DEFAULT_TEMPLATES.keys())

TRIGGER_INFO = {
    "passport_reminder":  "Sent 1 hour after check-in if no passport has been submitted.",
    "day_1_welcome":      "Sent 24 hours after check-in.",
    "mid_stay_concierge": "Sent 72 hours (3 days) after check-in.",
    "pre_checkout_remind":"Sent 20 hours before estimated checkout date.",
    "feedback_request":   "Sent 4 hours after estimated checkout. Captures guest rating (1–5).",
    "pre_arrival":        "Sent 24–48 hours before a pre-registered guest arrival date. Prompts for ETA.",
}


@router.get("/list/{villa_code}", dependencies=[Depends(requires_role("staff"))])
async def list_templates(villa_code: str, user: dict = Depends(requires_role("staff"))):
    """List all automation templates for a villa. Seeds defaults on first call."""
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="You can only manage your own villa automations.")

    cursor = template_collection.find({"villa_code": villa_code})
    existing_templates = await cursor.to_list(length=20)

    # Seed missing templates
    existing_types = {t["type"] for t in existing_templates}
    new_inserts = []
    for t_type, default_content in DEFAULT_TEMPLATES.items():
        if t_type not in existing_types:
            new_inserts.append({
                "villa_code": villa_code,
                "type": t_type,
                "content": default_content,
                "trigger_info": TRIGGER_INFO.get(t_type, "Scheduled background event."),
                "is_active": False,
                "created_at": datetime.utcnow(),
            })

    if new_inserts:
        await template_collection.insert_many(new_inserts)
        cursor = template_collection.find({"villa_code": villa_code})
        existing_templates = await cursor.to_list(length=20)

    # Ensure trigger_info is populated on older records
    results = []
    for t in existing_templates:
        t["id"] = str(t["_id"])
        t.pop("_id", None)
        if "trigger_info" not in t:
            t["trigger_info"] = TRIGGER_INFO.get(t["type"], "Scheduled background event.")
        results.append(t)

    # Sort by a canonical order
    order = list(DEFAULT_TEMPLATES.keys())
    results.sort(key=lambda x: order.index(x["type"]) if x["type"] in order else 99)
    return {"templates": results}


@router.put("/update/{villa_code}/{trigger_type}", dependencies=[Depends(requires_role("staff"))])
async def update_template(
    villa_code: str,
    trigger_type: str,
    data: TemplateUpdate,
    user: dict = Depends(requires_role("staff"))
):
    """Update template content or toggle active status."""
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="Forbidden")

    if trigger_type not in ALLOWED_TRIGGER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger type. Allowed: {', '.join(sorted(ALLOWED_TRIGGER_TYPES))}"
        )

    if not data.content or not data.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    if len(data.content) > 2000:
        raise HTTPException(status_code=400, detail="Message content must be 2000 characters or fewer.")

    res = await template_collection.update_one(
        {"villa_code": villa_code, "type": trigger_type},
        {"$set": {
            "content": data.content.strip(),
            "is_active": data.is_active,
            "updated_at": datetime.utcnow(),
        }}
    )

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found. Please list templates first to seed defaults.")

    return {"message": f"Automation '{trigger_type}' updated successfully."}

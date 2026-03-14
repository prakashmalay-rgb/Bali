"""
Content Library — admin-managed messages/documents that can be
broadcast to guests via WhatsApp (email placeholder included).

Access control:
  - read_only / staff / admin : GET list + GET single
  - staff / admin             : POST create, PUT update, POST send
  - admin only                : DELETE
"""

from fastapi import APIRouter, Depends, Body
from app.db.session import db, villa_code_collection
from app.utils.auth import requires_role, get_current_user
from typing import Annotated, Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

router = APIRouter(
    prefix="/content",
    tags=["Content Library"],
    dependencies=[Depends(requires_role("read_only"))],
)

content_collection = db["content_library"]

ALLOWED_TYPES = {"announcement", "promotion", "notice", "travel_tip", "welcome_message", "house_rules", "privacy_notice"}


# ── helpers ───────────────────────────────────────────────────────────────────

def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for f in ("created_at", "updated_at"):
        if isinstance(doc.get(f), datetime):
            doc[f] = doc[f].isoformat()
    for entry in doc.get("send_history", []):
        if isinstance(entry.get("sent_at"), datetime):
            entry["sent_at"] = entry["sent_at"].isoformat()
    return doc


def _validate_body(title: str, body: str, content_type: str) -> Optional[str]:
    if not title or not title.strip():
        return "title is required"
    if len(title) > 200:
        return "title must be 200 characters or fewer"
    if not body or not body.strip():
        return "body is required"
    if len(body) > 4000:
        return "body must be 4000 characters or fewer"
    if content_type not in ALLOWED_TYPES:
        return f"type must be one of: {', '.join(sorted(ALLOWED_TYPES))}"
    return None


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@router.get("")
async def list_content(user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        items = await content_collection.find().sort("updated_at", -1).to_list(200)
        return {"success": True, "items": [_serialize(i) for i in items]}
    except Exception as e:
        return {"success": False, "error": str(e), "items": []}


@router.get("/{item_id}")
async def get_content(item_id: str, user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        doc = await content_collection.find_one({"_id": ObjectId(item_id)})
        if not doc:
            return {"success": False, "error": "Content item not found"}
        return {"success": True, "item": _serialize(doc)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("")
async def create_content(
    payload: Dict[str, Any] = Body(...),
    user: Annotated[dict, Depends(requires_role("staff"))] = None
) -> Dict[str, Any]:
    title = (payload.get("title") or "").strip()
    body = (payload.get("body") or "").strip()
    content_type = (payload.get("type") or "announcement").strip()
    tags: List[str] = [t.strip() for t in payload.get("tags", []) if isinstance(t, str)]

    err = _validate_body(title, body, content_type)
    if err:
        return {"success": False, "error": err}

    now = datetime.utcnow()
    doc = {
        "title": title,
        "body": body,
        "type": content_type,
        "tags": tags,
        "created_by": user.get("email", "admin"),
        "created_at": now,
        "updated_at": now,
        "send_history": [],
    }
    result = await content_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"success": True, "item": _serialize(doc)}


@router.put("/{item_id}")
async def update_content(
    item_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Annotated[dict, Depends(requires_role("staff"))] = None
) -> Dict[str, Any]:
    try:
        existing = await content_collection.find_one({"_id": ObjectId(item_id)})
        if not existing:
            return {"success": False, "error": "Content item not found"}

        title = (payload.get("title") or existing.get("title", "")).strip()
        body = (payload.get("body") or existing.get("body", "")).strip()
        content_type = (payload.get("type") or existing.get("type", "announcement")).strip()
        tags: List[str] = [t.strip() for t in payload.get("tags", existing.get("tags", [])) if isinstance(t, str)]

        err = _validate_body(title, body, content_type)
        if err:
            return {"success": False, "error": err}

        await content_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"title": title, "body": body, "type": content_type, "tags": tags, "updated_at": datetime.utcnow()}}
        )
        updated = await content_collection.find_one({"_id": ObjectId(item_id)})
        return {"success": True, "item": _serialize(updated)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/{item_id}")
async def delete_content(
    item_id: str,
    user: Annotated[dict, Depends(requires_role("admin"))] = None
) -> Dict[str, Any]:
    try:
        result = await content_collection.delete_one({"_id": ObjectId(item_id)})
        if result.deleted_count == 0:
            return {"success": False, "error": "Content item not found"}
        return {"success": True, "message": "Deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Send endpoint ─────────────────────────────────────────────────────────────

@router.post("/{item_id}/send")
async def send_content(
    item_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Annotated[dict, Depends(requires_role("staff"))] = None
) -> Dict[str, Any]:
    """
    Send a content item to guests.

    payload:
      channel:    "whatsapp" | "email" | "both"
      target:     "all" | "villa" | "custom"
      villa_code: "V1"  (required when target == "villa")
      recipients: ["628...","628..."]  (required when target == "custom")
    """
    from app.utils.whatsapp_func import send_whatsapp_message

    channel: str = payload.get("channel", "whatsapp")
    target: str = payload.get("target", "all")
    villa_code_filter: Optional[str] = payload.get("villa_code")
    custom_recipients: List[str] = payload.get("recipients", [])

    # ── Validate inputs ───────────────────────────────────────────────────
    if channel not in ("whatsapp", "email", "both"):
        return {"success": False, "error": "channel must be 'whatsapp', 'email', or 'both'"}
    if target not in ("all", "villa", "custom"):
        return {"success": False, "error": "target must be 'all', 'villa', or 'custom'"}
    if target == "villa" and not villa_code_filter:
        return {"success": False, "error": "villa_code is required when target is 'villa'"}
    if target == "custom":
        if not custom_recipients:
            return {"success": False, "error": "recipients list is required when target is 'custom'"}
        # Basic phone number sanity check
        for r in custom_recipients:
            if not str(r).strip().isdigit():
                return {"success": False, "error": f"Invalid recipient number: {r}"}

    # ── Fetch content item ────────────────────────────────────────────────
    try:
        doc = await content_collection.find_one({"_id": ObjectId(item_id)})
    except Exception:
        return {"success": False, "error": "Invalid item ID"}
    if not doc:
        return {"success": False, "error": "Content item not found"}

    message_body: str = doc["body"]

    # ── Resolve recipient list ────────────────────────────────────────────
    recipient_ids: List[str] = []
    if target == "custom":
        recipient_ids = [str(r).strip() for r in custom_recipients]
    else:
        query = {}
        if target == "villa" and villa_code_filter:
            query["villa_code"] = villa_code_filter
        vc_docs = await villa_code_collection.find(query, {"sender_id": 1}).to_list(1000)
        # Deduplicate, exclude empty
        seen = set()
        for v in vc_docs:
            sid = v.get("sender_id")
            if sid and str(sid) not in seen:
                seen.add(str(sid))
                recipient_ids.append(str(sid))

    if not recipient_ids:
        return {"success": False, "error": "No recipients found for the given target"}

    # ── Send via WhatsApp ─────────────────────────────────────────────────
    wa_sent = 0
    wa_failed = 0
    email_note = None

    if channel in ("whatsapp", "both"):
        for rid in recipient_ids:
            try:
                await send_whatsapp_message(rid, message_body)
                wa_sent += 1
            except Exception:
                wa_failed += 1

    if channel in ("email", "both"):
        # Email is not yet configured — log intent only
        email_note = "Email channel is not yet configured. WhatsApp was used instead."

    # ── Record in send history ────────────────────────────────────────────
    history_entry = {
        "sent_at": datetime.utcnow(),
        "sent_by": user.get("email", "admin"),
        "channel": channel,
        "target": target if target != "villa" else f"villa:{villa_code_filter}",
        "recipient_count": wa_sent,
        "failed_count": wa_failed,
    }
    await content_collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$push": {"send_history": history_entry}}
    )

    result = {
        "success": True,
        "sent": wa_sent,
        "failed": wa_failed,
        "total_recipients": len(recipient_ids),
    }
    if email_note:
        result["note"] = email_note
    return result
